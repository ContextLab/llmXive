import json
import logging
import os
import sys
import time
import traceback
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project API
from config import get_config, set_global_seed, get_max_memory_mb, SEED
from utils.model_loader import load_model, ModelLoadException
from utils.monitor import setup_logger, get_memory_usage_mb, check_memory_limit, MemoryLimitException
from utils.exceptions import GenerationException

# Constants
RAM_LIMIT_MB = 7000  # 7 GB limit as per Spec

def load_method_data(input_dir: str) -> List[Dict[str, Any]]:
    """Load method data from a JSON file in the input directory."""
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    # Load all JSON files in the directory (batch files from T024)
    all_methods = []
    for json_file in sorted(input_path.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_methods.extend(data)
                else:
                    all_methods.append(data)
        except json.JSONDecodeError as e:
            logging.warning(f"Skipping invalid JSON file {json_file}: {e}")
    return all_methods

def generate_docstring_batch(
    model: Any,
    tokenizer: Any,
    methods: List[Dict[str, Any]],
    temperature: float = 0.2,
    max_new_tokens: int = 256
) -> List[Dict[str, Any]]:
    """Generate docstrings for a batch of methods with memory monitoring."""
    results = []
    
    for i, method_data in enumerate(methods):
        # MEMORY MONITORING CHECK (T025 Requirement)
        # Check memory usage BEFORE processing each method
        current_ram = get_memory_usage_mb()
        if current_ram > RAM_LIMIT_MB:
            # Log the specific entry required by T025
            log_msg = f"RAM_LIMIT_EXCEEDED: Current RAM {current_ram:.2f}MB > Limit {RAM_LIMIT_MB}MB at method {i}/{len(methods)}"
            logging.critical(log_msg)
            
            # Write to monitor.log explicitly as required
            monitor_log_path = Path("logs/monitor.log")
            monitor_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(monitor_log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {log_msg}\n")
            
            # Raise the exception defined in code/utils/exceptions.py
            raise MemoryLimitException(log_msg)
        
        # Generate docstring
        try:
            signature = method_data.get('signature', '')
            if not signature:
                generated = ""
            else:
                # Prepare input
                prompt = f"Write a docstring for this Python method:\n{signature}"
                inputs = tokenizer(prompt, return_tensors="pt")
                
                # Generate
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
                generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
                # Extract just the generated part (remove prompt)
                generated = generated[len(prompt):].strip()
            
            # Record result
            result = method_data.copy()
            result['generated_docstring'] = generated
            result['generation_status'] = 'success'
            results.append(result)
            
        except Exception as e:
            # Log error but continue with next method
            logging.error(f"Failed to generate for method {i}: {e}")
            result = method_data.copy()
            result['generated_docstring'] = ""
            result['generation_status'] = 'error'
            results.append(result)
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save results to a JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved {len(results)} results to {output_path}")

def process_repo_with_fallback(
    input_path: str,
    output_path: str,
    temperature: float = 0.2
):
    """Process a single repo batch file with memory monitoring and model fallback."""
    # Load data
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            methods = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_path}")
    except json.JSONDecodeError as e:
        raise GenerationException(f"Invalid JSON in {input_path}: {e}")
    
    # Load model with quantization fallback (T011 requirement)
    try:
        model, tokenizer = load_model()
        logging.info("Model loaded successfully")
    except ModelLoadException as e:
        raise ModelLoadException(f"Failed to load model with fallback: {e}")
    
    # Generate docstrings with memory monitoring
    try:
        results = generate_docstring_batch(
            model=model,
            tokenizer=tokenizer,
            methods=methods,
            temperature=temperature
        )
        save_results(results, output_path)
    except MemoryLimitException as e:
        # Re-raise to ensure the process aborts as required
        raise e
    except Exception as e:
        raise GenerationException(f"Generation failed: {e}")

def main():
    """Main entry point for docstring generation with memory monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate docstrings with memory monitoring")
    parser.add_argument("--input-dir", type=str, default="data/raw/repos",
                      help="Directory containing input JSON files")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                      help="Directory for output JSON files")
    parser.add_argument("--temperature", type=float, default=0.2,
                      help="Temperature for generation")
    parser.add_argument("--seed", type=int, default=SEED,
                      help="Random seed")
    
    args = parser.parse_args()
    
    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "generate.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set global seed
    set_global_seed(args.seed)
    
    # Setup monitor logger
    monitor_logger = setup_logger("logs/monitor.log")
    
    # Process all batch files
    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    batch_files = sorted(input_path.glob("*.json"))
    
    if not batch_files:
        logging.warning(f"No JSON files found in {args.input_dir}")
        return
    
    for batch_file in batch_files:
        repo_slug = batch_file.stem  # e.g., "requests" from "requests.json"
        output_file = output_path / f"generation_batch_{repo_slug}.json"
        
        logging.info(f"Processing {batch_file.name} -> {output_file.name}")
        
        try:
            process_repo_with_fallback(
                input_path=str(batch_file),
                output_path=str(output_file),
                temperature=args.temperature
            )
        except MemoryLimitException as e:
            logging.critical(f"Memory limit exceeded, aborting process: {e}")
            # Immediate abort as required by T025
            sys.exit(1)
        except Exception as e:
            logging.error(f"Failed to process {batch_file.name}: {e}")
            # Continue with next file unless critical error
            continue
    
    logging.info("Generation complete")

if __name__ == "__main__":
    main()