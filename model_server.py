import os
import modal
from pydantic import BaseModel

# ---------- Build image with CUDA + llama-cpp-python + fastapi ----------
image = (
    # FIX: Use the 'devel' image which includes the full CUDA toolkit (nvcc)
    modal.Image.from_registry("nvidia/cuda:12.2.2-devel-ubuntu22.04", add_python="3.10")
    .entrypoint([])
    .apt_install("git", "build-essential", "cmake")
    .env({
        "CMAKE_ARGS": "-DGGML_CUDA=on", 
        "IMAGE_BUILD_ID": "12.2.2-runtime", # This is just a label, can remain
        "CC": "gcc",
        "CXX": "g++",
        # FIX: Add the stub path AND explicitly link the cuda library
        "LDFLAGS": "-L/usr/local/cuda/lib64/stubs -lcuda" 
    })
    .pip_install(
        "llama-cpp-python[server]>=0.2.78",
        "uvicorn>=0.23.0",
        "pydantic",
        "fastapi",
    )
)

# ---------- Modal app ----------
app = modal.App("prompt2shell-api")

# Persisted volume created earlier: model-volume
volume = modal.Volume.from_name("model-volume")

MODEL_DIR = "/models"
MODEL_PATH = f"{MODEL_DIR}/phi3-mini.gguf"
SYSTEM_PROMPT = (
    "You convert a user's request into ONE concise shell command. "
    "Output ONLY the command, no explanations, no code fences, no prose."
)

# ---------- Inference class ----------
@app.cls(
    gpu="t4",
    image=image,
    volumes={MODEL_DIR: volume},  # mount volume at /models
    scaledown_window=180,        # replaces container_idle_timeout
    max_containers=10,           # Maximum number of containers (replaces concurrency_limit)
)
class ModelServer:
    def __enter__(self):
        """Container startup hook: try to load the model once.
        If anything fails here, we log and allow generate() to
        attempt a lazy load so we can surface clearer errors.
        """
        try:
            from llama_cpp import Llama

            if not os.path.exists(MODEL_PATH):
                raise FileNotFoundError(
                    f"Model file not found at {MODEL_PATH}. "
                    f"Mounted entries at {MODEL_DIR}: {os.listdir(MODEL_DIR)}"
                )

            # Load GGUF model (offload all layers to GPU)
            self.llm = Llama(
                model_path=MODEL_PATH,
                n_gpu_layers=-1,  # all layers to GPU
                n_ctx=4096,
                n_batch=512,
                verbose=True,
            )
            print("[ModelServer] Model loaded in __enter__")
        except Exception as e:
            # Do not re-raise; generate() will try a lazy load and report
            print(f"[ModelServer] __enter__ failed: {e}")
    
    @modal.method()
    def generate(self, prompt: str):
        if not prompt or not prompt.strip():
            return {"response": ""}

        # Lazy load guard: if __enter__ did not complete, load here
        if not hasattr(self, "llm"):
            try:
                from llama_cpp import Llama
                if not os.path.exists(MODEL_PATH):
                    raise FileNotFoundError(
                        f"Model file not found at {MODEL_PATH}. "
                        f"Mounted entries at {MODEL_DIR}: {os.listdir(MODEL_DIR)}"
                    )
                self.llm = Llama(
                    model_path=MODEL_PATH,
                    n_gpu_layers=-1,
                    n_ctx=4096,
                    n_batch=512,
                    verbose=True,
                )
                print("[ModelServer] Model lazy-loaded in generate()")
            except Exception as e:
                return {"error": f"Model load failed: {e}"}

        # Format prompt to steer the model to return only a command
        formatted = (
            f"<|system|>\n{SYSTEM_PROMPT}<|end|>\n"
            f"<|user|>\n{prompt}\nOutput only the command.<|end|>\n"
            f"<|assistant|>"
        )

        out = self.llm(
            formatted,
            max_tokens=128,
            stop=["<|end|>", "</s>", "<|user|>"],
            temperature=0.1,
            top_p=0.9,
            echo=False,
        )
        text = out.get("choices", [{}])[0].get("text", "").strip()

        # Post-process: take the first non-empty line, strip code fences/backticks
        line = next((l for l in text.splitlines() if l.strip()), "").strip()
        if line.startswith("```") and line.endswith("```"):
            line = line.strip("`")
        if line.startswith("bash "):
            line = line[5:].strip()
        return {"response": line}


# ---------- Public web endpoint ----------
class GenerateRequest(BaseModel):
    prompt: str


@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
def api_endpoint(request: GenerateRequest):
    """
    Public HTTPS endpoint.
    Expects JSON: { "prompt": "..." }
    Returns: { "response": "..." }
    """
    prompt = request.prompt
    
    if not prompt or not prompt.strip():
        return {"error": "No prompt provided"}
    
    server = ModelServer()
    return server.generate.remote(prompt)

