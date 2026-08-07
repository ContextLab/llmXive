"""
T017b: Apply failure_classifier.py to baseline results.

This script loads the baseline execution results from
data/intermediate/baseline_run.jsonl, applies the failure classification
logic from analysis.failure_classifier, and writes the annotated results
to data/intermediate/baseline_run_classified.jsonl.

It enforces the 'fail loudly' principle: if the input file does not exist
or is empty, it raises an error rather than generating synthetic data.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to ensure imports work when run as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.failure_classifier import classify_failure, FailureCategory, process_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_PATH = project_root / "data" / "intermediate" / "baseline_run.jsonl"
OUTPUT_PATH = project_root / "data" / "intermediate" / "baseline_run_classified.jsonl"

def load_results(input_path: Path) -> List[Dict[str, Any]]:
    """Load results from a JSONL file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    results = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                results.append(record)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num} in {input_path}: {e}")

    if not results:
        raise ValueError(f"Input file {input_path} is empty or contains no valid records.")

    return results

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save annotated results to a JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in results:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

def main():
    logger.info(f"Starting failure classification for {INPUT_PATH}")
    
    try:
        # Load baseline results
        baseline_results = load_results(INPUT_PATH)
        logger.info(f"Loaded {len(baseline_results)} records from {INPUT_PATH}")

        # Apply classification using the existing process_results function
        # process_results expects a list of records and returns a list of records with 'failure_category' added
        classified_results = process_results(baseline_results)

        # Verify that classification was applied
        classified_count = sum(
            1 for r in classified_results 
            if 'failure_category' in r and r['failure_category'] != FailureCategory.NONE
        )
        logger.info(f"Classified {classified_count}/{len(classified_results)} records as failures.")

        # Save results
        save_results(classified_results, OUTPUT_PATH)
        logger.info(f"Successfully wrote classified results to {OUTPUT_PATH}")

    except Exception as e:
        logger.error(f"Error during failure classification: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()