"""
User Story 2: LLM Docstring Generation with Resource Constraints.

Implements the docstring generation loop reading from truncated method lists
in data/raw/repos/*.json and writing results to data/processed/generation_results.json.

Enforces:
- Fixed temperature sampling
- Memory monitoring (abort if > 7GB)
- Strict 4-bit quantization (via model_loader)
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports matching API surface
from utils.model_loader import load_model, ModelLoadException
from utils.monitor import (
    setup_logger, 
    get_memory_usage_mb, 
    check_memory_limit, 
    MemoryLimitException
)
from utils.repo_loader import load_repo_list
from config import get_config

# Configure logging
logger = setup_logger("generation", "logs/monitor.log")

# Constants
RAM_LIMIT_MB = 7000  # 7 GB limit
TEMPERATURE = 0.7    # Fixed temperature as per task description
MAX_SEQ_LENGTH = 1024

class GenerationException(Exception):
    """Custom exception for generation failures."""
    pass

def load_method_data(input_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all method data from JSON files in the input directory.
    
    Reads from data/raw/repos/*.json (produced by T019).
    """
    all_methods = []
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {input_dir}")
    
    logger.info(f"Found {len(json_files)} repository JSON files in {input_dir}")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both list of methods and dict with 'methods' key
            if isinstance(data, list):
                methods = data
            elif isinstance(data, dict) and 'methods' in data:
                methods = data['methods']
            else:
                logger.warning(f"Unexpected format in {json_file}, skipping")
                continue
            
            logger.info(f"Loaded {len(methods)} methods from {json_file.name}")
            all_methods.extend(methods)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {json_file}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error reading {json_file}: {e}")
            continue
    
    if not all_methods:
        raise ValueError("No valid method data found in input directory")
    
    logger.info(f"Total methods loaded: {len(all_methods)}")
    return all_methods

def generate_docstring_batch(
    model, 
    tokenizer, 
    methods: List[Dict[str, Any]], 
    batch_size: int = 4
) -> List[Dict[str, Any]]:
    """
    Generate docstrings for a batch of methods.
    
    Uses fixed temperature sampling and monitors memory.
    """
    results = []
    
    for i in range(0, len(methods), batch_size):
        batch = methods[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} methods)")
        
        # Check memory before processing batch
        current_ram = get_memory_usage_mb()
        logger.debug(f"Current RAM usage: {current_ram:.1f} MB")
        
        if current_ram > RAM_LIMIT_MB:
            logger.error(f"RAM limit exceeded: {current_ram:.1f} MB > {RAM_LIMIT_MB} MB")
            raise MemoryLimitException(f"RAM usage {current_ram:.1f} MB exceeds limit {RAM_LIMIT_MB} MB")
        
        for method_data in batch:
            try:
                # Construct prompt
                signature = method_data.get('signature', '')
                prompt = f"Generate a docstring for the following Python method:\n\n{signature}\n\nDocstring:"
                
                # Tokenize
                inputs = tokenizer(
                    prompt, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=MAX_SEQ_LENGTH
                ).to(model.device)
                
                # Generate with fixed temperature
                with torch.no_grad():
                    output_ids = model.generate(
                        **inputs,
                        max_new_tokens=256,
                        temperature=TEMPERATURE,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                # Decode and clean
                generated_text = tokenizer.decode(
                    output_ids[0][inputs['input_ids'].shape[1]:], 
                    skip_special_tokens=True
                ).strip()
                
                # Handle empty/whitespace results
                if not generated_text or generated_text.isspace():
                    logger.warning(f"Empty docstring generated for {method_data.get('method_name', 'unknown')}")
                    generated_text = ""  # Mark as empty but not None
                
                results.append({
                    'repo_url': method_data.get('repo_url'),
                    'file_path': method_data.get('file_path'),
                    'method_name': method_data.get('method_name'),
                    'signature': signature,
                    'human_docstring': method_data.get('human_docstring'),
                    'generated_docstring': generated_text,
                    'generation_status': 'success'
                })
                
            except Exception as e:
                logger.error(f"Generation failed for {method_data.get('method_name', 'unknown')}: {e}")
                results.append({
                    'repo_url': method_data.get('repo_url'),
                    'file_path': method_data.get('file_path'),
                    'method_name': method_data.get('method_name'),
                    'signature': method_data.get('signature', ''),
                    'human_docstring': method_data.get('human_docstring'),
                    'generated_docstring': None,
                    'generation_status': 'error',
                    'error_message': str(e)
                })
        
        # Log memory after batch
        current_ram = get_memory_usage_mb()
        logger.info(f"Batch complete. Current RAM: {current_ram:.1f} MB")
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path):
    """Save generation results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """Main entry point for docstring generation."""
    logger.info("Starting docstring generation pipeline")
    start_time = time.time()
    
    # Load configuration
    try:
        config = get_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Define paths
    input_dir = Path("data/raw/repos")
    output_path = Path("data/processed/generation_results.json")
    
    # Load method data
    try:
        methods = load_method_data(input_dir)
    except Exception as e:
        logger.error(f"Failed to load method data: {e}")
        sys.exit(1)
    
    # Load model with strict 4-bit quantization
    logger.info("Loading model with 4-bit quantization...")
    try:
        model, tokenizer = load_model(
            model_name=config.model_name,
            quantization_bits=4
        )
        logger.info("Model loaded successfully")
    except ModelLoadException as e:
        logger.error(f"Model loading failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during model loading: {e}")
        sys.exit(1)
    
    # Generate docstrings
    logger.info(f"Generating docstrings for {len(methods)} methods...")
    try:
        results = generate_docstring_batch(model, tokenizer, methods)
    except MemoryLimitException as e:
        logger.error(f"Memory limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        sys.exit(1)
    
    # Save results
    try:
        save_results(results, output_path)
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        sys.exit(1)
    
    # Final report
    elapsed_time = time.time() - start_time
    success_count = sum(1 for r in results if r['generation_status'] == 'success')
    error_count = len(results) - success_count
    
    logger.info(f"Generation complete in {elapsed_time:.1f} seconds")
    logger.info(f"Success: {success_count}, Errors: {error_count}")
    logger.info(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()
