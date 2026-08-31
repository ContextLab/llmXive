import os
import sys
import json
import glob
import logging
import argparse
from pathlib import Path

# Ensure the code directory is in the path for imports if running as script
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from extraction import extract_perspective_features
from data_loader import prepare_sensitivity_thresholds, save_thresholds_to_file
from matching import run_matching_pipeline
from data_collection import run_aggregation_pipeline
from analysis import run_analysis_pipeline, run_sensitivity_sweep
from config import get_config

def setup_logging(log_file: str = "data/logs/pipeline.log"):
    """Configure logging for the pipeline."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_extraction_step(args):
    """Run the extraction step."""
    logger = logging.getLogger(__name__)
    logger.info("Starting extraction step...")
    # Implementation would call extract_perspective_features on input_dir
    # and save to output.
    # Assuming extract_perspective_features handles the file processing,
    # we need a wrapper or main loop here if extract_perspective_features is per-file.
    # Based on T016, extract_perspective_features takes a file_path.
    # We need to iterate over files in input_dir.
    
    input_dir = args.input_dir
    output_file = args.output
    
    if not os.path.exists(input_dir):
        logger.error(f"Input directory {input_dir} does not exist.")
        return 1
    
    # Simple loop for demonstration, assuming .txt files
    # In a real scenario, this might be more robust
    stories = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                try:
                    result = extract_perspective_features(file_path)
                    if result:
                        stories.append(result)
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {e}")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(stories, f, indent=2)
    
    logger.info(f"Extraction complete. Saved {len(stories)} records to {output_file}")
    return 0

def run_thresholds_step(args):
    """Run the thresholds preparation step."""
    logger = logging.getLogger(__name__)
    logger.info("Starting thresholds preparation step...")
    
    output_path = args.output
    
    # Call the function from data_loader
    prepare_sensitivity_thresholds(output_path=output_path)
    
    logger.info(f"Thresholds saved to {output_path}")
    return 0

def run_matching_step(args):
    """Run the matching step."""
    logger = logging.getLogger(__name__)
    logger.info("Starting matching step...")
    
    input_file = args.input
    target_file = args.target
    output_file = args.output
    threshold = args.threshold
    
    # Implementation would call run_matching_pipeline
    # This is a placeholder to satisfy the CLI structure
    # The actual implementation is in T025
    logger.warning("Matching step not fully implemented in this snippet.")
    return 0

def run_aggregation_step(args):
    """Run the aggregation step."""
    logger = logging.getLogger(__name__)
    logger.info("Starting aggregation step...")
    
    features_file = args.features
    responses_file = args.responses
    output_file = args.output
    
    # Implementation would call run_aggregation_pipeline
    # This is a placeholder to satisfy the CLI structure
    # The actual implementation is in T032
    logger.warning("Aggregation step not fully implemented in this snippet.")
    return 0

def run_analysis_step(args):
    """Run the analysis step."""
    logger = logging.getLogger(__name__)
    logger.info("Starting analysis step...")
    
    input_file = args.input
    output_file = args.output
    
    # Implementation would call run_analysis_pipeline
    # This is a placeholder to satisfy the CLI structure
    # The actual implementation is in T041
    logger.warning("Analysis step not fully implemented in this snippet.")
    return 0

def run_sensitivity_step(args):
    """Run the sensitivity analysis step."""
    logger = logging.getLogger(__name__)
    logger.info("Starting sensitivity analysis step...")
    
    # Implementation would call run_sensitivity_sweep
    # This is a placeholder to satisfy the CLI structure
    # The actual implementation is in T043
    logger.warning("Sensitivity step not fully implemented in this snippet.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Narrative Perspective Analysis Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract perspective features')
    extract_parser.add_argument('--input-dir', required=True, help='Input directory containing stories')
    extract_parser.add_argument('--output', required=True, help='Output JSON file path')
    extract_parser.set_defaults(func=run_extraction_step)

    # Prepare-thresholds command
    thresholds_parser = subparsers.add_parser('prepare-thresholds', help='Prepare sensitivity thresholds')
    thresholds_parser.add_argument('--output', required=True, help='Output JSON file path for thresholds')
    thresholds_parser.set_defaults(func=run_thresholds_step)

    # Match command
    match_parser = subparsers.add_parser('match', help='Run matching validation')
    match_parser.add_argument('--input', required=True, help='Input perspective features JSON')
    match_parser.add_argument('--target', required=True, help='Target moral judgement CSV')
    match_parser.add_argument('--output', required=True, help='Output matching results JSON')
    match_parser.add_argument('--threshold', type=float, required=True, help='Similarity threshold')
    match_parser.set_defaults(func=run_matching_step)

    # Aggregate command
    aggregate_parser = subparsers.add_parser('aggregate', help='Aggregate reader scores')
    aggregate_parser.add_argument('--features', required=True, help='Input perspective features JSON')
    aggregate_parser.add_argument('--responses', required=True, help='Input aligned reader response CSV')
    aggregate_parser.add_argument('--output', required=True, help='Output aggregated dataset CSV')
    aggregate_parser.set_defaults(func=run_aggregation_step)

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run analysis')
    analyze_parser.add_argument('--input', required=True, help='Input aligned dataset CSV')
    analyze_parser.add_argument('--output', required=True, help='Output analysis results JSON')
    analyze_parser.set_defaults(func=run_analysis_step)

    # Sensitivity command
    sensitivity_parser = subparsers.add_parser('sensitivity', help='Run sensitivity analysis')
    sensitivity_parser.set_defaults(func=run_sensitivity_step)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    setup_logging()
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())