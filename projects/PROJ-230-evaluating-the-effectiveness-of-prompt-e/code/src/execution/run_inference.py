import os
import sys
import json
import logging
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Local imports based on provided API surface
from src.execution.api_client import call_inference_api, InferenceError, MalformedResponseError
from src.utils.logging import get_logger, log_prompt, log_raw_output
from src.utils.timeout_utils import run_with_api_timeout, TimeoutError as ApiTimeoutError
from src.ingestion.validate_corpus_size import validate_corpus_size

# Constants
PROMPT_CONDITIONS = [
    "zero_shot_basic",
    "zero_shot_style",
    "few_shot_basic",
    "few_shot_style"
]

PROMPT_FILES = {
    "zero_shot_basic": "zero_shot_basic.txt",
    "zero_shot_style": "zero_shot_style.txt",
    "few_shot_basic": "few_shot_basic.txt",
    "few_shot_style": "few_shot_style.txt"
}

# Configuration paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_DIR = DATA_DIR / "prompts"
PROCESSED_CORPUS_PATH = DATA_DIR / "processed" / "corpus.csv"
EVALUATION_DIR = DATA_DIR / "evaluation"
RAW_TRANSLATIONS_DIR = EVALUATION_DIR / "raw_translations"

logger = get_logger(__name__)

def load_prompts() -> Dict[str, str]:
    """Load prompt templates from files."""
    prompts = {}
    for condition, filename in PROMPT_FILES.items():
        prompt_path = PROMPTS_DIR / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompts[condition] = f.read()
    return prompts

def load_corpus() -> pd.DataFrame:
    """Load the preprocessed corpus."""
    if not PROCESSED_CORPUS_PATH.exists():
        raise FileNotFoundError(f"Corpus file not found: {PROCESSED_CORPUS_PATH}")
    df = pd.read_csv(PROCESSED_CORPUS_PATH)
    logger.info(f"Loaded corpus with {len(df)} entries from {PROCESSED_CORPUS_PATH}")
    return df

def prepare_prompt(prompt_template: str, python_code: str) -> str:
    """Inject code into the prompt template."""
    return prompt_template.replace("{python_code}", python_code)

def save_translation(condition: str, index: int, python_code: str, js_output: str, seed: int, prompt_text: str, status: str = "success"):
    """Save a single translation result to a JSON file."""
    condition_dir = RAW_TRANSLATIONS_DIR / condition
    condition_dir.mkdir(parents=True, exist_ok=True)
    
    output_filename = f"translation_{index:04d}.json"
    output_path = condition_dir / output_filename
    
    record = {
        "index": index,
        "seed": seed,
        "condition": condition,
        "python_code": python_code,
        "javascript_code": js_output,
        "prompt_text": prompt_text,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    
    logger.debug(f"Saved translation to {output_path}")

def run_inference_for_entry(
    entry: Dict[str, Any], 
    condition: str, 
    prompt_template: str,
    seed: int,
    timeout_seconds: int = 120
) -> Dict[str, Any]:
    """Run inference for a single corpus entry under a specific condition."""
    python_code = entry.get("python_code", "")
    if not python_code:
        logger.warning(f"Skipping entry {entry.get('id', 'unknown')}: missing python_code")
        return {"status": "skipped", "reason": "missing_code"}

    # Prepare prompt
    prompt_text = prepare_prompt(prompt_template, python_code)
    
    # Log prompt for reproducibility
    log_prompt(
        logger=logger,
        condition=condition,
        seed=seed,
        prompt=prompt_text
    )

    try:
        # Run with timeout enforcement
        response = run_with_api_timeout(
            call_inference_api,
            timeout_seconds=timeout_seconds,
            prompt=prompt_text,
            seed=seed
        )
        
        js_output = response.get("generated_text", "")
        
        # Log raw output
        log_raw_output(
            logger=logger,
            condition=condition,
            seed=seed,
            output=js_output
        )

        # Check for failure indicators
        if "I cannot" in js_output or "sorry" in js_output.lower():
            save_translation(condition, entry.get('id', 0), python_code, js_output, seed, prompt_text, status="failed_content")
            logger.info(f"Entry {entry.get('id', 'unknown')} failed content check (non-code output)")
            return {"status": "failed_content", "output": js_output}

        save_translation(condition, entry.get('id', 0), python_code, js_output, seed, prompt_text, status="success")
        return {"status": "success", "output": js_output}

    except ApiTimeoutError:
        logger.error(f"Timeout for entry {entry.get('id', 'unknown')} in condition {condition}")
        save_translation(condition, entry.get('id', 0), python_code, "", seed, prompt_text, status="timeout")
        return {"status": "timeout", "output": ""}
    except InferenceError as e:
        logger.error(f"Inference error for entry {entry.get('id', 'unknown')}: {str(e)}")
        save_translation(condition, entry.get('id', 0), python_code, "", seed, prompt_text, status="inference_error")
        return {"status": "inference_error", "output": ""}
    except MalformedResponseError as e:
        logger.error(f"Malformed response for entry {entry.get('id', 'unknown')}: {str(e)}")
        save_translation(condition, entry.get('id', 0), python_code, "", seed, prompt_text, status="malformed_response")
        return {"status": "malformed_response", "output": ""}
    except Exception as e:
        logger.exception(f"Unexpected error for entry {entry.get('id', 'unknown')}: {str(e)}")
        save_translation(condition, entry.get('id', 0), python_code, "", seed, prompt_text, status="unexpected_error")
        return {"status": "unexpected_error", "output": ""}

def main():
    """Main entry point for running inference across all conditions and corpus."""
    logger.info("Starting run_inference.py")
    
    # Ensure output directory exists
    RAW_TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load prompts
    try:
        prompts = load_prompts()
        logger.info(f"Loaded {len(prompts)} prompt conditions")
    except FileNotFoundError as e:
        logger.error(f"Failed to load prompts: {e}")
        sys.exit(1)

    # Load corpus
    try:
        corpus = load_corpus()
        if len(corpus) < 200:
            logger.warning(f"Corpus size {len(corpus)} is below expected threshold of 200")
    except FileNotFoundError as e:
        logger.error(f"Failed to load corpus: {e}")
        sys.exit(1)

    # Determine seed
    seed = int(os.environ.get("INFERENCE_SEED", "42"))
    random.seed(seed)
    logger.info(f"Using random seed: {seed}")

    # Iterate through conditions
    for condition in PROMPT_CONDITIONS:
        logger.info(f"Processing condition: {condition}")
        prompt_template = prompts.get(condition)
        if not prompt_template:
            logger.warning(f"No prompt template found for {condition}, skipping")
            continue

        # Process each entry in the corpus
        for idx, row in corpus.iterrows():
            entry = row.to_dict()
            # Inject a deterministic seed per entry per condition for reproducibility
            entry_seed = seed + idx + hash(condition) % 10000 
            
            result = run_inference_for_entry(
                entry=entry,
                condition=condition,
                prompt_template=prompt_template,
                seed=entry_seed,
                timeout_seconds=120
            )
            
            # Log summary
            if result["status"] == "success":
                logger.debug(f"Entry {entry.get('id', idx)}: Success")
            else:
                logger.info(f"Entry {entry.get('id', idx)}: {result['status']}")

    logger.info("run_inference.py completed successfully")

if __name__ == "__main__":
    main()