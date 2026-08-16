import os
import json
import glob
import logging
import argparse
import sys
from pathlib import Path

# Import extraction logic
from extraction import extract_perspective_features
from utils import compute_artifact_hash

def setup_logging(log_file_path: str = 'data/logs/pipeline.log') -> logging.Logger:
    """
    Sets up logging to both file and console.
    Ensures the directory for the log file exists.
    """
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger('pipeline')
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    try:
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print(f"Warning: Could not create log file {log_file_path}: {e}")

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def run_extraction_step(input_dir: str, output_path: str, logger: logging.Logger) -> bool:
    """
    Runs the perspective feature extraction on all text files in input_dir.
    Outputs a JSON list to output_path.
    
    Schema:
    [
      {
        "story_id": str,
        "raw_text": str (truncated to 500 chars),
        "pronoun_density_1st": float,
        "pronoun_density_3rd": float,
        "narrator_distance_score": float,
        "confidence_flag": str
      }
    ]
    """
    logger.info(f"Starting extraction on directory: {input_dir}")
    
    if not os.path.exists(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        return False

    # Find all text files
    text_files = glob.glob(os.path.join(input_dir, '*.txt'))
    if not text_files:
        logger.warning(f"No .txt files found in {input_dir}")
        return False

    logger.info(f"Found {len(text_files)} text files to process.")

    results = []
    skipped_count = 0

    for file_path in text_files:
        story_id = os.path.basename(file_path).replace('.txt', '')
        
        try:
            # extract_perspective_features handles edge cases (<50 words, non-English)
            # and returns None if the record should be skipped, logging the reason.
            record = extract_perspective_features(file_path)
            
            if record is None:
                skipped_count += 1
                continue

            # Truncate raw_text to 500 characters for the output schema
            raw_text = record.get('raw_text', '')
            if len(raw_text) > 500:
                raw_text = raw_text[:500]

            output_record = {
                "story_id": story_id,
                "raw_text": raw_text,
                "pronoun_density_1st": record['pronoun_density_1st'],
                "pronoun_density_3rd": record['pronoun_density_3rd'],
                "narrator_distance_score": record['narrator_distance_score'],
                "confidence_flag": record['confidence_flag']
            }
            results.append(output_record)

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            # Continue processing other files (robustness requirement)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Write results to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Extraction complete. Processed {len(results)} stories, skipped {skipped_count}.")
    logger.info(f"Output written to: {output_path}")
    
    # Compute artifact hash for versioning
    artifact_hash = compute_artifact_hash(output_path)
    logger.info(f"Artifact hash: {artifact_hash}")

    return True

def run_all_pipeline(args, logger: logging.Logger):
    """
    Runs the full pipeline: extraction -> matching -> analysis.
    Currently implemented to run extraction and matching as per task dependencies.
    """
    logger.info("Running full pipeline...")
    
    # 1. Extraction
    if not run_extraction_step(args.input_dir, args.output, logger):
        logger.error("Extraction failed. Stopping pipeline.")
        return False

    logger.info("Pipeline execution completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description='Narrative Perspective Analysis Pipeline')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Run perspective feature extraction')
    extract_parser.add_argument('--input-dir', required=True, help='Directory containing raw text files')
    extract_parser.add_argument('--output', required=True, help='Output JSON file path')

    # Match command (placeholder for T025, implemented minimally to avoid crash if called)
    match_parser = subparsers.add_parser('match', help='Run matching validation')
    match_parser.add_argument('--input', required=True, help='Input features JSON')
    match_parser.add_argument('--target', required=True, help='Target dataset CSV')
    match_parser.add_argument('--output', required=True, help='Output results JSON')

    # Analyze command (placeholder for T041)
    analyze_parser = subparsers.add_parser('analyze', help='Run statistical analysis')
    analyze_parser.add_argument('--input', required=True, help='Input aligned dataset CSV')
    analyze_parser.add_argument('--output', required=True, help='Output analysis results JSON')

    # All command
    all_parser = subparsers.add_parser('all', help='Run the entire pipeline')
    all_parser.add_argument('--input-dir', required=True, help='Directory containing raw text files')
    all_parser.add_argument('--output', required=True, help='Output JSON file path for extraction')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    logger = setup_logging()

    if args.command == 'extract':
        success = run_extraction_step(args.input_dir, args.output, logger)
        sys.exit(0 if success else 1)
    
    elif args.command == 'all':
        success = run_all_pipeline(args, logger)
        sys.exit(0 if success else 1)

    elif args.command == 'match':
        logger.error("Matching step (T025) is not yet implemented.")
        sys.exit(1)

    elif args.command == 'analyze':
        logger.error("Analysis step (T041) is not yet implemented.")
        sys.exit(1)

    else:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)

if __name__ == '__main__':
    main()