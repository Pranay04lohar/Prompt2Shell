import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_MODEL = "microsoft/Phi-3-mini-4k-instruct"
LORA_PATH = r"backend/lora_adapter/lora_adapter"  # adjust if needed
OUTPUT_DIR = r"merged-phi3-prompt2shell"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading base model...")
base = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype="auto",
    device_map="cpu"
)

print("Applying LoRA adapter...")
merged = PeftModel.from_pretrained(base, LORA_PATH)
merged = merged.merge_and_unload()  # bake LoRA weights into base model

print("Saving merged model...")
merged.save_pretrained(OUTPUT_DIR)

print("Saving tokenizer...")
tok = AutoTokenizer.from_pretrained(BASE_MODEL)
tok.save_pretrained(OUTPUT_DIR)

print(f"Done. Merged model at: {OUTPUT_DIR}")