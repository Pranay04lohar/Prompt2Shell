"""
Reusable agent utilities for command generation.
Can be used by both CLI and API server.
"""
import os
import json
import re
# Lazy import transformers to avoid dependency check issues at startup
try:
    import torch
except ImportError:
    torch = None


# Global model instance (singleton pattern)
_model = None
_tokenizer = None
_device = None


def initialize_model(base_model_name="microsoft/Phi-3-mini-4k-instruct", 
                     lora_adapter_path=None,
                     device_map=None):
    """
    Initialize the model and tokenizer (singleton pattern).
    Only loads once, subsequent calls return existing model.
    """
    global _model, _tokenizer, _device
    
    if _model is not None:
        return _model, _tokenizer, _device
    
    # Lazy import transformers here to avoid dependency check issues at module import time
    # Workaround for numpy detection issue in transformers dependency check
    try:
        # Ensure numpy is available (it might not be detected by transformers)
        import numpy
        numpy_version = numpy.__version__
        print(f"NumPy version detected: {numpy_version}")
    except ImportError:
        raise ImportError("NumPy is required but not installed. Please install it: pip install numpy>=1.17")
    
    # Import transformers with error handling for numpy detection issues
    # The problem: transformers checks numpy version during import and fails
    # Solution: Patch the checking mechanism if error occurs
    transformers_imported = False
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        transformers_imported = True
    except ValueError as e:
        # Catch the numpy version check error that occurs during import
        error_str = str(e)
        if "Unable to compare versions for numpy" in error_str:
            print(f"NumPy detection issue detected. NumPy is installed (v{numpy_version}) but transformers can't detect it.")
            print("This is likely due to corrupted package metadata.")
            print("Attempting to work around this issue...")
            
            # The error happens in dependency_versions_check.py during import
            # We need to patch it before it runs. Since it already ran and failed,
            # we can't easily patch it. However, we can try to manually install
            # or fix the numpy metadata, or use a different import strategy.
            
            # Alternative: Manually verify numpy and skip the check
            # Since we can't patch before import fails, let's try a different approach:
            # Import transformers by bypassing the dependency check
            try:
                # Try to import transformers modules directly, skipping __init__.py
                import importlib
                import sys
                
                # Manually load transformers components we need
                transformers_path = None
                try:
                    import site
                    for site_package in site.getsitepackages():
                        transformers_init = os.path.join(site_package, 'transformers', '__init__.py')
                        if os.path.exists(transformers_init):
                            transformers_path = os.path.join(site_package, 'transformers')
                            break
                except:
                    pass
                
                if transformers_path:
                    # Add to path and try direct imports
                    if transformers_path not in sys.path:
                        sys.path.insert(0, transformers_path)
                    
                    # Try importing the modules we need directly
                    try:
                        # Import model classes directly from their files
                        from transformers.models.auto import modeling_auto, tokenization_auto
                        AutoModelForCausalLM = modeling_auto.AutoModelForCausalLM
                        AutoTokenizer = tokenization_auto.AutoTokenizer
                        
                        from peft import PeftModel
                        transformers_imported = True
                        print("Successfully imported transformers using direct imports!")
                    except:
                        # If that fails, provide clear instructions
                        raise RuntimeError(
                            f"Transformers cannot detect NumPy (version {numpy_version} is installed). "
                            f"\n\nThe issue is corrupted package metadata in your Python environment. "
                            f"\n\nRecommended fix - Clean reinstall of NumPy:\n"
                            f"  1. pip uninstall numpy -y\n"
                            f"  2. pip install --no-cache-dir numpy>=1.17\n"
                            f"  3. Restart the server\n"
                            f"\nAlternatively, consider using a fresh virtual environment:\n"
                            f"  python -m venv new_venv\n"
                            f"  new_venv\\Scripts\\activate  # Windows\n"
                            f"  pip install -r requirements.txt\n"
                            f"\nOriginal error: {error_str}"
                        )
                else:
                    raise
            except Exception as bypass_error:
                raise RuntimeError(
                    f"Transformers cannot detect NumPy even though it's installed (version {numpy_version}). "
                    f"This is due to corrupted package metadata.\n\n"
                    f"Recommended fix:\n"
                    f"  pip uninstall numpy -y\n"
                    f"  pip install --no-cache-dir numpy>=1.17\n"
                    f"  Then restart the server.\n\n"
                    f"Original error: {error_str}\n"
                    f"Bypass attempt failed: {bypass_error}"
                )
        else:
            raise
    except ImportError as e:
        raise ImportError(f"Failed to import transformers or peft: {e}. Please ensure all dependencies are installed.")
    
    if not transformers_imported:
        raise ImportError("Failed to import transformers - see error messages above.")
    
    # Ensure torch is imported
    if torch is None:
        raise ImportError("PyTorch (torch) is not installed. Please install it: pip install torch")
    
    # Default to relative path from backend directory
    if lora_adapter_path is None:
        # Get backend directory (parent of src)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        lora_adapter_path = os.path.join(backend_dir, "lora_adapter", "lora_adapter")
    
    if device_map is None:
        # Check available GPU memory
        if torch.cuda.is_available():
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"GPU detected: {torch.cuda.get_device_name(0)} ({gpu_memory_gb:.1f} GB)")
            # Mistral-7B needs ~14GB FP16, but with 4-bit quantization needs ~4GB
            # If GPU has less than 6GB, might need quantization or CPU
            if gpu_memory_gb < 6:
                print("Warning: GPU has limited memory. Will use quantization to reduce memory usage.")
            device_map = "cuda"
        else:
            device_map = "cpu"
            print("No CUDA GPU detected, using CPU (will be slower)")
    
    _device = device_map
    
    print(f"Loading tokenizer and base model...")
    _tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    
    # Set padding token if not present (Mistral models might need this)
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token
    
    # Use quantization for large models to reduce memory usage
    # 4-bit quantization can reduce memory by ~75%
    use_quantization = torch.cuda.is_available()
    
    if use_quantization:
        try:
            from transformers import BitsAndBytesConfig
            # Use 4-bit quantization with QLoRA
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            print("Loading model with 4-bit quantization to save GPU memory...")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                device_map="auto",  # Let transformers handle device placement
                quantization_config=quantization_config,
                torch_dtype=torch.float16
            )
        except Exception as e:
            print(f"Warning: Quantization failed ({e}), falling back to CPU mode...")
            use_quantization = False
            device_map = "cpu"
    
    if not use_quantization:
        # Fallback: Use CPU or try with smaller precision
        print(f"Loading model on {device_map} (no quantization)...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            device_map=device_map if device_map == "cpu" else "auto",
            torch_dtype=torch.float32 if device_map == "cpu" else torch.float16
        )
    
    print(f"Loading LoRA adapter...")
    _model = PeftModel.from_pretrained(base_model, lora_adapter_path)
    
    return _model, _tokenizer, _device


def extract_commands_from_text(text):
    """Extract actual shell commands from Stack Overflow style text"""
    commands = []
    lines = text.split('\n')
    
    # Extract bash code blocks
    code_blocks = re.findall(r'```bash\n(.*?)\n```', text, re.DOTALL)
    for block in code_blocks:
        block_lines = block.strip().split('\n')
        for line in block_lines:
            line = line.strip()
            if line and not line.startswith('#'):  # Skip comments
                if len(line.split()) <= 10 and not any(keyword in line for keyword in ['while', 'for', 'if', 'function']):
                    commands.append(line)
                    break
    
    if commands:
        return commands
    
    # Otherwise, look line by line
    command_starters = ['git', 'cd', 'ls', 'mkdir', 'touch', 'mv', 'cp', 'rm', 'python', 'python3', 
                       'pip', 'pip3', 'npm', 'node', 'docker', 'curl', 'wget', 'tar', 'grep', 'find', 
                       'sudo', 'apt', 'yum', 'brew', 'head', 'tail', 'cat', 'sort', 'uniq', 'wc', 'awk', 'sed']
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if any(line.startswith(cmd + ' ') for cmd in command_starters):
            commands.append(line)
        elif line.startswith('$ '):
            commands.append(line[2:])
        elif line.startswith('```') and any(cmd in line for cmd in command_starters):
            cmd = line.replace('```bash', '').replace('```', '').strip()
            if cmd:
                commands.append(cmd)
        elif line.startswith('`') and line.endswith('`') and len(line) > 2:
            cmd = line[1:-1]
            if any(cmd.startswith(c + ' ') for c in command_starters):
                commands.append(cmd)
        elif '`' in line:
            backtick_commands = re.findall(r'`([^`]+)`', line)
            for cmd in backtick_commands:
                if any(cmd.startswith(c + ' ') for c in command_starters):
                    commands.append(cmd)
    
    return commands


def get_fallback_command(instruction):
    """Generate fallback command based on instruction keywords"""
    instruction_lower = instruction.lower()
    
    if any(word in instruction_lower for word in ['branch', 'git']):
        return "git checkout -b <branch-name>"
    elif any(word in instruction_lower for word in ['list', 'files']):
        return "ls -la"
    elif any(word in instruction_lower for word in ['directory', 'folder', 'mkdir']):
        return "mkdir <directory-name>"
    elif any(word in instruction_lower for word in ['virtual', 'venv', 'environment']):
        return "python3 -m venv <env_name>"
    elif any(word in instruction_lower for word in ['pip', 'install', 'package']):
        return "pip install <package_name>"
    elif any(word in instruction_lower for word in ['docker', 'container']):
        return "docker run <image_name>"
    elif any(word in instruction_lower for word in ['first', 'lines', 'head']) and any(word in instruction_lower for word in ['file', 'log']):
        if any(word in instruction_lower for word in ['ten', '10']):
            return "head -n 10 <filename>"
        else:
            return "head <filename>"
    elif any(word in instruction_lower for word in ['last', 'tail']) and any(word in instruction_lower for word in ['file', 'log']):
        return "tail <filename>"
    elif any(word in instruction_lower for word in ['read', 'view', 'show', 'cat']) and any(word in instruction_lower for word in ['file', 'log']):
        return "cat <filename>"
    else:
        return None


def extract_fallback_from_plan(plan, instruction):
    """Try to extract commands from plan using keyword matching"""
    commands = []
    lines = [line.strip() for line in plan.split('\n') if line.strip()]
    
    for line in lines[:5]:  # Check first 5 lines
        if 'git' in line.lower() and any(word in line.lower() for word in ['branch', 'checkout', 'create']):
            if 'checkout -b' in line.lower():
                commands.append('git checkout -b <branch-name>')
                break
            elif 'branch' in line.lower() and 'create' in line.lower():
                commands.append('git checkout -b <branch-name>')
                break
        elif any(word in line.lower() for word in ['venv', 'virtual', 'environment']) and 'python' in line.lower():
            if 'python3 -m venv' in line.lower() or 'python -m venv' in line.lower():
                commands.append('python3 -m venv <env_name>')
                break
        elif 'pip' in line.lower() and 'install' in line.lower():
            if 'requests' in line.lower():
                commands.append('pip install requests')
                break
        elif any(word in line.lower() for word in ['first', 'lines', 'head']) and any(word in line.lower() for word in ['file', '.log', '.txt']):
            if 'ten' in line.lower() or '10' in line:
                commands.append('head -n 10 <filename>')
                break
    
    return commands


def select_best_command(commands, instruction):
    """Select the most relevant command based on the instruction"""
    instruction_lower = instruction.lower()
    
    # For branch creation, prioritize 'checkout -b' over plain 'checkout'
    if any(word in instruction_lower for word in ['create', 'new']) and 'branch' in instruction_lower:
        for cmd in commands:
            if 'checkout -b' in cmd and not any(word in cmd for word in ['merge', 'delete', 'remove']):
                return cmd
    
    # For file operations, prioritize specific file commands
    if any(word in instruction_lower for word in ['first', 'lines', 'head']):
        for cmd in commands:
            if cmd.startswith('head'):
                return cmd
    
    if any(word in instruction_lower for word in ['last', 'tail']):
        for cmd in commands:
            if cmd.startswith('tail'):
                return cmd
    
    # For virtual environment, prioritize venv creation
    if any(word in instruction_lower for word in ['virtual', 'venv', 'environment']):
        for cmd in commands:
            if 'python' in cmd and 'venv' in cmd:
                return cmd
    
    # For pip, prioritize install commands
    if 'install' in instruction_lower:
        for cmd in commands:
            if 'pip install' in cmd:
                return cmd
    
    # Default: return the first command
    return commands[0] if commands else None


def generate_command(instruction, model=None, tokenizer=None, device=None, 
                    base_model_name="microsoft/Phi-3-mini-4k-instruct",
                    lora_adapter_path=None):
    """
    Generate shell command from natural language instruction.
    
    Returns:
        tuple: (command, plan) where command is the best extracted command and plan is the raw model response
    """
    # If a remote model endpoint is configured, proxy the request instead of loading a local model
    remote_url = os.getenv("MODEL_ENDPOINT_URL")
    if remote_url:
        try:
            import requests
            resp = requests.post(remote_url, json={"prompt": instruction}, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            cmd = data.get("response") or data.get("command") or ""
            plan = cmd
            if not cmd:
                return "# No command returned", ""
            return cmd, plan
        except Exception as e:
            # Fall through to local model as a backup if available
            print(f"Remote MODEL_ENDPOINT_URL call failed: {e}. Falling back to local model if available.")

    # Initialize model if not provided
    if model is None or tokenizer is None:
        if lora_adapter_path is None:
            model, tokenizer, device = initialize_model(base_model_name)
        else:
            model, tokenizer, device = initialize_model(base_model_name, lora_adapter_path)
    
    # Generate plan using appropriate prompt format based on model
    # Phi-3-mini uses chat template format (similar to Mistral)
    if "phi-3" in base_model_name.lower():
        # Phi-3-mini uses chat template format
        system_prompt = "You are a helpful assistant that generates shell commands from natural language instructions. Provide clear, executable commands."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction}
        ]
        # Apply chat template if available
        if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
            # Fallback format
            prompt = f"<|user|>\n{instruction}<|end|>\n<|assistant|>"
    elif "phi-2" in base_model_name.lower() or "phi2" in base_model_name.lower():
        # Phi-2 format: simple instruction-based prompt
        system_prompt = "You are a helpful assistant that generates shell commands from natural language instructions."
        prompt = f"Instruct: {instruction}\nOutput:"
    elif "mistral" in base_model_name.lower() or "tinyllama" in base_model_name.lower():
        # Models with chat templates
        system_prompt = "You are a helpful assistant that generates shell commands from natural language instructions. Provide clear, executable commands."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction}
        ]
        # Apply chat template if available
        if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
            # Fallback to simple format
            prompt = f"[INST] {instruction} [/INST]"
    else:
        # Generic format for other models
        prompt = f"Question: {instruction}\n\nAnswer:"
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract the answer part - handle different model formats
    if "<|assistant|>" in response:
        # Phi-3 format: extract text after <|assistant|>
        plan = response.split("<|assistant|>")[-1].strip()
        # Remove end token if present
        if "<|end|>" in plan:
            plan = plan.split("<|end|>")[0].strip()
    elif "Output:" in response:
        # Phi-2 format: extract text after "Output:"
        plan = response.split("Output:")[-1].strip()
    elif "[/INST]" in response:
        # Mistral format: extract text after [/INST]
        plan = response.split("[/INST]")[-1].strip()
    elif "Answer:" in response:
        # Legacy format
        plan = response.split("Answer:")[-1].strip()
    else:
        # Try to extract just the generated part
        if prompt in response:
            plan = response.split(prompt)[-1].strip()
        else:
            plan = response.strip()
    
    # Extract commands using the extraction function
    commands = extract_commands_from_text(plan)
    
    # If no clear commands found, try to extract from the first meaningful lines
    if not commands:
        commands = extract_fallback_from_plan(plan, instruction)
    
    # Output the best command or fallback
    if commands:
        best_command = select_best_command(commands, instruction)
        if best_command:
            return best_command, plan
    
    # Fallback based on common tasks
    fallback = get_fallback_command(instruction)
    if fallback:
        return fallback, plan
    
    return "# Command not recognized", plan


def log_command(instruction, command, log_path=None):
    """Log the instruction and command to a JSONL file"""
    if log_path is None:
        # Get backend directory (parent of src)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(backend_dir, "logs", "trace.jsonl")
    
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as logf:
        logf.write(json.dumps({"instruction": instruction, "step": command}) + "\n")

