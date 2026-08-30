"""
Docstring generation script for User Story 2.

Iterates over extracted method JSONs in data/raw/repos/, generates docstrings
using the configured model (with quantization fallback), and writes intermediate
results to data/processed/generation_batch_{repo_id}.json.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import BitsAndBytesConfig

# Import project utilities
from utils.model_loader import load_model, ModelLoadException
from utils.monitor import check_memory_limit, log_memory_snapshot, MemoryLimitException
from utils.exceptions import GenerationException
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/generation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
RAM_LIMIT_MB = 7000  # 7 GB
FIXED_TEMPERATURE = 0.1  # Fixed low temperature as per task description
MAX_NEW_TOKENS = 256

def load_method_data(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load method data from a JSON file.
    
    Args:
        json_path: Path to the JSON file containing extracted methods.
        
    Returns:
        List of method dictionaries.
        
    Raises:
        GenerationException: If file cannot be read or parsed.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise GenerationException(f"Expected list of methods in {json_path}, got {type(data)}")
        return data
    except json.JSONDecodeError as e:
        raise GenerationException(f"Failed to parse JSON in {json_path}: {e}")
    except FileNotFoundError:
        raise GenerationException(f"File not found: {json_path}")
    except Exception as e:
        raise GenerationException(f"Unexpected error loading {json_path}: {e}")

def generate_docstring_batch(
    methods: List[Dict[str, Any]],
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    batch_size: int = 4
) -> List[Dict[str, Any]]:
    """
    Generate docstrings for a batch of methods.
    
    Args:
        methods: List of method dictionaries with 'code' and 'ast_params'.
        model: Loaded transformer model.
        tokenizer: Loaded tokenizer.
        batch_size: Number of methods to process in parallel.
        
    Returns:
        List of updated method dictionaries with 'generated_docstring' added.
    """
    results = []
    
    # Prepare prompts
    prompts = []
    for method in methods:
        code = method.get('code', '')
        if not code:
            logger.warning("Skipping method with empty code")
            results.append({**method, 'generated_docstring': None, 'generation_error': 'Empty code'})
            continue
        
        # Simple prompt template
        prompt = f"""Write a Google-style docstring for the following Python function.
        Include a summary and parameter descriptions.
        
        Function:
        ```python
        {code}
        ```
        
        Docstring:
        """
        prompts.append(prompt)
    
    # Process in batches
    for i in range(0, len(prompts), batch_size):
        batch_prompts = prompts[i:i+batch_size]
        batch_methods = methods[i:i+batch_size]
        
        # Check memory before processing batch
        try:
            check_memory_limit(RAM_LIMIT_MB)
        except MemoryLimitException:
            logger.error(f"Memory limit exceeded during batch processing at index {i}")
            raise
        
        try:
            # Tokenize
            inputs = tokenizer(batch_prompts, return_tensors="pt", padding=True, truncation=True)
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW_TOKENS,
                    temperature=FIXED_TEMPERATURE,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # Decode and store results
            for j, (method, output_ids) in enumerate(zip(batch_methods, outputs)):
                generated_text = tokenizer.decode(output_ids, skip_special_tokens=True)
                # Extract just the generated part (after the last "Docstring:")
                if "Docstring:" in generated_text:
                    docstring_part = generated_text.split("Docstring:")[-1].strip()
                else:
                    docstring_part = generated_text.strip()
                
                results.append({
                    **method,
                    'generated_docstring': docstring_part
                })
                
        except Exception as e:
            logger.error(f"Error generating for batch starting at {i}: {e}")
            # Mark remaining methods in this batch as failed
            for method in batch_methods:
                results.append({
                    **method,
                    'generated_docstring': None,
                    'generation_error': str(e)
                })
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save generation results to a JSON file.
    
    Args:
        results: List of method dictionaries with generated docstrings.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """Main entry point for docstring generation."""
    logger.info("Starting docstring generation pipeline")
    
    config = get_config()
    input_dir = Path(config.get('input_dir', 'data/raw/repos'))
    output_dir = Path(config.get('output_dir', 'data/processed'))
    
    # Find all JSON files in input directory
    json_files = sorted(input_dir.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No JSON files found in {input_dir}")
        return
    
    logger.info(f"Found {len(json_files)} repository JSON files to process")
    
    # Load model with quantization fallback
    model, tokenizer = load_model()
    logger.info("Model loaded successfully")
    
    # Process each repository file
    for json_file in json_files:
        try:
            logger.info(f"Processing {json_file.name}")
            
            # Load data
            methods = load_method_data(json_file)
            logger.info(f"Loaded {len(methods)} methods from {json_file.name}")
            
            # Generate docstrings
            results = generate_docstring_batch(methods, model, tokenizer)
            
            # Determine output filename
            repo_id = json_file.stem.replace('methods_', '')
            output_filename = f"generation_batch_{repo_id}.json"
            output_path = output_dir / output_filename
            
            # Save results
            save_results(results, output_path)
            
            logger.info(f"Completed processing {json_file.name}")
            
        except MemoryLimitException:
            logger.critical(f"Memory limit exceeded while processing {json_file.name}. Aborting pipeline.")
            sys.exit(1)
        except GenerationException as e:
            logger.error(f"Failed to process {json_file.name}: {e}")
            continue
        except Exception as e:
            logger.exception(f"Unexpected error processing {json_file.name}: {e}")
            continue
    
    logger.info("Docstring generation pipeline completed")

if __name__ == "__main__":
    main()