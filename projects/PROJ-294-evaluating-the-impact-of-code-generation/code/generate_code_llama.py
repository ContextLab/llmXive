"""
CodeLlama Sensitivity Implementation (T052)

Generates code samples using CodeLlama-7b-Instruct-hf (8-bit quantized)
for sensitivity analysis. Targets GPU environment (Kaggle) as CPU inference
for 7B models is intractable.

Output: data/generated/llama_samples.json
Dependency: T010 (HumanEval dataset)
"""
import os
import sys
import json
import logging
import time
import torch
from typing import List, Dict, Any, Optional

# Attempt to import local utilities
try:
    from utils import setup_logging, get_logger, set_task_id, get_task_id
except ImportError:
    # Fallback for direct execution if utils is not in path
    def setup_logging(task_id=None):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    def set_task_id(tid):
        pass
    
    def get_task_id():
        return None

# Constants
MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"
OUTPUT_PATH = "data/generated/llama_samples.json"
INPUT_PATH = "data/raw/humaneval.parquet"
TASK_ID = "T052"

def ensure_state_dir():
    """Ensure the state directory exists."""
    state_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "state")
    os.makedirs(state_dir, exist_ok=True)
    return state_dir

def ensure_log_dir():
    """Ensure the log directory exists."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def check_gpu_availability():
    """Check if a GPU is available."""
    if not torch.cuda.is_available():
        logging.error("No GPU available. This task requires a GPU for CodeLlama-7b.")
        return False
    logging.info(f"GPU available: {torch.cuda.get_device_name(0)}")
    return True

def load_model_gpu():
    """Load the CodeLlama-7b-Instruct model with 8-bit quantization on GPU."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        
        logging.info(f"Loading model: {MODEL_NAME}")
        
        # Configure 8-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        
        logging.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logging.error(f"Failed to load model: {e}")
        raise

def generate_code_for_task(task_prompt: str, model, tokenizer, max_new_tokens: int = 512) -> Optional[str]:
    """Generate code for a single task prompt."""
    try:
        # Format prompt for CodeLlama-Instruct
        # CodeLlama-Instruct expects a specific format: [INST] ... [/INST]
        formatted_prompt = f"[INST] Write Python code to solve the following problem:\n\n{task_prompt}\n\n[/INST]"
        
        inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.2,
                top_p=0.95,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract code block if present (CodeLlama often outputs markdown blocks)
        if "```python" in generated_text:
            start_idx = generated_text.find("```python") + len("```python")
            end_idx = generated_text.find("```", start_idx)
            if end_idx != -1:
                code = generated_text[start_idx:end_idx].strip()
            else:
                code = generated_text[start_idx:].strip()
        elif "```" in generated_text:
            start_idx = generated_text.find("```") + len("```")
            end_idx = generated_text.find("```", start_idx)
            if end_idx != -1:
                code = generated_text[start_idx:end_idx].strip()
            else:
                code = generated_text[start_idx:].strip()
        else:
            code = generated_text.strip()
        
        # Clean up any trailing instruction text
        if "Here is the code:" in code:
            code = code.split("Here is the code:")[1].strip()
        if "Sure, here is the code:" in code:
            code = code.split("Sure, here is the code:")[1].strip()
            
        return code
    except Exception as e:
        logging.error(f"Generation failed for task: {e}")
        return None

def main():
    """Main entry point for CodeLlama code generation."""
    logger = setup_logging(task_id=TASK_ID)
    set_task_id(TASK_ID)
    
    logging.info(f"Starting CodeLlama code generation (Task: {TASK_ID})")
    
    # Check GPU availability
    if not check_gpu_availability():
        logging.critical("GPU is required for this task but not available. Aborting.")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_PATH)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load model
    model, tokenizer = load_model_gpu()
    
    # Load HumanEval dataset
    try:
        from datasets import load_dataset
        logging.info(f"Loading HumanEval dataset from {INPUT_PATH}")
        
        if os.path.exists(INPUT_PATH):
            # Load from local parquet if it exists
            ds = load_dataset("parquet", data_files={"test": INPUT_PATH}, split="test")
        else:
            # Fallback to HuggingFace if local file doesn't exist
            logging.warning(f"Local file {INPUT_PATH} not found. Downloading from HuggingFace.")
            ds = load_dataset("openai/openai_humaneval", split="test")
        
        logging.info(f"Loaded {len(ds)} tasks from HumanEval dataset.")
    except Exception as e:
        logging.error(f"Failed to load HumanEval dataset: {e}")
        sys.exit(1)
    
    # Generate code for all tasks
    samples = []
    failed_tasks = []
    
    for idx, task in enumerate(ds):
        task_id = task["task_id"]
        prompt = task["prompt"]
        
        logging.info(f"Processing task {idx+1}/{len(ds)}: {task_id}")
        
        generated_code = generate_code_for_task(prompt, model, tokenizer)
        
        sample = {
            "task_id": task_id,
            "prompt": prompt,
            "generated_code": generated_code,
            "source_type": "llama_7b",
            "model_name": MODEL_NAME,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": generated_code is not None
        }
        
        samples.append(sample)
        
        if generated_code is None:
            failed_tasks.append(task_id)
            logging.warning(f"Failed to generate code for {task_id}")
        else:
            logging.info(f"Successfully generated code for {task_id}")
    
    # Save results
    logging.info(f"Saving {len(samples)} samples to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    # Log summary
    success_count = sum(1 for s in samples if s["success"])
    logging.info(f"Generation complete: {success_count}/{len(samples)} tasks succeeded")
    
    if failed_tasks:
        logging.warning(f"Failed tasks: {failed_tasks}")
    
    logging.info(f"CodeLlama code generation completed successfully (Task: {TASK_ID})")

if __name__ == "__main__":
    main()
