"""
CLI agent for generating shell commands from natural language.
Uses the reusable agent_utils module.
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_utils import generate_command, log_command, initialize_model
import torch

# Argument parsing
if len(sys.argv) < 2:
    print("Usage: python src/agent.py \"<your instruction>\"")
    sys.exit(1)
user_instruction = sys.argv[1]

# Print GPU info
if torch.cuda.is_available():
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA GPU not available. Running on CPU.")

# Initialize model
initialize_model()

# Generate command
print("Response:", end=" ")
command, _ = generate_command(user_instruction)

# Output the command
print(f"{command}")

# Log the command
log_command(user_instruction, command)
