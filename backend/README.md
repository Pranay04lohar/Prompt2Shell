---
title: Prompt2Shell Backend
emoji: 🐚
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
app_port: 5000
---

# Prompt2Shell Backend API

FastAPI backend for generating shell commands from natural language using a fine-tuned Phi-3-mini model with LoRA adapters.

## Features

- 🤖 Fine-tuned Phi-3-mini model with QLoRA
- ⚡ 4-bit quantization for efficient inference
- 🔌 RESTful API with FastAPI
- 🐳 Dockerized for easy deployment

## API Endpoints

### Health Check
```
GET /health
```

### Generate Commands
```
POST /generate
Content-Type: application/json

{
  "prompt": "List all files modified today"
}
```

## Requirements

- Python 3.11+
- PyTorch
- Transformers
- PEFT (LoRA adapters)
- FastAPI
- Uvicorn

## Model

- Base Model: `microsoft/Phi-3-mini-4k-instruct`
- LoRA Adapter: Fine-tuned on shell command Q&A dataset
- Quantization: 4-bit (for GPU memory efficiency)

## Environment Variables

- `ALLOWED_ORIGINS`: Comma-separated list of CORS origins (default: localhost)
- `PORT`: Server port (default: 5000)

## License

MIT
