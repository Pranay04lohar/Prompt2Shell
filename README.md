# Prompt2Shell

AI-powered shell command generator that transforms natural language prompts into executable shell commands using a fine-tuned Phi-3-mini model.

[Live Site](https://prompt2shell.vercel.app/)


---

## Demo Video:



## Features

- Natural language to shell command conversion
- Fine-tuned Phi-3-mini (QLoRA) model
- Modern terminal-style UI
- Fast inference via Modal (GPU-accelerated)
- Free deployment: Vercel (frontend) + Render (backend) + Modal (model serving)

## Tech Stack

**Frontend:**

- React + TypeScript + Vite
- Tailwind CSS

**Backend:**

- Python FastAPI
- Proxies requests to Modal endpoint

**Model Serving:**

- Modal (GPU instances)
- llama.cpp (GGUF format)
- Phi-3-mini-4k-instruct (fine-tuned with QLoRA)

## Project Structure

```
Prompt2Shell/
├── frontend/          # React/Vite frontend
├── backend/           # FastAPI backend
│   └── src/
│       ├── api.py     # FastAPI endpoints
│       └── agent_utils.py  # Model proxy logic
├── model_server.py   # Modal deployment script
└── merged-phi3-prompt2shell/  # Merged HF model (gitignored)
```

## Quick Setup

### Local Development

1. **Frontend:**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python run_server.py
   ```

### Deployment

1. **Model (Modal):**

   - Upload GGUF model to Modal volume
   - Deploy: `modal deploy model_server.py`
   - Set `MODEL_ENDPOINT_URL` on Render

2. **Backend (Render):**

   - Set env: `MODEL_ENDPOINT_URL`, `ALLOWED_ORIGINS`
   - Deploy web service

3. **Frontend (Vercel):**
   - Set env: `VITE_API_BASE_URL` (Render backend URL)
   - Deploy

## Fine-tuning concepts (short)

- PEFT (Parameter-Efficient Fine-Tuning):

  - Fine-tune large models by updating a small subset of parameters, not all weights.
  - Cuts VRAM and compute, enables training on modest GPUs.

- LoRA (Low-Rank Adaptation):

  - A PEFT method that learns low-rank updates (A·B) inserted into attention/MLP layers while keeping the base model frozen.
  - Produces small adapter files that can be merged into the base model later.

- QLoRA (Quantized LoRA):
  - Loads the base model in 4-bit during training while training LoRA adapters in higher precision.
  - Enables near full-quality fine-tuning on 4–8 GB GPUs.

Why we used them

- We needed a domain-specific behavior (“NL → shell command”) without full model retraining.
- LoRA/QLoRA let us fine-tune efficiently, ship tiny adapters, and later merge → convert to GGUF for fast inference with `llama.cpp` on Modal.

## License

MIT
