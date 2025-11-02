# Deployment Plan: Ollama

## Overview

Deploy the fine-tuned Phi-3-mini model with LoRA adapters on Ollama instead of Hugging Face Spaces.

## Why Ollama?

- ✅ **Free & Local/Cloud**: Can run locally or deploy to servers
- ✅ **Easy API**: Simple REST API (compatible with existing frontend)
- ✅ **GGUF Support**: Efficient model format (smaller, faster)
- ✅ **No GPU Required**: Can run on CPU (slower but free)
- ✅ **Easy Deployment**: Simple setup process

## Prerequisites

1. **Ollama Installed** (locally or on server):

   - Download from: https://ollama.ai
   - Or install on server: `curl -fsSL https://ollama.ai/install.sh | sh`

2. **Model Conversion Tools**:
   - `llama.cpp` for converting to GGUF format
   - Or use `transformers` + `ctranslate2` for conversion

## Deployment Steps

### Step 1: Convert Fine-Tuned Model to GGUF Format

**Current Setup:**

- Base Model: `microsoft/Phi-3-mini-4k-instruct`
- LoRA Adapter: `backend/lora_adapter/lora_adapter/`
- Format: Hugging Face Transformers (PyTorch)

**Conversion Process:**

1. Merge LoRA adapter with base model (create full fine-tuned model)
2. Convert merged model to GGUF format using `llama.cpp` or similar tool
3. Quantize model (4-bit or 8-bit) for smaller size and faster inference

**Tools Needed:**

- `transformers` - to merge LoRA with base model
- `llama.cpp` - to convert to GGUF format
- Or use online conversion tools

### Step 2: Create Ollama Modelfile

Create a `Modelfile` that:

- Points to the GGUF model file
- Sets system prompt for command generation
- Configures generation parameters (temperature, top_p, etc.)

**Example Modelfile:**

```
FROM ./phi3-mini-finetuned.gguf

TEMPLATE """<|system|>
You are a helpful assistant that generates shell commands from natural language instructions. Provide clear, executable commands.
<|user|>
{{ .Prompt }}
<|assistant|>
"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
```

### Step 3: Import Model into Ollama

```bash
# Create custom model in Ollama
ollama create prompt2shell -f Modelfile

# Or load the model directly
ollama load phi3-mini-finetuned
```

### Step 4: Serve via Ollama API

Ollama provides a REST API at `http://localhost:11434` (or configured port):

**Endpoints:**

- `POST /api/generate` - Generate text (for our use case)
- `POST /api/chat` - Chat completion
- `GET /api/tags` - List models

### Step 5: Update Backend/Frontend

**Option A: Use Ollama API Directly (Frontend)**

- Frontend calls Ollama API directly
- No backend needed (simplest approach)

**Option B: Proxy via FastAPI Backend**

- Keep FastAPI backend
- Backend calls Ollama API and formats response
- Maintains same frontend code

## File Structure Changes

**Files to Create:**

- `backend/convert_to_ollama.py` - Script to convert model to GGUF
- `backend/Modelfile` - Ollama model configuration
- `backend/ollama_api.py` - Optional FastAPI proxy for Ollama

**Files to Modify:**

- `frontend/src/lib/api.ts` - Update API URL to Ollama endpoint
- OR keep FastAPI as proxy

## Advantages

1. **Simpler Deployment**: No need for Docker/Gradio setup
2. **Better Performance**: GGUF format is optimized for inference
3. **Flexible**: Run locally or on any server
4. **API Compatible**: Ollama API similar to OpenAI format

## Disadvantages

1. **Model Conversion**: Need to convert model format (one-time)
2. **Server Required**: Need to run Ollama server (can be local)
3. **Setup Required**: Need to install Ollama and convert model

## Comparison: Ollama vs HF Spaces

| Feature     | Ollama              | HF Spaces       |
| ----------- | ------------------- | --------------- |
| Setup       | Medium (conversion) | Easy (Git push) |
| API         | REST API            | Gradio + API    |
| Performance | Fast (GGUF)         | Medium          |
| GPU         | Optional            | Free ZeroGPU    |
| Deployment  | Self-hosted         | Managed         |
| Cost        | Free (self-hosted)  | Free            |

## Next Steps (After Approval)

1. Create model conversion script
2. Create Ollama Modelfile
3. Update API endpoints (frontend or backend)
4. Create deployment instructions

## Questions to Consider

1. **Where to deploy Ollama?**

   - Local machine (for testing)
   - Cloud server (Render, Railway, Fly.io)
   - VPS (DigitalOcean, Linode, etc.)

2. **Keep FastAPI backend?**

   - Option A: Frontend → Ollama (direct)
   - Option B: Frontend → FastAPI → Ollama (proxy)

3. **Model size preference?**
   - 4-bit quantized (smaller, faster)
   - 8-bit quantized (better quality, larger)

---

**Ready for Approval:**
Please review this plan and let me know:

- ✅ Approve to proceed with Ollama deployment
- ⚠️ Want changes to the plan
- ❌ Prefer a different approach
