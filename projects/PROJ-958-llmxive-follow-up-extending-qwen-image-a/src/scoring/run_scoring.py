"""
Script to process the full dataset (IA-Bench + WISE-Verified)
and write scoring results to data/derived/scoring_results.csv.

This script orchestrates the Syntactic Complexity Scoring pipeline for User Story 1.
It loads raw data, computes features, calculates normalized scores, and outputs
a consolidated CSV file.
"""

import os
import sys
import logging
import csv
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import (
    DATA_DERIVED_PATH,
    DATA_RAW_IA_BENCH_PATH,
    DATA_RAW_WISE_VERIFIED_PATH,
    SEED,
    LOG_LEVEL
)
from src.utils import setup_logger, get_domain_stratification
from src.utils.data_loader import load_ia_bench_references, load_wise_verified
from src.scoring.syntactic_features import (
    compute_syntactic_features,
    compute_lexical_features,
    handle_parse_failure
)
from src.scoring.complexity_calculator import (
    calculate_weighted_score,
    normalize_score
)

# Configure logging
logger = setup_logger(__name__, level=LOG_LEVEL)

def ensure_directories():
    """Ensure output directories exist."""
    os.makedirs(DATA_DERIVED_PATH, exist_ok=True)
    logger.info(f"Ensured directory exists: {DATA_DERIVED_PATH}")

def load_all_prompts():
    """
    Load prompts from both IA-Bench and WISE-Verified datasets.
    Returns a list of dictionaries with 'prompt_id', 'prompt_text', 'source', and optional metadata.
    """
    all_data = []

    # Load IA-Bench data (prompts + references)
    try:
        logger.info("Loading IA-Bench dataset...")
        ia_bench_data = load_ia_bench_references()
        for row in ia_bench_data:
            all_data.append({
                'prompt_id': row.get('id', 'unknown_ia'),
                'prompt_text': row.get('prompt', ''),
                'source': 'ia-bench',
                'reference_description': row.get('reference_description', None)
            })
        logger.info(f"Loaded {len(ia_bench_data)} prompts from IA-Bench.")
    except Exception as e:
        logger.error(f"Failed to load IA-Bench data: {e}")
        # Depending on strictness, we might exit here. 
        # For now, we continue with whatever data we have, but log the error.
        # In a strict "fail loudly" mode, we would raise e.

    # Load WISE-Verified data
    try:
        logger.info("Loading WISE-Verified dataset...")
        wise_data = load_wise_verified()
        for row in wise_data:
            all_data.append({
                'prompt_id': row.get('id', 'unknown_wise'),
                'prompt_text': row.get('prompt', ''),
                'source': 'wise-verified',
                'metadata': row.get('metadata', {})
            })
        logger.info(f"Loaded {len(wise_data)} prompts from WISE-Verified.")
    except Exception as e:
        logger.error(f"Failed to load WISE-Verified data: {e}")

    if not all_data:
        raise RuntimeError("No data loaded from any source. Cannot proceed with scoring.")
    
    return all_data

def process_dataset(prompts):
    """
    Process each prompt: compute features, calculate score, normalize.
    Returns a list of result dictionaries.
    """
    results = []
    total = len(prompts)
    success_count = 0
    failure_count = 0

    for idx, item in enumerate(prompts):
        prompt_id = item['prompt_id']
        prompt_text = item['prompt_text']
        source = item['source']

        logger.debug(f"Processing [{idx+1}/{total}]: {prompt_id} ({source})")

        # Handle empty or malformed prompts
        if not prompt_text or not isinstance(prompt_text, str) or not prompt_text.strip():
            logger.warning(f"Empty or malformed prompt detected for {prompt_id}. Assigning default score 0.0.")
            result = {
                'prompt_id': prompt_id,
                'source': source,
                'prompt_text': prompt_text,
                'syntactic_depth': 0.0,
                'clause_count': 0,
                'mtld': 0.0,
                'raw_score': 0.0,
                'normalized_score': 0.0,
                'status': 'failed_parse',
                'reference_description': item.get('reference_description', None)
            }
            results.append(result)
            failure_count += 1
            continue

        try:
            # 1. Compute Syntactic Features
            syntactic_features = compute_syntactic_features(prompt_text)
            if syntactic_features is None:
                # handle_parse_failure returns 0.0 for depth/clauses if parse fails
                syntactic_features = handle_parse_failure()
            
            syntactic_depth = syntactic_features.get('depth', 0.0)
            clause_count = syntactic_features.get('clause_count', 0)

            # 2. Compute Lexical Features
            lexical_features = compute_lexical_features(prompt_text)
            mtld = lexical_features.get('mtld', 0.0)

            # 3. Calculate Raw Weighted Score
            raw_score = calculate_weighted_score(
                syntactic_depth=syntactic_depth,
                clause_count=clause_count,
                mtld=mtld
            )

            # 4. Normalize to [0.0, 1.0]
            normalized_score = normalize_score(raw_score)

            result = {
                'prompt_id': prompt_id,
                'source': source,
                'prompt_text': prompt_text,
                'syntactic_depth': syntactic_depth,
                'clause_count': clause_count,
                'mtld': mtld,
                'raw_score': raw_score,
                'normalized_score': normalized_score,
                'status': 'success',
                'reference_description': item.get('reference_description', None)
            }
            results.append(result)
            success_count += 1

        except Exception as e:
            logger.error(f"Error processing {prompt_id}: {e}")
            # Fallback for unexpected errors
            result = {
                'prompt_id': prompt_id,
                'source': source,
                'prompt_text': prompt_text,
                'syntactic_depth': 0.0,
                'clause_count': 0,
                'mtld': 0.0,
                'raw_score': 0.0,
                'normalized_score': 0.0,
                'status': 'error',
                'reference_description': item.get('reference_description', None)
            }
            results.append(result)
            failure_count += 1

    logger.info(f"Processing complete. Success: {success_count}, Failed/Error: {failure_count}")
    return results

def write_results(results, output_path):
    """
    Write results to CSV file.
    """
    if not results:
        logger.warning("No results to write.")
        return

    fieldnames = [
        'prompt_id', 'source', 'prompt_text', 'syntactic_depth', 'clause_count',
        'mtld', 'raw_score', 'normalized_score', 'status', 'reference_description'
    ]

    logger.info(f"Writing {len(results)} results to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info("Successfully wrote scoring results.")

def main():
    logger.info("Starting Syntactic Complexity Scoring Pipeline (T015)...")
    logger.info(f"Random Seed: {SEED}")
    
    # Ensure output directory exists
    ensure_directories()

    # Define output path
    output_file = os.path.join(DATA_DERIVED_PATH, "scoring_results.csv")

    try:
        # 1. Load Data
        prompts = load_all_prompts()
        logger.info(f"Total prompts loaded: {len(prompts)}")

        # 2. Process Data
        results = process_dataset(prompts)

        # 3. Write Output
        write_results(results, output_file)

        logger.info("Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise e

if __name__ == "__main__":
    sys.exit(main())
