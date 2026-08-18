import os
import sys
import json
import glob
import logging
import argparse
from datetime import datetime

# Import from sibling modules based on provided API surface
from config import get_config
from data_loader import fetch_gutenberg_stories, fetch_external_moral_dataset, prepare_sensitivity_thresholds
from extraction import extract_perspective_features
from matching import run_matching_pipeline, run_sensitivity_analysis_pipeline
from data_collection import run_aggregation_pipeline
from analysis import run_analysis_pipeline, run_sensitivity_sweep

def setup_logging(log_file='data/logs/pipeline.log'):
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
    """Run the perspective feature extraction pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("Starting extraction step...")
    input_dir = args.input_dir or 'data/raw/gutenberg_stories'
    output_file = args.output or 'data/processed/perspective_features.json'
    
    # Ensure input directory exists (fetch if needed)
    if not os.path.exists(input_dir):
        logger.warning(f"Input directory {input_dir} not found. Attempting to fetch Gutenberg stories...")
        fetch_gutenberg_stories('data/raw/gutenberg_stories')
    
    # Run extraction
    results = extract_perspective_features(input_dir, output_file)
    logger.info(f"Extraction complete. Results saved to {output_file}")
    return results

def run_matching_step(args):
    """Run the text similarity matching pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("Starting matching step...")
    input_file = args.input or 'data/processed/perspective_features.json'
    target_file = args.target or 'data/raw/moral_judgement_dataset.csv'
    output_file = args.output or 'data/processed/matching_results.json'
    
    # Ensure target data exists
    if not os.path.exists(target_file):
        logger.warning(f"Target file {target_file} not found. Fetching external moral dataset...")
        fetch_external_moral_dataset(target_file)
    
    results = run_matching_pipeline(input_file, target_file, output_file)
    logger.info(f"Matching complete. Results saved to {output_file}")
    return results

def run_aggregation_step(args):
    """Run the data aggregation pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("Starting aggregation step...")
    features_file = args.features or 'data/processed/perspective_features.json'
    responses_file = args.responses or 'data/processed/aligned_reader_response.csv'
    output_file = args.output or 'data/processed/aligned_dataset.csv'
    
    results = run_aggregation_pipeline(features_file, responses_file, output_file)
    logger.info(f"Aggregation complete. Results saved to {output_file}")
    return results

def run_analysis_step(args):
    """Run the full statistical analysis pipeline (T041)."""
    logger = logging.getLogger(__name__)
    logger.info("Starting analysis step...")
    input_file = args.input or 'data/processed/aligned_dataset.csv'
    output_file = args.output or 'data/processed/analysis_results.json'
    
    # Ensure input data exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found. Please run aggregation step first.")
    
    # Run analysis pipeline which returns the full results dict
    results = run_analysis_pipeline(input_file, output_file)
    
    # Ensure the output file is written
    if not os.path.exists(output_file):
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {output_file}")
    return results

def run_sensitivity_step(args):
    """Run the sensitivity analysis pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("Starting sensitivity step...")
    matching_file = args.matching or 'data/processed/matching_results.json'
    thresholds_file = args.thresholds or 'data/processed/thresholds.json'
    dataset_file = args.dataset or 'data/processed/aligned_dataset.csv'
    output_file = args.output or 'data/processed/sensitivity_report.json'
    
    results = run_sensitivity_sweep(matching_file, thresholds_file, dataset_file, output_file)
    logger.info(f"Sensitivity analysis complete. Results saved to {output_file}")
    return results

def main():
    parser = argparse.ArgumentParser(description='Narrative Perspective Analysis Pipeline')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Extraction command
    extract_parser = subparsers.add_parser('extract', help='Run perspective feature extraction')
    extract_parser.add_argument('--input-dir', type=str, help='Input directory for stories')
    extract_parser.add_argument('--output', type=str, help='Output JSON file for features')

    # Matching command
    match_parser = subparsers.add_parser('match', help='Run text similarity matching')
    match_parser.add_argument('--input', type=str, help='Input features JSON file')
    match_parser.add_argument('--target', type=str, help='Target moral judgement dataset CSV')
    match_parser.add_argument('--output', type=str, help='Output matching results JSON')

    # Aggregation command
    agg_parser = subparsers.add_parser('aggregate', help='Run data aggregation')
    agg_parser.add_argument('--features', type=str, help='Input features JSON file')
    agg_parser.add_argument('--responses', type=str, help='Input reader response CSV file')
    agg_parser.add_argument('--output', type=str, help='Output aligned dataset CSV')

    # Analysis command (T041)
    analyze_parser = subparsers.add_parser('analyze', help='Run full statistical analysis')
    analyze_parser.add_argument('--input', type=str, help='Input aligned dataset CSV')
    analyze_parser.add_argument('--output', type=str, help='Output analysis results JSON')

    # Sensitivity command
    sens_parser = subparsers.add_parser('sensitivity', help='Run sensitivity analysis')
    sens_parser.add_argument('--matching', type=str, help='Input matching results JSON')
    sens_parser.add_argument('--thresholds', type=str, help='Input thresholds JSON')
    sens_parser.add_argument('--dataset', type=str, help='Input aligned dataset CSV')
    sens_parser.add_argument('--output', type=str, help='Output sensitivity report JSON')

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging()
    logger.info(f"Pipeline started at {datetime.now()}")
    logger.info(f"Command: {args.command}")

    if args.command == 'extract':
        run_extraction_step(args)
    elif args.command == 'match':
        run_matching_step(args)
    elif args.command == 'aggregate':
        run_aggregation_step(args)
    elif args.command == 'analyze':
        run_analysis_step(args)
    elif args.command == 'sensitivity':
        run_sensitivity_step(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
