import os
import json
import glob
import logging
import argparse
import sys
from pathlib import Path

# Import project modules using the public API surface
from extraction import extract_perspective_features
from data_loader import fetch_gutenberg_stories
from matching import run_sensitivity_analysis_pipeline
from data_collection import run_aggregation_pipeline
from analysis import run_analysis_pipeline
from config import get_config
from utils import compute_artifact_hash

# Configure logging
def setup_logging(log_file: str = "data/logs/extraction.log") -> logging.Logger:
    """Setup logging to both file and console."""
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates in re-runs
    logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def run_extraction_step(input_dir: str, output_path: str, logger: logging.Logger) -> bool:
    """
    Run the perspective feature extraction pipeline.
    
    Args:
        input_dir: Directory containing story text files (.txt)
        output_path: Path to save the JSON output
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting extraction on corpus: {input_dir}")
    
    if not os.path.isdir(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        return False
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    results = []
    skipped_count = 0
    processed_count = 0
    
    # Find all .txt files
    story_files = glob.glob(os.path.join(input_dir, "*.txt"))
    
    if not story_files:
        logger.warning(f"No .txt files found in {input_dir}")
        # Write empty list if no files
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return True
    
    for file_path in story_files:
        try:
            result = extract_perspective_features(file_path)
            if result is None:
                skipped_count += 1
                continue
            
            results.append(result)
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            continue
    
    # Write results to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Extraction complete. Processed: {processed_count}, Skipped: {skipped_count}")
    logger.info(f"Output written to: {output_path}")
    
    return True

def run_matching_step(input_path: str, target_path: str, output_path: str, logger: logging.Logger) -> bool:
    """
    Run the text similarity matching step.
    
    Args:
        input_path: Path to perspective features JSON
        target_path: Path to target moral judgement dataset CSV
        output_path: Path to save matching results JSON
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Starting matching step")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file does not exist: {input_path}")
        return False
        
    if not os.path.exists(target_path):
        logger.error(f"Target file does not exist: {target_path}")
        return False
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Run matching logic
        results = run_sensitivity_analysis_pipeline(input_path, target_path, output_path, logger)
        logger.info(f"Matching complete. Results saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Matching failed: {str(e)}")
        return False

def run_aggregation_step(features_path: str, responses_path: str, output_path: str, logger: logging.Logger) -> bool:
    """
    Run the data aggregation step.
    
    Args:
        features_path: Path to perspective features JSON
        responses_path: Path to aligned reader response CSV
        output_path: Path to save aggregated dataset CSV
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Starting aggregation step")
    
    if not os.path.exists(features_path):
        logger.error(f"Features file does not exist: {features_path}")
        return False
        
    if not os.path.exists(responses_path):
        logger.error(f"Responses file does not exist: {responses_path}")
        return False
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        run_aggregation_pipeline(features_path, responses_path, output_path, logger)
        logger.info(f"Aggregation complete. Output saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Aggregation failed: {str(e)}")
        return False

def run_analysis_step(input_path: str, output_path: str, logger: logging.Logger) -> bool:
    """
    Run the statistical analysis step.
    
    Args:
        input_path: Path to aligned dataset CSV
        output_path: Path to save analysis results JSON
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Starting analysis step")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file does not exist: {input_path}")
        return False
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        results = run_analysis_pipeline(input_path, output_path, logger)
        logger.info(f"Analysis complete. Results saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return False

def run_all_pipeline(logger: logging.Logger) -> bool:
    """
    Run the entire pipeline end-to-end.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if all steps successful, False otherwise
    """
    logger.info("Starting full pipeline")
    
    config = get_config()
    
    # Step 1: Fetch data (if needed) - assumed already done by T007
    gutenberg_dir = config.get('GUTENBERG_STORIES_DIR', 'data/raw/gutenberg_stories')
    
    # Step 2: Extraction
    features_output = config.get('FEATURES_OUTPUT', 'data/processed/perspective_features.json')
    if not run_extraction_step(gutenberg_dir, features_output, logger):
        logger.error("Extraction step failed")
        return False
    
    # Step 3: Matching
    # Check if target data exists, if not, skip or generate mock
    target_path = config.get('MORAL_JUDGEMENT_DATASET', 'data/raw/moral_judgement_dataset.csv')
    matching_output = config.get('MATCHING_OUTPUT', 'data/processed/matching_results.json')
    
    if os.path.exists(target_path):
        if not run_matching_step(features_output, target_path, matching_output, logger):
            logger.error("Matching step failed")
            return False
    else:
        logger.warning(f"Target dataset not found at {target_path}. Skipping matching step.")
    
    # Step 4: Aggregation
    responses_path = config.get('READER_RESPONSE_PATH', 'data/processed/aligned_reader_response.csv')
    aggregated_output = config.get('AGGREGATED_OUTPUT', 'data/processed/aligned_dataset.csv')
    
    if os.path.exists(responses_path):
        if not run_aggregation_step(features_output, responses_path, aggregated_output, logger):
            logger.error("Aggregation step failed")
            return False
    else:
        logger.warning(f"Reader response data not found at {responses_path}. Skipping aggregation step.")
    
    # Step 5: Analysis
    analysis_output = config.get('ANALYSIS_OUTPUT', 'data/processed/analysis_results.json')
    if os.path.exists(aggregated_output):
        if not run_analysis_step(aggregated_output, analysis_output, logger):
            logger.error("Analysis step failed")
            return False
    else:
        logger.warning(f"Aggregated dataset not found at {aggregated_output}. Skipping analysis step.")
    
    logger.info("Full pipeline completed successfully")
    return True

def main():
    """Main entry point for the pipeline CLI."""
    parser = argparse.ArgumentParser(description="Narrative Perspective Analysis Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Run perspective feature extraction')
    extract_parser.add_argument('--input-dir', required=True, help='Directory containing story .txt files')
    extract_parser.add_argument('--output', required=True, help='Output JSON file path')
    
    # Match command
    match_parser = subparsers.add_parser('match', help='Run text similarity matching')
    match_parser.add_argument('--input', required=True, help='Input perspective features JSON')
    match_parser.add_argument('--target', required=True, help='Target moral judgement dataset CSV')
    match_parser.add_argument('--output', required=True, help='Output matching results JSON')
    
    # Aggregate command
    aggregate_parser = subparsers.add_parser('aggregate', help='Run data aggregation')
    aggregate_parser.add_argument('--features', required=True, help='Input perspective features JSON')
    aggregate_parser.add_argument('--responses', required=True, help='Input aligned reader response CSV')
    aggregate_parser.add_argument('--output', required=True, help='Output aggregated dataset CSV')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run statistical analysis')
    analyze_parser.add_argument('--input', required=True, help='Input aligned dataset CSV')
    analyze_parser.add_argument('--output', required=True, help='Output analysis results JSON')
    
    # All command
    all_parser = subparsers.add_parser('all', help='Run the entire pipeline')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    logger = setup_logging()
    
    success = False
    
    if args.command == 'extract':
        success = run_extraction_step(args.input_dir, args.output, logger)
    elif args.command == 'match':
        success = run_matching_step(args.input, args.target, args.output, logger)
    elif args.command == 'aggregate':
        success = run_aggregation_step(args.features, args.responses, args.output, logger)
    elif args.command == 'analyze':
        success = run_analysis_step(args.input, args.output, logger)
    elif args.command == 'all':
        success = run_all_pipeline(logger)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()