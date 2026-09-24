import os
import sys
import json
import logging
import time
import random
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils.logging import get_logger, log_prompt, log_raw_output
from src.utils.timeout_utils import run_with_api_timeout, TimeoutError
from src.execution.api_client import call_inference_api, InferenceError, MalformedResponseError

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "data" / "prompts"
CORPUS_PATH = PROJECT_ROOT / "data" / "processed" / "corpus.csv"
OUTPUT_BASE_DIR = PROJECT_ROOT / "data" / "evaluation" / "raw_translations"
TIMEOUT_SECONDS = 120
MAX_RETRIES = 3
DEFAULT_SEED = 42

logger = get_logger(__name__)


def load_prompts() -> Dict[str, str]:
    """
    Loads the four prompt condition files from data/prompts/.
    Returns a dictionary mapping condition_name -> prompt_text.
    """
    conditions = ["zero_shot_basic", "zero_shot_style", "few_shot_basic", "few_shot_style"]
    prompts = {}
    
    if not PROMPTS_DIR.exists():
        raise FileNotFoundError(f"Prompts directory not found: {PROMPTS_DIR}")

    for condition in conditions:
        file_path = PROMPTS_DIR / f"{condition}.txt"
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file missing: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            prompts[condition] = f.read()
    
    logger.info(f"Loaded {len(prompts)} prompt conditions.")
    return prompts


def load_corpus() -> List[Dict[str, Any]]:
    """
    Loads the processed corpus from data/processed/corpus.csv.
    Returns a list of dictionaries with 'python_code', 'javascript_code', 'id'.
    """
    if not CORPUS_PATH.exists():
        raise FileNotFoundError(f"Corpus file not found: {CORPUS_PATH}")

    corpus = []
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure we have the necessary fields
            if "python_code" in row and "id" in row:
                corpus.append({
                    "id": row["id"],
                    "python_code": row["python_code"],
                    "reference_js": row.get("javascript_code", "")
                })
    
    logger.info(f"Loaded {len(corpus)} entries from corpus.")
    return corpus


def prepare_prompt(prompt_template: str, python_code: str) -> str:
    """
    Prepares the final prompt by injecting the python code into the template.
    Assumes the template contains a placeholder like {python_code} or similar.
    If no placeholder is found, appends the code at the end.
    """
    # Simple injection strategy: look for common placeholders or append
    if "{python_code}" in prompt_template:
        return prompt_template.format(python_code=python_code)
    elif "<code>" in prompt_template:
        return prompt_template.replace("<code>", python_code)
    else:
        # Fallback: append code at the end with a separator
        return f"{prompt_template}\n\nPython Code:\n{python_code}"


def save_translation(condition: str, entry_id: str, output_path: Path, translation_data: Dict[str, Any]):
    """
    Saves the translation result to the appropriate condition directory.
    The translation_data includes raw output, seed, timestamp, etc.
    """
    condition_dir = OUTPUT_BASE_DIR / condition
    condition_dir.mkdir(parents=True, exist_ok=True)
    
    file_name = f"{entry_id}.json"
    file_path = condition_dir / file_name
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(translation_data, f, indent=2, ensure_ascii=False)
    
    logger.debug(f"Saved translation for {entry_id} ({condition}) to {file_path}")


def run_inference_for_entry(
    entry: Dict[str, Any],
    prompt_condition: str,
    prompt_text: str,
    seed: int
) -> Dict[str, Any]:
    """
    Executes the inference API call for a single entry under a specific prompt condition.
    Handles timeouts and retries.
    """
    entry_id = entry["id"]
    python_code = entry["python_code"]
    
    full_prompt = prepare_prompt(prompt_text, python_code)
    
    # Log the prompt for reproducibility
    log_prompt(
        logger, 
        prompt_condition=prompt_condition, 
        prompt_text=full_prompt, 
        seed=seed,
        entry_id=entry_id
    )

    result_data = {
        "entry_id": entry_id,
        "prompt_condition": prompt_condition,
        "seed": seed,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_code": python_code,
        "raw_output": "",
        "status": "pending",
        "error_message": ""
    }

    try:
        # Enforce timeout and call API
        response_text = run_with_api_timeout(
            call_inference_api, 
            args=(full_prompt,), 
            timeout=TIMEOUT_SECONDS,
            max_retries=MAX_RETRIES
        )
        
        result_data["raw_output"] = response_text
        result_data["status"] = "success"
        
        # Log the raw output
        log_raw_output(
            logger,
            output_text=response_text,
            prompt_condition=prompt_condition,
            entry_id=entry_id,
            seed=seed
        )

    except TimeoutError as te:
        result_data["status"] = "timeout"
        result_data["error_message"] = str(te)
        logger.warning(f"Timeout for {entry_id} ({prompt_condition}): {te}")
    except InferenceError as ie:
        result_data["status"] = "api_error"
        result_data["error_message"] = str(ie)
        logger.error(f"API Error for {entry_id} ({prompt_condition}): {ie}")
    except MalformedResponseError as mre:
        result_data["status"] = "malformed"
        result_data["error_message"] = str(mre)
        logger.error(f"Malformed response for {entry_id} ({prompt_condition}): {mre}")
    except Exception as e:
        result_data["status"] = "unknown_error"
        result_data["error_message"] = str(e)
        logger.exception(f"Unexpected error for {entry_id} ({prompt_condition}): {e}")

    return result_data


def main():
    """
    Main entry point for running inference on the corpus with all prompt conditions.
    """
    logger.info("Starting inference pipeline (T021).")
    
    # Ensure output directory exists
    OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)
    
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

    # Set random seed for reproducibility
    random.seed(DEFAULT_SEED)
    
    total_entries = len(corpus)
    total_conditions = len(prompts)
    total_iterations = total_entries * total_conditions
    
    logger.info(f"Processing {total_entries} entries across {total_conditions} conditions ({total_iterations} total requests).")

    processed_count = 0

    for condition_name, prompt_text in prompts.items():
        logger.info(f"--- Starting condition: {condition_name} ---")
        
        for entry in corpus:
            # Generate a deterministic seed for this entry+condition combination
            # This ensures reproducibility if the run is restarted
            seed = hash(f"{entry['id']}_{condition_name}_{DEFAULT_SEED}") & 0xFFFFFFFF
            
            result = run_inference_for_entry(
                entry=entry,
                prompt_condition=condition_name,
                prompt_text=prompt_text,
                seed=seed
            )
            
            # Save the result immediately
            save_translation(
                condition=condition_name,
                entry_id=entry["id"],
                output_path=OUTPUT_BASE_DIR,
                translation_data=result
            )
            
            processed_count += 1
            if processed_count % 10 == 0:
                logger.info(f"Progress: {processed_count}/{total_iterations}")

    logger.info(f"Inference pipeline completed. Processed {processed_count} requests.")
    logger.info(f"Results saved to: {OUTPUT_BASE_DIR}")


if __name__ == "__main__":
    main()