"""
Run Inference for Code Translation
Iterates through the processed corpus and applies four prompt conditions.
"""
import os
import sys
import json
import logging
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports based on API surface
from src.execution.api_client import call_inference_api, InferenceError, MalformedResponseError
from src.utils.logging import get_logger, log_prompt, log_raw_output
from src.utils.timeout_utils import run_with_api_timeout, TimeoutError as ApiTimeoutError

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_DIR = DATA_DIR / "prompts"
PROCESSED_CORPUS = DATA_DIR / "processed" / "corpus.csv"
EVALUATION_DIR = DATA_DIR / "evaluation"
RAW_TRANSLATIONS_DIR = EVALUATION_DIR / "raw_translations"
LOGS_DIR = EVALUATION_DIR / "logs"

# Prompt conditions defined in T010
PROMPT_CONDITIONS = [
    "zero_shot_basic",
    "zero_shot_style",
    "few_shot_basic",
    "few_shot_style"
]

# Model configuration
MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"
DEFAULT_SEED = 42
MAX_NEW_TOKENS = 512
TEMPERATURE = 0.2

logger = get_logger(__name__)


def load_prompts() -> Dict[str, str]:
    """
    Load the four prompt conditions from data/prompts/.
    Returns a dict mapping condition name -> prompt template string.
    """
    prompts = {}
    if not PROMPTS_DIR.exists():
        raise FileNotFoundError(f"Prompts directory not found: {PROMPTS_DIR}")

    for condition in PROMPT_CONDITIONS:
        prompt_file = PROMPTS_DIR / f"{condition}.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file missing: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompts[condition] = f.read()
    
    logger.info(f"Loaded {len(prompts)} prompt conditions.")
    return prompts


def load_corpus() -> List[Dict[str, Any]]:
    """
    Load the processed corpus from data/processed/corpus.csv.
    Returns a list of dicts with 'python_code' and 'javascript_code' keys.
    """
    if not PROCESSED_CORPUS.exists():
        raise FileNotFoundError(f"Corpus file not found: {PROCESSED_CORPUS}")
    
    corpus = []
    import csv
    with open(PROCESSED_CORPUS, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure required columns exist
            if 'python_code' in row and 'javascript_code' in row:
                corpus.append({
                    'id': row.get('id', ''),
                    'python_code': row['python_code'],
                    'javascript_code': row['javascript_code'] # Reference for evaluation, not used in generation
                })
    
    logger.info(f"Loaded {len(corpus)} entries from corpus.")
    return corpus


def prepare_prompt(prompt_template: str, python_code: str) -> str:
    """
    Inject the Python code into the prompt template.
    Assumes the template contains a placeholder like {python_code} or similar.
    If no placeholder is found, appends the code.
    """
    if "{python_code}" in prompt_template:
        return prompt_template.format(python_code=python_code)
    elif "{{python_code}}" in prompt_template:
        return prompt_template.format(python_code=python_code)
    else:
        # Fallback: append if no placeholder detected
        return f"{prompt_template}\n\n{python_code}"


def save_translation(condition: str, entry_id: str, python_code: str, raw_output: str, seed: int):
    """
    Save the translation result to data/evaluation/raw_translations/{condition}/
    as a JSON file.
    """
    output_dir = RAW_TRANSLATIONS_DIR / condition
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    safe_id = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in str(entry_id))
    filename = f"{safe_id}_{seed}.json"
    filepath = output_dir / filename
    
    data = {
        "id": entry_id,
        "condition": condition,
        "seed": seed,
        "python_code": python_code,
        "raw_output": raw_output,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Also log to the central logger for audit
    log_raw_output(
        logger=logger,
        prompt_condition=condition,
        seed=seed,
        raw_output=raw_output,
        input_source=entry_id
    )


def run_inference_for_entry(
    entry: Dict[str, Any],
    prompt_template: str,
    condition: str,
    seed: int
) -> Optional[str]:
    """
    Run a single inference request for one entry and one condition.
    Returns the raw output string or None if failed.
    """
    full_prompt = prepare_prompt(prompt_template, entry['python_code'])
    
    try:
        # Enforce timeout as per T009/T020 constraints
        response_text = run_with_api_timeout(
            call_inference_api,
            model=MODEL_NAME,
            prompt=full_prompt,
            max_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            seed=seed,
            timeout_seconds=120
        )
        
        # Log the prompt for reproducibility
        log_prompt(
            logger=logger,
            condition=condition,
            seed=seed,
            prompt=full_prompt
        )
        
        return response_text

    except ApiTimeoutError as e:
        logger.error(f"Timeout for {condition} on entry {entry['id']}: {e}")
        return None
    except InferenceError as e:
        logger.error(f"Inference error for {condition} on entry {entry['id']}: {e}")
        return None
    except MalformedResponseError as e:
        logger.error(f"Malformed response for {condition} on entry {entry['id']}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error for {condition} on entry {entry['id']}: {e}")
        return None


def main():
    """
    Main entry point for running inference across all conditions and corpus.
    """
    logger.info("Starting Inference Pipeline (T021)")
    
    # Ensure output directories exist
    RAW_TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load prompts
    try:
        prompts = load_prompts()
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # Load corpus
    try:
        corpus = load_corpus()
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    if not corpus:
        logger.warning("Corpus is empty. Nothing to process.")
        return

    # Set global seed for reproducibility
    random.seed(DEFAULT_SEED)
    
    total_entries = len(corpus)
    total_conditions = len(PROMPT_CONDITIONS)
    total_iterations = total_entries * total_conditions
    
    logger.info(f"Processing {total_entries} entries x {total_conditions} conditions = {total_iterations} tasks.")
    
    processed_count = 0
    failed_count = 0

    for condition in PROMPT_CONDITIONS:
        logger.info(f"--- Processing Condition: {condition} ---")
        prompt_template = prompts[condition]
        
        for entry in corpus:
            entry_id = entry['id']
            # Use a deterministic seed based on entry id and condition index
            # to ensure reproducibility across runs
            entry_seed = DEFAULT_SEED + hash(f"{entry_id}_{condition}") % 10000
            
            logger.info(f"Running: {condition} | ID: {entry_id} | Seed: {entry_seed}")
            
            result = run_inference_for_entry(
                entry=entry,
                prompt_template=prompt_template,
                condition=condition,
                seed=entry_seed
            )
            
            if result is not None:
                save_translation(
                    condition=condition,
                    entry_id=entry_id,
                    python_code=entry['python_code'],
                    raw_output=result,
                    seed=entry_seed
                )
                processed_count += 1
            else:
                failed_count += 1
                # Log failed translation as per T024 requirement
                logger.warning(f"Translation failed for {condition} | ID: {entry_id}")

    logger.info(f"Inference Pipeline Complete. Success: {processed_count}, Failed: {failed_count}")
    logger.info(f"Outputs saved to: {RAW_TRANSLATIONS_DIR}")


if __name__ == "__main__":
    main()
