"""
Inference module for energy consumption assessment.
Loads models sequentially, runs inference on HumanEval problems,
measures energy using codecarbon, and writes results to CSV.
"""
import os
import json
import time
import csv
import gc
import logging
from typing import List, Dict, Any, Optional
import torch

from codecarbon import EmissionsTracker
from transformers import AutoModelForCausalLM, AutoTokenizer
from code.config import (
    get_model_hf_id,
    get_model_params_m,
    ensure_directories,
    DATA_PROCESSED_DIR,
    MODEL_IDS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants from config
MAX_NEW_TOKENS = 50  # Limit generation length
TEMPERATURE = 0.0
SEED = 42

def load_problems_from_jsonl(filepath: str) -> List[Dict[str, Any]]:
    """Load HumanEval problems from JSONL file."""
    problems = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                problems.append(json.loads(line))
    return problems

def unload_model(model: Any, tokenizer: Any) -> None:
    """Explicitly unload model and tokenizer to free RAM."""
    del model
    del tokenizer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Model unloaded and garbage collected.")

def count_tokens(text: str, tokenizer: Any) -> int:
    """Count tokens generated using the model's tokenizer."""
    if not text:
        return 0
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)

def run_inference_for_model(
    model_id: str,
    problems: List[Dict[str, Any]],
    max_tokens: int = MAX_NEW_TOKENS,
    temperature: float = TEMPERATURE
) -> List[Dict[str, Any]]:
    """
    Run inference for a single model on all problems.
    Returns list of results with energy, tokens, and runtime.
    """
    results = []
    hf_id = get_model_hf_id(model_id)
    params = get_model_params_m(model_id)

    logger.info(f"Loading model: {model_id} (HF: {hf_id}, Params: {params}M)")

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(
        hf_id,
        trust_remote_code=True,
        padding_side='left'
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        hf_id,
        trust_remote_code=True,
        torch_dtype=torch.float32,  # Force float32 for CPU stability
        low_cpu_mem_usage=True
    )
    model.eval()

    # Set seed for reproducibility
    torch.manual_seed(SEED)

    # Prepare output directory
    ensure_directories()

    # Run inference with codecarbon
    output_file = os.path.join(DATA_PROCESSED_DIR, 'energy_inference_raw.csv')
    
    # Clear any existing file to ensure fresh run
    if os.path.exists(output_file):
        os.remove(output_file)

    try:
        with EmissionsTracker(
            project_name=f"llmXive-{model_id}",
            experiment_name="inference-energy",
            output_dir=DATA_PROCESSED_DIR,
            log_level="info"
        ) as tracker:
            start_time = time.time()

            for problem in problems:
                problem_id = problem.get('task_id', 'unknown')
                prompt = problem.get('prompt', '')
                
                if not prompt:
                    logger.warning(f"Skipping problem {problem_id} due to empty prompt.")
                    continue

                # Tokenize input
                inputs = tokenizer(prompt, return_tensors='pt', padding=True)
                
                # Generate
                with torch.no_grad():
                    outputs = model.generate(
                        inputs['input_ids'],
                        attention_mask=inputs['attention_mask'],
                        max_new_tokens=max_tokens,
                        temperature=temperature,
                        do_sample=(temperature > 0),
                        pad_token_id=tokenizer.pad_token_id,
                        eos_token_id=tokenizer.eos_token_id
                    )

                # Decode generated text
                generated_ids = outputs[0, inputs['input_ids'].shape[1]:]
                generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

                # Count tokens
                tokens_gen = count_tokens(generated_text, tokenizer)

                # Get energy consumption
                emissions = tracker.finalize()
                # codecarbon finalizes on exit, but we need intermediate values
                # We'll store the final emissions after the context exits
                
                results.append({
                    'model_id': model_id,
                    'problem_id': problem_id,
                    'tokens_generated': tokens_gen,
                    'energy_kwh': None,  # Will be filled after tracker finalizes
                    'runtime_seconds': None  # Will be calculated after
                })

            end_time = time.time()
            total_runtime = end_time - start_time

            # Calculate runtime per problem (approximate)
            num_problems = len(results)
            if num_problems > 0:
                avg_runtime = total_runtime / num_problems
                for i, res in enumerate(results):
                    res['runtime_seconds'] = avg_runtime
                    # codecarbon tracks total energy for the context
                    # We'll use the final emissions value
                    res['energy_kwh'] = emissions
            else:
                logger.warning("No problems processed for model.")

    except Exception as e:
        logger.error(f"Error during inference for {model_id}: {e}")
        # Ensure we still write partial results if possible
        raise
    finally:
        # Unload model to free RAM
        unload_model(model, tokenizer)

    # Write results to CSV
    write_results_to_csv(results, output_file)
    logger.info(f"Wrote {len(results)} results to {output_file}")

    return results

def write_results_to_csv(results: List[Dict[str, Any]], filepath: str) -> None:
    """Write inference results to CSV file."""
    fieldnames = ['model_id', 'problem_id', 'tokens_generated', 'energy_kwh', 'runtime_seconds']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def run_inference_per_problem() -> None:
    """
    Main entry point to run inference for all models sequentially.
    Loads HumanEval data and processes each model one by one.
    """
    ensure_directories()
    
    # Load problems
    data_raw_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
    human_eval_path = os.path.join(data_raw_dir, 'human_eval_data.jsonl')
    
    if not os.path.exists(human_eval_path):
        raise FileNotFoundError(f"HumanEval data not found at {human_eval_path}. Run download.py first.")
    
    problems = load_problems_from_jsonl(human_eval_path)
    logger.info(f"Loaded {len(problems)} problems from HumanEval.")

    # Process models sequentially
    for model_id in MODEL_IDS:
        logger.info(f"Processing model: {model_id}")
        try:
            run_inference_for_model(model_id, problems)
            logger.info(f"Completed inference for {model_id}")
        except Exception as e:
            logger.error(f"Failed to process {model_id}: {e}")
            # Continue with next model
            continue

def main() -> None:
    """Main function to execute the inference pipeline."""
    run_inference_per_problem()

if __name__ == "__main__":
    main()
