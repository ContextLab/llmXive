import os
import json
import glob
import logging
import argparse
import sys

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import get_config
from extraction import extract_perspective_features, DataQualityError
from matching import build_tfidf_vectors, find_top_matches, apply_sensitivity_analysis
from data_collection import validate_and_clean_responses, aggregate_reader_scores, run_aggregation_pipeline
from analysis import run_regression_analysis, apply_bonferroni_correction, calculate_vif, run_analysis_pipeline
from data_loader import fetch_gutenberg_stories, load_reader_response_data, fetch_all_datasets
from utils import scan_for_pii, compute_artifact_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_extraction_step(args):
    """Run the perspective feature extraction pipeline."""
    logger.info(f"Starting extraction from {args.input_dir}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    stories = []
    # Fetch real data if raw directory is empty or doesn't exist
    if not os.path.exists(args.input_dir) or not os.listdir(args.input_dir):
        logger.info("Raw data directory empty or missing. Fetching Gutenberg stories...")
        os.makedirs(args.input_dir, exist_ok=True)
        fetch_gutenberg_stories(args.input_dir)
    
    # Process all text files in input directory
    for file_path in glob.glob(os.path.join(args.input_dir, "*.txt")):
        try:
            feature_record = extract_perspective_features(file_path)
            stories.append(feature_record)
        except DataQualityError as e:
            logger.warning(f"Skipping {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    # Write output JSON
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(stories, f, indent=2)
    
    logger.info(f"Extraction complete. Wrote {len(stories)} records to {args.output}")
    return 0

def run_matching_step(args):
    """Run the text similarity matching validation."""
    logger.info(f"Starting matching with input {args.input} and target {args.target}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Load perspective features
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    with open(args.input, 'r', encoding='utf-8') as f:
        perspective_features = json.load(f)
    
    # Load target dataset (moral judgement)
    if not os.path.exists(args.target):
        raise FileNotFoundError(f"Target file not found: {args.target}")
    
    # Perform matching
    results = run_sensitivity_analysis_pipeline(perspective_features, args.target)
    
    # Write output JSON
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Matching complete. Wrote results to {args.output}")
    return 0

def run_data_collection_step(args):
    """Run the data collection pipeline (fetches real proxy data)."""
    logger.info("Starting data collection...")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Fetch real proxy data (fallback mode as per spec)
    reader_data = load_reader_response_data()
    
    if reader_data is None or len(reader_data) == 0:
        raise RuntimeError("Failed to fetch real reader response data from verified source.")
    
    # Save to CSV
    reader_data.to_csv(args.output, index=False)
    logger.info(f"Data collection complete. Wrote {len(reader_data)} records to {args.output}")
    return 0

def run_aggregation_step(args):
    """Run the aggregation pipeline to align features with responses."""
    logger.info(f"Starting aggregation with features {args.features} and responses {args.responses}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Load inputs
    if not os.path.exists(args.features):
        raise FileNotFoundError(f"Features file not found: {args.features}")
    if not os.path.exists(args.responses):
        raise FileNotFoundError(f"Responses file not found: {args.responses}")
    
    # Run aggregation
    aligned_df = run_aggregation_pipeline(args.features, args.responses)
    
    # Write output CSV
    aligned_df.to_csv(args.output, index=False)
    logger.info(f"Aggregation complete. Wrote {len(aligned_df)} records to {args.output}")
    return 0

def run_analysis_step(args):
    """Run the full statistical analysis and output results JSON."""
    logger.info(f"Starting analysis on {args.input}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    # Run the full analysis pipeline
    results = run_analysis_pipeline(args.input)
    
    # Write output JSON
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Wrote results to {args.output}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Narrative Perspective Analysis Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Run perspective feature extraction')
    extract_parser.add_argument('--input-dir', required=True, help='Directory containing raw story text files')
    extract_parser.add_argument('--output', required=True, help='Output JSON file path')
    extract_parser.set_defaults(func=run_extraction_step)
    
    # Match command
    match_parser = subparsers.add_parser('match', help='Run text similarity matching')
    match_parser.add_argument('--input', required=True, help='Input JSON with perspective features')
    match_parser.add_argument('--target', required=True, help='Target CSV with moral judgement data')
    match_parser.add_argument('--output', required=True, help='Output JSON with matching results')
    match_parser.set_defaults(func=run_matching_step)
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Run data collection (fetch proxy data)')
    collect_parser.add_argument('--output', required=True, help='Output CSV file path')
    collect_parser.set_defaults(func=run_data_collection_step)
    
    # Aggregate command
    aggregate_parser = subparsers.add_parser('aggregate', help='Run aggregation pipeline')
    aggregate_parser.add_argument('--features', required=True, help='Input JSON with perspective features')
    aggregate_parser.add_argument('--responses', required=True, help='Input CSV with reader responses')
    aggregate_parser.add_argument('--output', required=True, help='Output CSV with aligned dataset')
    aggregate_parser.set_defaults(func=run_aggregation_step)
    
    # Analyze command (T041)
    analyze_parser = subparsers.add_parser('analyze', help='Run full statistical analysis')
    analyze_parser.add_argument('--input', required=True, help='Input CSV with aligned dataset')
    analyze_parser.add_argument('--output', required=True, help='Output JSON with analysis results')
    analyze_parser.set_defaults(func=run_analysis_step)
    
    # All command
    all_parser = subparsers.add_parser('all', help='Run full pipeline end-to-end')
    all_parser.set_defaults(func=lambda args: run_all_pipeline())
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    return args.func(args)

def run_all_pipeline():
    """Run the full pipeline end-to-end."""
    logger.info("Starting full pipeline...")
    
    # 1. Extract
    run_extraction_step(argparse.Namespace(input_dir='data/raw', output='data/processed/perspective_features.json'))
    
    # 2. Match
    run_matching_step(argparse.Namespace(
        input='data/processed/perspective_features.json',
        target='data/raw/moral_judgement_dataset.csv',
        output='data/processed/matching_results.json'
    ))
    
    # 3. Collect
    run_data_collection_step(argparse.Namespace(output='data/processed/reader_response.csv'))
    
    # 4. Aggregate
    run_aggregation_step(argparse.Namespace(
        features='data/processed/perspective_features.json',
        responses='data/processed/reader_response.csv',
        output='data/processed/aligned_dataset.csv'
    ))
    
    # 5. Analyze
    run_analysis_step(argparse.Namespace(
        input='data/processed/aligned_dataset.csv',
        output='data/processed/analysis_results.json'
    ))
    
    logger.info("Full pipeline complete.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
