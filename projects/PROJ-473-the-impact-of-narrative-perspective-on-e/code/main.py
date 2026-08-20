import os
import sys
import json
import glob
import logging
import argparse
from pathlib import Path

# Import analysis functions
from analysis import (
    run_regression_analysis,
    apply_bonferroni_correction,
    calculate_vif,
    generate_scatter_plot,
    run_analysis_pipeline,
    run_sensitivity_sweep
)
from data_loader import prepare_sensitivity_thresholds, save_thresholds_to_file
from data_collection import run_aggregation_pipeline
from extraction import extract_perspective_features
from matching import run_matching_pipeline
from config import get_config

# Setup logging
def setup_logging(log_file: str = "data/logs/pipeline.log"):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_extraction_step(args, logger):
    """Run the perspective feature extraction pipeline."""
    logger.info("Starting extraction step...")
    input_dir = args.input_dir or "data/raw/gutenberg_stories"
    output_path = args.output or "data/processed/perspective_features.json"
    
    # Ensure input directory exists
    if not os.path.exists(input_dir):
        logger.error(f"Input directory {input_dir} does not exist.")
        return False
    
    # Process all .txt files in the directory
    story_files = glob.glob(os.path.join(input_dir, "*.txt"))
    if not story_files:
        logger.warning(f"No .txt files found in {input_dir}. Skipping extraction.")
        return True
    
    results = []
    for file_path in story_files:
        try:
            feature = extract_perspective_features(file_path)
            if feature:
                results.append(feature)
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            continue
    
    # Write results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Extraction complete. Wrote {len(results)} records to {output_path}")
    return True

def run_matching_step(args, logger):
    """Run the text similarity matching pipeline."""
    logger.info("Starting matching step...")
    input_path = args.input or "data/processed/perspective_features.json"
    target_path = args.target or "data/raw/moral_judgement_external.csv"
    output_path = args.output or "data/processed/matching_results.json"
    thresholds_str = args.thresholds or "0.25,0.30,0.35,0.40"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} does not exist.")
        return False
    if not os.path.exists(target_path):
        logger.error(f"Target file {target_path} does not exist.")
        return False
    
    thresholds = [float(t) for t in thresholds_str.split(",")]
    
    # Run matching pipeline
    results = run_matching_pipeline(input_path, target_path, thresholds)
    
    # Write results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Matching complete. Wrote {len(results)} records to {output_path}")
    return True

def run_aggregation_step(args, logger):
    """Run the data aggregation pipeline."""
    logger.info("Starting aggregation step...")
    features_path = args.features or "data/processed/perspective_features.json"
    responses_path = args.responses or "data/processed/aligned_reader_response.csv"
    output_path = args.output or "data/processed/aligned_dataset.csv"
    
    if not os.path.exists(features_path):
        logger.error(f"Features file {features_path} does not exist.")
        return False
    if not os.path.exists(responses_path):
        logger.error(f"Responses file {responses_path} does not exist.")
        return False
    
    # Run aggregation
    success = run_aggregation_pipeline(features_path, responses_path, output_path)
    
    if success:
        logger.info(f"Aggregation complete. Wrote dataset to {output_path}")
    else:
        logger.error("Aggregation failed.")
    
    return success

def run_analysis_step(args, logger):
    """Run the full statistical analysis pipeline."""
    logger.info("Starting analysis step...")
    input_path = args.input or "data/processed/aligned_dataset.csv"
    output_path = args.output or "data/processed/analysis_results.json"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} does not exist.")
        return False
    
    # Run full analysis pipeline
    results = run_analysis_pipeline(input_path)
    
    if results is None:
        logger.error("Analysis pipeline failed to produce results.")
        return False
    
    # Write results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Wrote results to {output_path}")
    return True

def run_sensitivity_step(args, logger):
    """Run the sensitivity analysis pipeline."""
    logger.info("Starting sensitivity analysis step...")
    matching_path = args.matching or "data/processed/matching_results.json"
    thresholds_path = args.thresholds or "data/processed/thresholds.json"
    dataset_path = args.dataset or "data/processed/aligned_dataset.csv"
    output_path = args.output or "data/processed/sensitivity_report.json"
    
    if not os.path.exists(matching_path):
        logger.error(f"Matching results {matching_path} do not exist.")
        return False
    if not os.path.exists(thresholds_path):
        logger.error(f"Thresholds file {thresholds_path} does not exist.")
        return False
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset file {dataset_path} does not exist.")
        return False
    
    # Run sensitivity sweep
    results = run_sensitivity_sweep(matching_path, thresholds_path, dataset_path)
    
    if results is None:
        logger.error("Sensitivity sweep failed.")
        return False
    
    # Write results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Wrote report to {output_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Narrative Perspective Analysis Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Pipeline commands")

    # Extraction command
    extract_parser = subparsers.add_parser("extract", help="Run perspective extraction")
    extract_parser.add_argument("--input-dir", type=str, default="data/raw/gutenberg_stories")
    extract_parser.add_argument("--output", type=str, default="data/processed/perspective_features.json")

    # Matching command
    match_parser = subparsers.add_parser("match", help="Run text similarity matching")
    match_parser.add_argument("--input", type=str, default="data/processed/perspective_features.json")
    match_parser.add_argument("--target", type=str, default="data/raw/moral_judgement_external.csv")
    match_parser.add_argument("--output", type=str, default="data/processed/matching_results.json")
    match_parser.add_argument("--thresholds", type=str, default="0.25,0.30,0.35,0.40")

    # Aggregation command
    aggregate_parser = subparsers.add_parser("aggregate", help="Run data aggregation")
    aggregate_parser.add_argument("--features", type=str, default="data/processed/perspective_features.json")
    aggregate_parser.add_argument("--responses", type=str, default="data/processed/aligned_reader_response.csv")
    aggregate_parser.add_argument("--output", type=str, default="data/processed/aligned_dataset.csv")

    # Analysis command (T041)
    analyze_parser = subparsers.add_parser("analyze", help="Run full statistical analysis")
    analyze_parser.add_argument("--input", type=str, default="data/processed/aligned_dataset.csv")
    analyze_parser.add_argument("--output", type=str, default="data/processed/analysis_results.json")

    # Sensitivity command
    sensitivity_parser = subparsers.add_parser("sensitivity", help="Run sensitivity analysis")
    sensitivity_parser.add_argument("--matching", type=str, default="data/processed/matching_results.json")
    sensitivity_parser.add_argument("--thresholds", type=str, default="data/processed/thresholds.json")
    sensitivity_parser.add_argument("--dataset", type=str, default="data/processed/aligned_dataset.csv")
    sensitivity_parser.add_argument("--output", type=str, default="data/processed/sensitivity_report.json")

    # All command
    all_parser = subparsers.add_parser("all", help="Run full pipeline")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    logger = setup_logging()

    success = True
    if args.command == "extract":
        success = run_extraction_step(args, logger)
    elif args.command == "match":
        success = run_matching_step(args, logger)
    elif args.command == "aggregate":
        success = run_aggregation_step(args, logger)
    elif args.command == "analyze":
        success = run_analysis_step(args, logger)
    elif args.command == "sensitivity":
        success = run_sensitivity_step(args, logger)
    elif args.command == "all":
        # Run full pipeline in order
        # 1. Prepare thresholds
        prepare_sensitivity_thresholds()
        save_thresholds_to_file("data/processed/thresholds.json")
        
        # 2. Extract
        if not run_extraction_step(args, logger):
            success = False
        # 3. Match
        elif not run_matching_step(args, logger):
            success = False
        # 4. Aggregate
        elif not run_aggregation_step(args, logger):
            success = False
        # 5. Analyze
        elif not run_analysis_step(args, logger):
            success = False
        # 6. Sensitivity
        elif not run_sensitivity_step(args, logger):
            success = False
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
