import os
import modal
from pydantic import BaseModel

# ---------- Build image with CUDA + llama-cpp-python + fastapi ----------
# Your image build definition is correct and can remain as-is
image = (
    modal.Image.from_registry("nvidia/cuda:12.2.2-devel-ubuntu22.04", add_python="3.10")
    .entrypoint([])
    .apt_install("git", "build-essential", "cmake")
    .env({
        "CMAKE_ARGS": "-DGGML_CUDA=on", 
        "IMAGE_BUILD_ID": "12.2.2-runtime",
        "CC": "gcc",
        "CXX": "g++",
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
# NOTE: Make sure this path is correct inside your volume!
# If your file is at 'models/phi3-mini.gguf' inside the volume,
# this path should be: f"{MODEL_DIR}/models/phi3-mini.gguf"
MODEL_PATH = f"{MODEL_DIR}/phi3-mini.gguf"
SYSTEM_PROMPT = (
    "You convert a user's request into ONE concise shell command. "
    "Output ONLY the command, no explanations, no code fences."
)

# Pydantic model for the request
class GenerateRequest(BaseModel):
    prompt: str

# ---------- Inference class ----------
@app.cls(
    gpu="t4",
    image=image,
    volumes={MODEL_DIR: volume},  # mount volume at /models
    scaledown_window=180,
    max_containers=10,
)
class ModelServer:

    # FIX 1: Use @modal.enter() lifecycle hook
    # This runs ONCE when the container starts, not on every request.
    @modal.enter()
    def load_model(self):
        # FIX: Move 'global' to the top of the function
        global MODEL_PATH
        from llama_cpp import Llama
        
        if not os.path.exists(MODEL_PATH):
            # Check if the nested path exists, common user error
            nested_path = f"{MODEL_DIR}/models/phi3-mini.gguf"
            if os.path.exists(nested_path):
                # 'global' declaration is already at the top
                MODEL_PATH = nested_path
                print(f"Warning: Found model at nested path: {MODEL_PATH}")
            else:
                raise FileNotFoundError(
                    f"Model file not found at {MODEL_PATH}. "
                    "Ensure your Volume contains phi3-mini.gguf."
                )
        
        print("--- Loading model into GPU VRAM ---")
        # Load GGUF model (offload all layers to GPU)
        self.llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=-1,  # all layers to GPU
            n_ctx=2048,
            n_batch=256,
            verbose=True,
        )
        print("--- Model loading complete ---")

    # FIX 2: Move the FastAPI endpoint INSIDE the class
    # This method uses the already-loaded self.llm
    @modal.fastapi_endpoint(method="POST")
    def generate_endpoint(self, request: GenerateRequest):
        """
        Public HTTPS endpoint.
        Expects JSON: { "prompt": "..." }
        Returns: { "response": "..." }
        """
        prompt = request.prompt
        if not prompt or not prompt.strip():
            return {"error": "No prompt provided"}
        
        # self.llm is already loaded!
        # Prefer the GGUF-provided chat template via llama.cpp's chat API
        out = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{prompt}. Output only the command."},
            ],
            temperature=0.1,
            top_p=0.9,
            max_tokens=64,
            stop=["<|end|>", "</s>", "<|user|>"]
        )
        text = (
            out.get("choices", [{}])[0]
               .get("message", {})
               .get("content", "")
            or out.get("choices", [{}])[0].get("text", "")
        ).strip()
        # take first non-empty line and strip code fences/backticks
        line = next((l for l in text.splitlines() if l.strip()), "").strip()
        if line.startswith("```") and line.endswith("```"):
            line = line.strip("`")
        if line.startswith("bash "):
            line = line[5:].strip()
        return {"response": line}


# FIX 3: Removed the separate @app.function() endpoint.
# The class method 'generate_endpoint' is now the public API.

