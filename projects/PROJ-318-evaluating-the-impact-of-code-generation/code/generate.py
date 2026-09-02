"""
Docstring Generation Pipeline (User Story 2).

Loads the Salesforce/codegen-350M-mono model with strict 4-bit quantization (fallback to 8-bit/full),
iterates over extracted method data, generates docstrings, and handles memory constraints.
"""

import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project imports
from config import (
    get_config,
    set_global_seed,
    get_device_and_dtype,
    get_quantization_config,
    get_max_memory_mb,
    configure_logging
)
from utils.model_loader import load_model, ModelLoadException
from utils.monitor import (
    setup_logger,
    get_memory_usage_mb,
    check_memory_limit,
    log_memory_snapshot,
    MemoryLimitException as MonitorMemoryLimitException
)
from utils.exceptions import MemoryLimitException
from utils.coverage import calculate_parameter_coverage

# Constants
MAX_RETRIES_ON_MEMORY = 2
CHUNK_SIZE_DECREMENT = 250  # Reduce chunk size by this amount on memory error

def load_method_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load method data from a JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {input_path}, got {type(data)}")
    
    return data

def generate_docstring_batch(
    methods: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    batch_size: int = 10,
    temperature: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Generate docstrings for a batch of methods.
    
    Args:
        methods: List of method dictionaries containing 'signature' and 'ast_params'.
        model: Loaded transformer model.
        tokenizer: Loaded tokenizer.
        batch_size: Number of methods to process in one go (for batching if needed).
        temperature: Generation temperature (fixed low value).
    
    Returns:
        List of updated method dictionaries with 'generated_docstring'.
    """
    results = []
    
    for i in range(0, len(methods), batch_size):
        batch = methods[i : i + batch_size]
        batch_results = []
        
        for method in batch:
            try:
                # Construct prompt
                signature = method.get('signature', '')
                if not signature:
                    batch_results.append({
                        **method,
                        'generated_docstring': '',
                        'generation_error': 'Missing signature'
                    })
                    continue
                
                prompt = f"Generate a docstring for the following Python function:\n\n{signature}\n\nDocstring:"
                
                # Tokenize
                inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
                
                # Generate
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=128,
                        temperature=temperature,
                        do_sample=True if temperature > 0 else False,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                # Decode
                generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                # Remove prompt from result
                docstring = generated_text[len(prompt):].strip()
                
                batch_results.append({
                    **method,
                    'generated_docstring': docstring,
                    'generation_error': None
                })
                
            except Exception as e:
                logging.warning(f"Generation error for method {method.get('name', 'unknown')}: {e}")
                batch_results.append({
                    **method,
                    'generated_docstring': '',
                    'generation_error': str(e)
                })
        
        results.extend(batch_results)
        
        # Check memory after each batch
        current_mem = get_memory_usage_mb()
        max_mem_limit = get_max_memory_mb()
        
        if current_mem > max_mem_limit:
            raise MonitorMemoryLimitException(
                f"Memory limit exceeded: {current_mem:.2f}MB > {max_mem_limit}MB"
            )
        
        log_memory_snapshot("generate_docstring_batch")
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save generation results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved results to {output_path}")

def process_repo_with_fallback(
    repo_id: str,
    input_path: Path,
    output_path: Path,
    model: Any,
    tokenizer: Any,
    config: Dict[str, Any]
) -> bool:
    """
    Process a single repository's methods with memory fallback logic.
    
    Returns:
        True if processing succeeded, False if it failed permanently.
    """
    methods = load_method_data(input_path)
    total_methods = len(methods)
    logging.info(f"Processing {repo_id}: {total_methods} methods")
    
    # Initial chunk size (max 1000 as per spec, but we start with a reasonable batch)
    current_chunk_size = min(500, total_methods)
    retry_count = 0
    
    while retry_count <= MAX_RETRIES_ON_MEMORY:
        try:
            logging.info(f"Processing {repo_id} in chunks of {current_chunk_size} (Attempt {retry_count + 1})")
            
            all_results = []
            for i in range(0, total_methods, current_chunk_size):
                chunk = methods[i : i + current_chunk_size]
                logging.info(f"Processing chunk {i//current_chunk_size + 1}: {len(chunk)} methods")
                
                # Generate docstrings for this chunk
                chunk_results = generate_docstring_batch(
                    chunk, 
                    model, 
                    tokenizer, 
                    temperature=config.get('temperature', 0.1)
                )
                all_results.extend(chunk_results)
                
                # Check memory after chunk
                check_memory_limit()
            
            # Success! Save results
            save_results(all_results, output_path)
            return True
            
        except MonitorMemoryLimitException as e:
            logging.warning(f"Memory limit hit: {e}")
            retry_count += 1
            
            if retry_count > MAX_RETRIES_ON_MEMORY:
                logging.error(f"Failed to process {repo_id} after {MAX_RETRIES_ON_MEMORY} retries due to memory limits.")
                # Log the specific entry to monitor.log as required
                monitor_logger = setup_logger("monitor")
                monitor_logger.error(f"RAM_LIMIT_EXCEEDED: {repo_id} failed after retries. Error: {str(e)}")
                return False
            
            # Reduce chunk size and retry
            new_chunk_size = max(50, current_chunk_size - CHUNK_SIZE_DECREMENT)
            if new_chunk_size >= current_chunk_size:
                new_chunk_size = max(1, current_chunk_size // 2) # Ensure progress
            current_chunk_size = new_chunk_size
            logging.info(f"Retrying {repo_id} with smaller chunk size: {current_chunk_size}")
            
        except Exception as e:
            logging.error(f"Unexpected error processing {repo_id}: {e}")
            traceback.print_exc()
            return False

def main():
    """Main entry point for the generation pipeline."""
    # Setup logging
    configure_logging()
    logger = logging.getLogger(__name__)
    
    # Load config
    config = get_config()
    set_global_seed(config.seed)
    
    # Load model
    logger.info("Loading model with quantization config...")
    try:
        model, tokenizer = load_model(
            model_name=config.model_name,
            quantization_config=get_quantization_config(),
            device_map="auto"
        )
        logger.info("Model loaded successfully.")
    except ModelLoadException as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Find input files
    input_dir = Path("data/raw/repos")
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)
    
    input_files = sorted(input_dir.glob("*.json"))
    if not input_files:
        logger.warning(f"No input files found in {input_dir}")
        sys.exit(0)
    
    logger.info(f"Found {len(input_files)} input files to process.")
    
    # Process each repository
    success_count = 0
    for input_file in input_files:
        repo_id = input_file.stem
        output_file = Path(f"data/processed/generation_batch_{repo_id}.json")
        
        logger.info(f"Processing {repo_id}...")
        success = process_repo_with_fallback(
            repo_id=repo_id,
            input_path=input_file,
            output_path=output_file,
            model=model,
            tokenizer=tokenizer,
            config=config
        )
        
        if success:
            success_count += 1
        else:
            logger.error(f"Failed to complete {repo_id}")
    
    logger.info(f"Generation pipeline complete. Success: {success_count}/{len(input_files)}")

if __name__ == "__main__":
    main()