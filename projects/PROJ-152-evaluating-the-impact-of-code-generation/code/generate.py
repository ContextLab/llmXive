"""
Code Generation Pipeline for Security Evaluation.
Implements generation loop to process prompts using loaded models.
"""
import os
import sys
import time
import signal
import logging
import hashlib
import json
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/failures.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Configuration imports
import config

# Custom exception for timeout
class TimeoutError(Exception):
    """Custom timeout exception for generation tasks."""
    pass

# Timeout handler using signal
def timeout_handler(signum, frame):
    raise TimeoutError("Generation timed out")

def load_model(model_name: str, device: str = "cpu"):
    """
    Load a model with 4-bit quantization as per T013.
    Expects model_name to be one of the configured models.
    """
    logger.info(f"Loading model: {model_name} on {device}")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from transformers import BitsAndBytesConfig

        # 4-bit quantization config for CPU
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float32,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )

        # Map model names to HuggingFace IDs
        model_map = {
            "starcoder-base": "bigcode/starcoderbase",
            "codegen-2b": "Salesforce/codegen-2B-multi",
            "gpt-neox-1.3b": "EleutherAI/gpt-neox-1.3b"
        }

        if model_name not in model_map:
            raise ValueError(f"Unknown model: {model_name}")

        hf_model_id = model_map[model_name]

        tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
        model = AutoModelForCausalLM.from_pretrained(
            hf_model_id,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True
        )

        model.eval()
        logger.info(f"Successfully loaded {model_name}")
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def generate_snippet(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_tokens: int = 256,
    timeout_seconds: int = 120
) -> str:
    """
    Generate a code snippet from a prompt with timeout handling.
    """
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,  # Greedy decoding for consistency
                temperature=None,
                top_p=None
            )
        
        generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        signal.alarm(0)  # Cancel alarm
        return generated_text

    except TimeoutError:
        signal.alarm(0)
        logger.warning(f"Generation timed out for prompt: {prompt[:50]}...")
        raise
    except Exception as e:
        signal.alarm(0)
        logger.error(f"Generation failed: {e}")
        raise

def load_prompts(manifest_path: str) -> List[Dict[str, Any]]:
    """
    Load prompts from the unified manifest file.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    return manifest.get('prompts', [])

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Save generation results to CSV.
    """
    import csv
    from datetime import datetime

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['snippet_id', 'model', 'prompt_id', 'code', 'line_count', 'timestamp']
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow(result)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """
    Main generation loop: process 30 prompts (N=90 snippets) across 3 models.
    """
    logger.info("Starting generation pipeline")
    
    # Configuration
    manifest_path = "data/prompts/manifest.json"
    output_path = "data/generated/snippets.csv"
    models = ["starcoder-base", "codegen-2b", "gpt-neox-1.3b"]
    
    # Load prompts
    try:
        prompts = load_prompts(manifest_path)
        logger.info(f"Loaded {len(prompts)} prompts from manifest")
        
        if len(prompts) != 30:
            logger.warning(f"Expected 30 prompts, found {len(prompts)}. Proceeding with available.")
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        raise

    all_results = []
    
    # Process each model
    for model_name in models:
        logger.info(f"Processing model: {model_name}")
        
        try:
            model, tokenizer = load_model(model_name)
        except Exception as e:
            logger.error(f"Skipping model {model_name} due to load failure: {e}")
            # Log failure but continue with other models
            continue
        
        # Process each prompt
        for prompt_data in prompts:
            prompt_id = prompt_data.get('id')
            prompt_text = prompt_data.get('prompt', '')
            
            if not prompt_text:
                logger.warning(f"Skipping empty prompt: {prompt_id}")
                continue
            
            logger.info(f"Generating for prompt {prompt_id} with model {model_name}")
            
            try:
                generated_code = generate_snippet(model, tokenizer, prompt_text)
                
                result = {
                    'snippet_id': f"{model_name}_{prompt_id}",
                    'model': model_name,
                    'prompt_id': prompt_id,
                    'code': generated_code,
                    'line_count': len(generated_code.splitlines()),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                all_results.append(result)
                
            except Exception as e:
                logger.error(f"Generation failed for {prompt_id} with {model_name}: {e}")
                # Log to failures.log (handled by logger config)
                continue
        
        # Clean up model to free memory
        del model
        del tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    # Save results
    if all_results:
        save_results(all_results, output_path)
        logger.info(f"Generation complete. Total snippets: {len(all_results)}")
    else:
        logger.error("No snippets were generated successfully.")
        raise RuntimeError("Generation pipeline produced no results")

if __name__ == "__main__":
    main()