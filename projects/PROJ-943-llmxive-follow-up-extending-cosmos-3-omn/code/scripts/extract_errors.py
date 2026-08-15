import json
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger, log_script_start, log_script_end

logger = get_logger(__name__)

INPUT_PATH = Path("code/data/results/raw_predictions.jsonl")
OUTPUT_PATH = Path("code/data/processed/misclassified_samples.jsonl")
MAX_MEMORY_MB = 7000  # 7 GB limit for safety, though this script is lightweight

def load_predictions(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load predictions from a JSONL file.
    Expects each line to be a JSON object containing 'true_label' and 'predicted_label'.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T017 (evaluate.py) has run successfully.")
    
    predictions = []
    logger.info(f"Loading predictions from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                predictions.append(record)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON on line {line_num}: {e}")
                raise
    
    logger.info(f"Loaded {len(predictions)} prediction records.")
    return predictions

def extract_misclassified(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter the list of predictions to keep only those where 
    predicted_label != true_label.
    """
    misclassified = []
    for record in predictions:
        # Robust check: ensure keys exist
        true_label = record.get('true_label')
        predicted_label = record.get('predicted_label')
        
        if true_label is None or predicted_label is None:
            logger.warning(f"Skipping record due to missing labels: {record.get('id', 'unknown')}")
            continue
        
        if true_label != predicted_label:
            misclassified.append(record)
    
    logger.info(f"Identified {len(misclassified)} misclassified samples out of {len(predictions)}.")
    return misclassified

def save_misclassified(misclassified: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the misclassified samples to a JSONL file.
    Ensures the output directory exists.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving {len(misclassified)} misclassified samples to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in misclassified:
            f.write(json.dumps(record) + '\n')
    
    logger.info("Successfully saved misclassified samples.")

def main():
    log_script_start(logger, "extract_errors")
    
    try:
        # 1. Load raw predictions
        predictions = load_predictions(INPUT_PATH)
        
        if not predictions:
            logger.warning("No predictions found in input file. Exiting.")
            return

        # 2. Extract misclassified samples
        misclassified = extract_misclassified(predictions)
        
        if not misclassified:
            logger.warning("No misclassified samples found. Output file will be empty.")
        
        # 3. Save results
        save_misclassified(misclassified, OUTPUT_PATH)
        
        log_script_end(logger, "extract_errors", success=True)
        
    except FileNotFoundError as e:
        logger.error(f"Critical file error: {e}")
        log_script_end(logger, "extract_errors", success=False)
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during execution: {e}")
        log_script_end(logger, "extract_errors", success=False)
        sys.exit(1)

if __name__ == "__main__":
    main()
