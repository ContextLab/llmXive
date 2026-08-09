import os
import json
import glob
import logging
from pathlib import Path
from extraction import extract_perspective_features
from matching import run_sensitivity_analysis_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for the research pipeline.
    Supports sub-commands:
      1. extract: Run perspective feature extraction (default behavior).
      2. match: Run matching validation and output matching_results.json.
    """
    import sys

    # Determine sub-command
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = "extract"

    if command == "extract":
        _run_extraction()
    elif command == "match":
        _run_matching_validation()
    else:
        logger.error(f"Unknown command: {command}. Use 'extract' or 'match'.")
        sys.exit(1)

def _run_extraction():
    """
    Run extraction on the data/raw/ corpus.
    Outputs JSON records to data/processed/perspective_features.json.
    """
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    output_file = processed_dir / "perspective_features.json"

    if not raw_dir.exists():
        logger.error(f"Raw data directory {raw_dir} does not exist.")
        return

    processed_dir.mkdir(parents=True, exist_ok=True)

    # Find all text files
    text_files = list(raw_dir.glob("*.txt"))
    if not text_files:
        logger.warning(f"No .txt files found in {raw_dir}.")
        return

    logger.info(f"Found {len(text_files)} files to process.")
    
    results = []
    for file_path in text_files:
        logger.info(f"Processing {file_path}...")
        try:
            features = extract_perspective_features(str(file_path))
            if features:
                results.append(features)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    logger.info(f"Processed {len(results)} files successfully.")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {output_file}")

def _run_matching_validation():
    """
    Run matching validation pipeline.
    Reads perspective features from data/processed/perspective_features.json
    and outputs matching results to data/processed/matching_results.json.
    """
    input_file = Path("data/processed/perspective_features.json")
    output_file = Path("data/processed/matching_results.json")
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} does not exist. Run extraction first.")
        return

    logger.info(f"Loading perspective features from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        stories = json.load(f)

    if not stories:
        logger.warning("No stories found in input file. Skipping matching.")
        return

    logger.info(f"Running matching validation on {len(stories)} stories...")
    
    # Execute the sensitivity analysis pipeline which includes matching logic
    results = run_sensitivity_analysis_pipeline(stories)
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing matching results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Matching validation complete. Results written to {output_file}")

if __name__ == "__main__":
    main()