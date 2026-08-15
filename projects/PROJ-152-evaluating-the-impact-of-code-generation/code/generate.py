"""
Code Generation Module for llmXive Project PROJ-152.

Implements model loading, snippet generation, and result saving for
evaluating the impact of code generation models on code security.
"""
import os
import sys
import time
import signal
import logging
import hashlib
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# Import project config
import config
from update_state import calculate_file_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/failures.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
GENERATION_TIMEOUT = 120  # seconds per snippet
MAX_NEW_TOKENS = 256
BATCH_SIZE = 1
QUANTIZATION_BITS = 4

class TimeoutError(Exception):
    """Custom timeout error for generation tasks."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for generation timeout."""
    raise TimeoutError(f"Generation timed out after {GENERATION_TIMEOUT} seconds")

def load_model(model_name: str, model_path: str) -> Tuple[Any, Any]:
    """
    Load a model with 4-bit quantization for CPU execution.
    
    Args:
        model_name: Name of the model (e.g., 'starcoder-base', 'codegen')
        model_path: Path to the model directory or HuggingFace model ID
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading model: {model_name} from {model_path}")
    
    # Configure 4-bit quantization for CPU
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float32,  # Use float32 for CPU compatibility
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        llm_int8_enable_fp32_cpu_offload=True,
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head"],
        llm_int8_threshold=6.0
    )
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            padding_side="left"
        )
        
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            device_map="cpu",  # Force CPU for safety
            trust_remote_code=True,
            torch_dtype=torch.float32
        )
        
        model.eval()
        logger.info(f"Successfully loaded {model_name}")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {str(e)}")
        raise

def generate_snippet(
    model: Any,
    tokenizer: Any,
    prompt: str,
    model_name: str
) -> str:
    """
    Generate a code snippet from a prompt with timeout handling.
    
    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        prompt: Input prompt string
        model_name: Name of the model for logging
        
    Returns:
        Generated code snippet string
    """
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(GENERATION_TIMEOUT)
    
    try:
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        
        # Generate with constraints
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.1
            )
        
        # Decode output
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part (after the prompt)
        if generated.startswith(prompt):
            snippet = generated[len(prompt):].strip()
        else:
            snippet = generated.strip()
        
        return snippet
        
    except TimeoutError as e:
        logger.warning(f"Timeout generating for model {model_name}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating snippet for model {model_name}: {str(e)}")
        raise
    finally:
        signal.alarm(0)  # Cancel the alarm

def load_prompts(manifest_path: str) -> List[Dict[str, Any]]:
    """
    Load prompts from the unified manifest.
    
    Args:
        manifest_path: Path to manifest.json
        
    Returns:
        List of prompt dictionaries
    """
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    return manifest.get('prompts', [])

def save_results(
    results: List[Dict[str, Any]],
    output_path: str,
    failures_log_path: str
) -> None:
    """
    Save generation results to CSV and log failures.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output CSV file
        failures_log_path: Path to failures log file
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['snippet_id', 'model', 'prompt_id', 'code', 'line_count', 'timestamp']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            # Calculate line count
            line_count = len(result['code'].splitlines()) if result['code'] else 0
            
            writer.writerow({
                'snippet_id': result['snippet_id'],
                'model': result['model'],
                'prompt_id': result['prompt_id'],
                'code': result['code'],
                'line_count': line_count,
                'timestamp': result['timestamp']
            })
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """Main generation loop to process all prompts with all models."""
    logger.info("Starting generation pipeline for PROJ-152")
    
    # Load configuration
    prompts_manifest = config.PROMPTS_MANIFEST_PATH
    output_csv = config.GENERATED_CSV_PATH
    
    # Define models to run
    models_config = [
        {
            "name": "starcoder-base",
            "path": "bigcode/starcoderbase-1b"  # Smaller version for CPU
        },
        {
            "name": "codegen",
            "path": "Salesforce/codegen-600m"
        },
        {
            "name": "gpt-neox",
            "path": "EleutherAI/pythia-1b"  # Using Pythia as GPT-NeoX alternative
        }
    ]
    
    # Load prompts
    prompts = load_prompts(prompts_manifest)
    logger.info(f"Loaded {len(prompts)} prompts")
    
    if len(prompts) == 0:
        logger.error("No prompts found in manifest. Exiting.")
        sys.exit(1)
    
    all_results = []
    failure_count = 0
    
    for model_config in models_config:
        model_name = model_config["name"]
        model_path = model_config["path"]
        
        try:
            # Load model
            model, tokenizer = load_model(model_name, model_path)
            
            # Process each prompt
            for prompt_data in prompts:
                prompt_id = prompt_data['id']
                prompt_text = prompt_data['prompt']
                
                snippet_id = f"{model_name}_{prompt_id}"
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                
                try:
                    # Generate snippet
                    generated_code = generate_snippet(model, tokenizer, prompt_text, model_name)
                    
                    result = {
                        'snippet_id': snippet_id,
                        'model': model_name,
                        'prompt_id': prompt_id,
                        'code': generated_code,
                        'timestamp': timestamp
                    }
                    
                    all_results.append(result)
                    logger.info(f"Generated: {snippet_id}")
                    
                except Exception as e:
                    failure_count += 1
                    logger.error(f"Failed to generate {snippet_id}: {str(e)}")
                    # Log to failures file
                    with open(config.FAILURES_LOG_PATH, 'a', encoding='utf-8') as f:
                        f.write(f"{timestamp} - {model_name} - {prompt_id} - ERROR: {str(e)}\n")
            
            # Unload model to free memory
            del model, tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info(f"Completed model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {str(e)}")
            with open(config.FAILURES_LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - MODEL_LOAD_ERROR - {model_name} - {str(e)}\n")
    
    # Save results
    save_results(all_results, output_csv, config.FAILURES_LOG_PATH)
    
    # Update state
    from update_state import update_state_for_directory
    update_state_for_directory('data/generated')
    
    logger.info(f"Generation pipeline completed. Total: {len(all_results)}, Failures: {failure_count}")
    logger.info(f"Output saved to {output_csv}")

if __name__ == "__main__":
    main()
