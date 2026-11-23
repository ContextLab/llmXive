import os
import sys
import json
import logging
import time
import random
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from project API surface
from src.execution.api_client import call_inference_api, InferenceError, MalformedResponseError
from src.execution.determinism_utils import set_deterministic_seed, log_determinism_metadata
from src.utils.logging import get_logger, log_raw_output
from src.execution.save_translations import ensure_output_dirs, save_translation

# Constants
PROMPT_DIR = Path("data/prompts")
CORPUS_PATH = Path("data/processed/corpus.csv")
OUTPUT_BASE_DIR = Path("data/evaluation/raw_translations")
MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"
DEFAULT_SEED = 42
MAX_RETRIES = 3

logger = get_logger(__name__)

def load_prompts() -> Dict[str, str]:
    """
    Load the four prompt condition files from data/prompts/.
    Returns a dictionary mapping condition name to prompt text.
    """
    conditions = ["zero_shot_basic", "zero_shot_style", "few_shot_basic", "few_shot_style"]
    prompts = {}
    
    if not PROMPT_DIR.exists():
        raise FileNotFoundError(f"Prompt directory {PROMPT_DIR} does not exist.")
    
    for condition in conditions:
        prompt_file = PROMPT_DIR / f"{condition}.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file {prompt_file} does not exist.")
        
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompts[condition] = f.read()
    
    logger.info(f"Loaded {len(prompts)} prompt conditions.")
    return prompts

def load_corpus() -> List[Dict[str, Any]]:
    """
    Load the preprocessed corpus from data/processed/corpus.csv.
    Returns a list of dictionaries with 'id', 'python_code', 'javascript_code'.
    """
    if not CORPUS_PATH.exists():
        raise FileNotFoundError(f"Corpus file {CORPUS_PATH} does not exist.")
    
    corpus = []
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        # Assuming CSV with headers: id,python_code,javascript_code
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('python_code') and row.get('id'):
                corpus.append({
                    "id": row['id'],
                    "python_code": row['python_code'],
                    "javascript_code": row.get('javascript_code', '') # Ground truth if available
                })
    
    logger.info(f"Loaded {len(corpus)} entries from corpus.")
    return corpus

def prepare_prompt(prompt_template: str, python_code: str) -> str:
    """
    Prepare the final prompt by injecting the Python code into the template.
    """
    # The template is expected to contain a placeholder or structure for the code.
    # For this implementation, we assume the prompt text is the instruction
    # and we append the code, or the prompt file contains the full structure.
    # Based on standard practices, we'll assume the prompt file contains the
    # instruction and we need to append the code if not already in the file.
    # However, T010 specified "complete prompt text". Let's assume the file
    # contains the full prompt including the placeholder or the instruction
    # to translate the following code.
    #
    # Strategy: If the prompt ends with a newline or specific token, append code.
    # To be safe and robust, we will simply append the code to the prompt text
    # if the prompt doesn't already seem to contain the code (which it shouldn't).
    # A more robust way is to have a specific placeholder like {code} in the prompt.
    # Given the task description "apply the four prompt conditions", we assume
    # the condition defines the *instruction* and we append the source code.
    
    if "{code}" in prompt_template:
        return prompt_template.format(code=python_code)
    else:
        # Fallback: append code if not present
        # Check if code is already in prompt (unlikely for a template)
        if python_code.strip() not in prompt_template:
            return f"{prompt_template}\n\nSource Python Code:\n{python_code}"
        return prompt_template

def run_inference_for_entry(
    entry: Dict[str, Any],
    condition: str,
    prompt_text: str,
    seed: int
) -> Dict[str, Any]:
    """
    Run inference for a single corpus entry under a specific prompt condition.
    Returns a result dictionary with status, output, and metadata.
    """
    set_deterministic_seed(seed)
    full_prompt = prepare_prompt(prompt_text, entry['python_code'])
    
    result = {
        "input_id": entry['id'],
        "condition": condition,
        "seed": seed,
        "status": "pending",
        "output": None,
        "error": None,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    try:
        # Call the API client with timeout and retry logic
        response = call_inference_api(
            model=MODEL_NAME,
            prompt=full_prompt,
            seed=seed,
            max_retries=MAX_RETRIES
        )
        
        result["output"] = response
        result["status"] = "success"
        logger.info(f"Success for {entry['id']} [{condition}].")
        
    except (InferenceError, MalformedResponseError) as e:
        result["status"] = "failed"
        result["error"] = str(e)
        logger.warning(f"Failed for {entry['id']} [{condition}]: {e}")
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Unexpected error: {str(e)}"
        logger.error(f"Unexpected error for {entry['id']} [{condition}]: {e}", exc_info=True)
    
    return result

def main():
    """
    Main entry point for running inference across the corpus and all prompt conditions.
    """
    logger.info("Starting inference run.")
    
    # 1. Load Prompts
    prompts = load_prompts()
    
    # 2. Load Corpus
    corpus = load_corpus()
    
    if not corpus:
        logger.error("Corpus is empty. Cannot proceed.")
        sys.exit(1)
    
    # 3. Ensure output directories exist
    ensure_output_dirs(OUTPUT_BASE_DIR)
    
    # 4. Iterate and Execute
    # We will run all conditions for all entries.
    # For reproducibility, we log the exact seed used for each run.
    
    total_runs = len(corpus) * len(prompts)
    current_run = 0
    
    for entry in corpus:
        for condition, prompt_text in prompts.items():
            current_run += 1
            logger.info(f"Running {current_run}/{total_runs}: {entry['id']} [{condition}]")
            
            # Generate a deterministic seed for this specific run
            # Based on entry id hash + condition hash + base seed
            base_seed = DEFAULT_SEED
            run_seed = hash(entry['id'] + condition + str(base_seed)) % (2**31 - 1)
            
            result = run_inference_for_entry(
                entry=entry,
                condition=condition,
                prompt_text=prompt_text,
                seed=run_seed
            )
            
            # Save the translation/output
            save_translation(
                output_dir=OUTPUT_BASE_DIR,
                condition=condition,
                input_id=entry['id'],
                result=result
            )
            
            # Log raw output for reproducibility (T022 requirement)
            log_raw_output(
                logger=logger,
                prompt=prompt_text,
                output=result.get('output'),
                seed=run_seed,
                condition=condition,
                input_id=entry['id']
            )
    
    logger.info("Inference run completed.")

if __name__ == "__main__":
    main()