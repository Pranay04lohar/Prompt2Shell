#!/usr/bin/env python3
"""
Start the FastAPI server for Prompt2Shell backend.
Run from the backend directory: python run_server.py
"""
import uvicorn
import sys
import os

# Add src to path before importing
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, "src")
sys.path.insert(0, src_dir)

# Now import the app directly
from api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=False)

