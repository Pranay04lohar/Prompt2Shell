"""
FastAPI server for Prompt2Shell backend API.
Provides REST endpoints for command generation.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Import agent utilities (assuming src directory is in path)
from agent_utils import initialize_model, generate_command

# Initialize FastAPI app
app = FastAPI(title="Prompt2Shell API", version="1.0.0")

# CORS middleware - allow frontend to connect
import os

# CORS configuration: supports exact list, wildcard, or regex via env
_origins_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,https://localhost:5173"
)
_origin_regex_env = os.getenv("ALLOWED_ORIGIN_REGEX", "")

cors_kwargs = {
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

if _origin_regex_env:
    cors_kwargs["allow_origin_regex"] = _origin_regex_env
    cors_kwargs["allow_credentials"] = True
else:
    allowed = [o.strip() for o in _origins_env.split(",") if o.strip()]
    if allowed == ["*"]:
        # Wildcard only works with allow_credentials=False
        cors_kwargs["allow_origins"] = ["*"]
        cors_kwargs["allow_credentials"] = False
    else:
        cors_kwargs["allow_origins"] = allowed
        cors_kwargs["allow_credentials"] = True

app.add_middleware(CORSMiddleware, **cors_kwargs)

# Request/Response models
class GenerateRequest(BaseModel):
    prompt: str


class Step(BaseModel):
    command: str
    explanation: str


class GenerateResponse(BaseModel):
    model: str
    steps: List[Step]


# Initialize model on startup
@app.on_event("startup")
async def startup_event():
    """Load model on startup unless proxying to external model."""
    if os.getenv("MODEL_ENDPOINT_URL"):
        print("MODEL_ENDPOINT_URL detected; skipping local model initialization.")
        return
    print("Initializing model on server startup...")
    try:
        initialize_model()
        print("Model initialized successfully!")
    except Exception as e:
        print(f"Error initializing model: {e}")
        print("Model will be loaded on first request...")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_commands(request: GenerateRequest):
    """
    Generate shell commands from a natural language prompt.
    
    Returns a response with model name and list of steps (commands with explanations).
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    try:
        # Generate command using agent utilities
        command, plan = generate_command(request.prompt.strip())
        
        # Create explanation from plan (first 200 chars or the plan itself)
        explanation = plan[:200] + "..." if len(plan) > 200 else plan
        if not explanation.strip():
            explanation = f"Generated command for: {request.prompt[:100]}"
        
        # Return response in format expected by frontend
        return GenerateResponse(
            model="Phi-3-mini (QLoRA Fine-Tuned)",
            steps=[
                Step(
                    command=command,
                    explanation=explanation
                )
            ]
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error generating command: {e}")
        print(f"Full traceback:\n{error_traceback}")
        
        # Provide more helpful error messages
        error_detail = str(e)
        if "numpy" in error_detail.lower() or "Unable to compare versions" in error_detail:
            error_detail = (
                "Model initialization failed due to NumPy version detection issue. "
                "NumPy is installed but transformers cannot detect it. "
                "This is likely due to corrupted package metadata. "
                "Error: " + str(e)
            )
        
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

