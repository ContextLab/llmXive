"""
generate.py - Model loading and code generation pipeline.

Loads StarCoder-Base, CodeGen, and GPT-NeoX with CPU-only 4-bit quantization.
Generates code snippets from prompts with a 120s timeout per generation.
Outputs: data/generated/snippets.csv
"""

import os
import sys
import time
import signal
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/failures.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

# Project root relative to this file
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
GENERATED_DIR = DATA_DIR / "generated"
PROMPTS_FILE = DATA_DIR / "prompts" / "manifest.json"
OUTPUT_CSV = GENERATED_DIR / "snippets.csv"

# Ensure directories exist
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

# Model Configuration
# Using 4-bit quantization via bitsandbytes (CPU compatible)
# Note: bitsandbytes-cpu is required in requirements.txt
MODELS = [
    "bigcode/starcoderbase",
    "Salesforce/codegen-2B-mono",
    "EleutherAI/gpt-neox-20b", # Using 20b as standard, but task says GPT-NeoX 1.3b. 
                               # Adjusting to 1.3b if specific small model needed, 
                               # but standard GPT-NeoX is 20b. Task says "GPT-NeoX 1.3B".
                               # Let's use the 1.3b variant if it exists or the main one.
                               # HuggingFace: EleutherAI/gpt-neox-1.3b
    "EleutherAI/gpt-neox-1.3b"
]
MODEL_NAMES = {
    "bigcode/starcoderbase": "StarCoder-Base",
    "Salesforce/codegen-2B-mono": "CodeGen",
    "EleutherAI/gpt-neox-1.3b": "GPT-NeoX"
}

GENERATION_TIMEOUT = 120  # seconds
MAX_NEW_TOKENS = 256
BATCH_SIZE = 1

# Timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Generation timed out")

def load_model(model_id: str):
    """
    Load a model with 4-bit quantization for CPU.
    Requires: transformers, torch, bitsandbytes (cpu version)
    """
    logger.info(f"Loading model: {model_id}")
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import torch

        # 4-bit quantization config for CPU
        # Note: bitsandbytes CPU support is experimental but required for this task.
        # If bitsandbytes CPU fails, we fallback to standard loading (warning).
        try:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float32, # CPU uses float32
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                quantization_config=quantization_config,
                device_map="cpu", # Force CPU
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            logger.info(f"Model {model_id} loaded with 4-bit quantization.")
        except Exception as e:
            logger.warning(f"4-bit quantization failed for {model_id} ({e}). Attempting standard load.")
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="cpu",
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )

        tokenizer = AutoTokenizer.from_pretrained(model_id)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        return model, tokenizer
    except ImportError as e:
        logger.error(f"Missing dependencies for model loading: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {e}")
        raise

def generate_snippet(model, tokenizer, prompt: str, prompt_id: str, model_name: str) -> Optional[Dict[str, Any]]:
    """
    Generate a code snippet with timeout handling.
    """
    start_time = time.time()
    
    # Set signal for timeout (Unix only)
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(GENERATION_TIMEOUT)
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        # Move to CPU explicitly
        inputs = {k: v for k, v in inputs.items()} # Already on CPU if model is

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up: remove prompt from generated text if it was repeated
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):]
        
        elapsed = time.time() - start_time
        logger.info(f"Generated snippet for {prompt_id} ({model_name}) in {elapsed:.2f}s")
        
        return {
            "prompt_id": prompt_id,
            "model": model_name,
            "code": generated_text.strip(),
            "line_count": len(generated_text.splitlines()),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "success"
        }

    except TimeoutError:
        logger.error(f"Timeout generating for {prompt_id} ({model_name}) after {GENERATION_TIMEOUT}s")
        return {
            "prompt_id": prompt_id,
            "model": model_name,
            "code": "",
            "line_count": 0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "timeout"
        }
    except Exception as e:
        logger.error(f"Error generating for {prompt_id} ({model_name}): {e}")
        return {
            "prompt_id": prompt_id,
            "model": model_name,
            "code": "",
            "line_count": 0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": f"error: {str(e)}"
        }
    finally:
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0) # Cancel alarm

def load_prompts() -> List[Dict[str, Any]]:
    """Load prompts from manifest.json"""
    if not PROMPTS_FILE.exists():
        raise FileNotFoundError(f"Prompts manifest not found: {PROMPTS_FILE}")
    
    with open(PROMPTS_FILE, 'r') as f:
        data = json.load(f)
    
    return data.get("prompts", [])

def save_results(results: List[Dict[str, Any]]):
    """Save results to CSV"""
    import csv
    
    if not results:
        logger.warning("No results to save.")
        return

    fieldnames = ["snippet_id", "model", "prompt_id", "code", "line_count", "timestamp", "status"]
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            # Generate snippet_id based on hash of content to ensure uniqueness
            content_str = f"{r['model']}-{r['prompt_id']}-{r['code']}"
            snippet_id = hashlib.md5(content_str.encode()).hexdigest()[:12]
            r["snippet_id"] = snippet_id
            writer.writerow(r)
    
    logger.info(f"Saved {len(results)} results to {OUTPUT_CSV}")

def main():
    logger.info("Starting code generation pipeline.")
    
    # Load prompts
    prompts = load_prompts()
    logger.info(f"Loaded {len(prompts)} prompts.")
    
    all_results = []
    
    # Load and process each model
    for model_id in MODELS:
        model_name = MODEL_NAMES[model_id]
        try:
            model, tokenizer = load_model(model_id)
        except Exception as e:
            logger.error(f"Skipping model {model_name} due to load error: {e}")
            continue
        
        # Generate for each prompt
        for prompt_data in prompts:
            prompt_text = prompt_data.get("text", "")
            prompt_id = prompt_data.get("id", "unknown")
            
            if not prompt_text:
                logger.warning(f"Skipping empty prompt {prompt_id}")
                continue
            
            result = generate_snippet(model, tokenizer, prompt_text, prompt_id, model_name)
            all_results.append(result)
        
        # Optional: Clear GPU memory (not needed for CPU, but good practice)
        del model, tokenizer
        
    save_results(all_results)
    logger.info("Generation pipeline complete.")

if __name__ == "__main__":
    main()
