"""
Main entry point for the narrative perspective analysis pipeline.
Handles CLI commands for extraction, matching, aggregation, and analysis.
"""
import os
import sys
import json
import glob
import logging
import argparse
import hashlib

from extraction import extract_perspective_features
from matching import run_matching_pipeline
from data_collection import run_aggregation_pipeline
from analysis import run_analysis_pipeline, run_sensitivity_sweep
from config import get_config

# Ensure log directory exists
os.makedirs('data/logs', exist_ok=True)

def setup_logging():
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_extraction_step(args):
    """Run the perspective extraction pipeline."""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting extraction on {args.input_dir}")
    
    if not os.path.exists(args.input_dir):
        logger.error(f"Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    try:
        extract_perspective_features(args.input_dir, args.output)
        logger.info(f"Extraction complete. Output written to {args.output}")
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        sys.exit(1)

def run_thresholds_step(args):
    """Generate threshold values for sensitivity analysis."""
    logger = logging.getLogger(__name__)
    thresholds = [0.25, 0.30, 0.35, 0.40]
    output_data = {"thresholds": thresholds}
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Thresholds written to {args.output}")

def run_matching_step(args):
    """Run the matching pipeline."""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting matching with threshold {args.threshold}")
    
    try:
        run_matching_pipeline(
            features_path=args.input,
            target_path=args.target,
            output_path=args.output,
            threshold=args.threshold
        )
        logger.info(f"Matching complete. Output written to {args.output}")
    except Exception as e:
        logger.error(f"Matching failed: {str(e)}")
        sys.exit(1)

def run_aggregation_step(args):
    """Run the aggregation pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("Starting aggregation")
    
    try:
        run_aggregation_pipeline(
            features_path=args.features,
            responses_path=args.responses,
            output_path=args.output
        )
        logger.info(f"Aggregation complete. Output written to {args.output}")
    except Exception as e:
        logger.error(f"Aggregation failed: {str(e)}")
        sys.exit(1)

def run_analysis_step(args):
    """Run the full analysis pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("Starting analysis")
    
    try:
        run_analysis_pipeline(
            dataset_path=args.input,
            output_path=args.output
        )
        logger.info(f"Analysis complete. Output written to {args.output}")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

def run_sensitivity_step(args):
    """Run the sensitivity analysis pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("Starting sensitivity analysis")
    
    try:
        run_sensitivity_sweep(
            stories_dir=args.stories_dir,
            target_csv=args.target_csv,
            thresholds_json=args.thresholds_json,
            perspective_json=args.perspective_json,
            output_path=args.output
        )
        logger.info(f"Sensitivity analysis complete. Output written to {args.output}")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {str(e)}")
        sys.exit(1)

def run_plot_step(args):
    """Generate the regression plot."""
    logger = logging.getLogger(__name__)
    logger.info(f"Generating plot from {args.input}")
    
    try:
        # Import here to avoid circular imports if analysis.py has issues
        from analysis import generate_scatter_plot
        generate_scatter_plot(args.input, args.output)
        logger.info(f"Plot saved to {args.output}")
    except Exception as e:
        logger.error(f"Plot generation failed: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Narrative Perspective Analysis Pipeline')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract perspective features')
    extract_parser.add_argument('--input-dir', required=True, help='Directory containing story text files')
    extract_parser.add_argument('--output', required=True, help='Output JSON file path')
    extract_parser.set_defaults(func=run_extraction_step)

    # Thresholds command
    thresholds_parser = subparsers.add_parser('prepare-thresholds', help='Generate threshold values')
    thresholds_parser.add_argument('--output', required=True, help='Output JSON file path')
    thresholds_parser.set_defaults(func=run_thresholds_step)

    # Match command
    match_parser = subparsers.add_parser('match', help='Run matching pipeline')
    match_parser.add_argument('--input', required=True, help='Input perspective features JSON')
    match_parser.add_argument('--target', required=True, help='Target moral judgement CSV')
    match_parser.add_argument('--output', required=True, help='Output matching results JSON')
    match_parser.add_argument('--threshold', type=float, default=0.30, help='Similarity threshold')
    match_parser.set_defaults(func=run_matching_step)

    # Aggregate command
    aggregate_parser = subparsers.add_parser('aggregate', help='Aggregate reader responses')
    aggregate_parser.add_argument('--features', required=True, help='Perspective features JSON')
    aggregate_parser.add_argument('--responses', required=True, help='Aligned reader responses CSV')
    aggregate_parser.add_argument('--output', required=True, help='Output aligned dataset CSV')
    aggregate_parser.set_defaults(func=run_aggregation_step)

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run full analysis')
    analyze_parser.add_argument('--input', required=True, help='Input aligned dataset CSV')
    analyze_parser.add_argument('--output', required=True, help='Output analysis results JSON')
    analyze_parser.set_defaults(func=run_analysis_step)

    # Plot command
    plot_parser = subparsers.add_parser('plot', help='Generate regression plot')
    plot_parser.add_argument('--input', required=True, help='Input aligned dataset CSV')
    plot_parser.add_argument('--output', required=True, help='Output PNG file path')
    plot_parser.set_defaults(func=run_plot_step)

    # Sensitivity command
    sensitivity_parser = subparsers.add_parser('sensitivity', help='Run sensitivity analysis')
    sensitivity_parser.add_argument('--stories-dir', required=True, help='Directory containing raw stories')
    sensitivity_parser.add_argument('--target-csv', required=True, help='Target moral judgement CSV')
    sensitivity_parser.add_argument('--thresholds-json', required=True, help='Thresholds JSON file')
    sensitivity_parser.add_argument('--perspective-json', required=True, help='Perspective features JSON')
    sensitivity_parser.add_argument('--output', required=True, help='Output sensitivity report JSON')
    sensitivity_parser.set_defaults(func=run_sensitivity_step)

    # All command (runs full pipeline)
    all_parser = subparsers.add_parser('all', help='Run full pipeline')
    all_parser.add_argument('--stories-dir', default='data/raw/gutenberg_stories', help='Stories directory')
    all_parser.add_argument('--target-csv', default='data/raw/moral_judgement_local.csv', help='Target CSV')
    all_parser.add_argument('--thresholds-json', default='data/processed/thresholds.json', help='Thresholds file')
    all_parser.add_argument('--perspective-json', default='data/processed/perspective_features.json', help='Perspective features file')
    all_parser.add_argument('--aligned-dataset', default='data/processed/aligned_dataset.csv', help='Aligned dataset file')
    all_parser.set_defaults(func=lambda args: run_full_pipeline(args))

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    setup_logging()
    
    if args.command == 'all':
        run_full_pipeline(args)
    else:
        args.func(args)

def run_full_pipeline(args):
    """Run the complete pipeline from raw data to final analysis."""
    logger = logging.getLogger(__name__)
    logger.info("Starting full pipeline execution")
    
    try:
        # 1. Extract features
        logger.info("Step 1: Extracting perspective features")
        extract_perspective_features(args.stories_dir, args.perspective_json)
        
        # 2. Prepare thresholds
        logger.info("Step 2: Preparing thresholds")
        thresholds = [0.25, 0.30, 0.35, 0.40]
        with open(args.thresholds_json, 'w') as f:
            json.dump({"thresholds": thresholds}, f)
        
        # 3. Run matching
        logger.info("Step 3: Running matching")
        run_matching_pipeline(
            features_path=args.perspective_json,
            target_path=args.target_csv,
            output_path='data/processed/matching_results.json',
            threshold=0.30
        )
        
        # 4. Aggregate data
        logger.info("Step 4: Aggregating data")
        # Note: This assumes aligned_reader_response.csv exists from T009.6d
        # If not, we might need to generate it or handle the missing file
        if not os.path.exists('data/processed/aligned_reader_response.csv'):
            logger.warning("aligned_reader_response.csv not found. Skipping aggregation.")
        else:
            run_aggregation_pipeline(
                features_path=args.perspective_json,
                responses_path='data/processed/aligned_reader_response.csv',
                output_path=args.aligned_dataset
            )
        
        # 5. Run analysis
        logger.info("Step 5: Running analysis")
        if os.path.exists(args.aligned_dataset):
            run_analysis_pipeline(
                dataset_path=args.aligned_dataset,
                output_path='data/processed/analysis_results.json'
            )
            
            # 6. Generate plot
            logger.info("Step 6: Generating plot")
            from analysis import generate_scatter_plot
            generate_scatter_plot(args.aligned_dataset, 'data/artifacts/regression_plot.png')
        
        # 7. Sensitivity analysis
        logger.info("Step 7: Running sensitivity analysis")
        run_sensitivity_sweep(
            stories_dir=args.stories_dir,
            target_csv=args.target_csv,
            thresholds_json=args.thresholds_json,
            perspective_json=args.perspective_json,
            output_path='data/processed/sensitivity_report.json'
        )
        
        logger.info("Full pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()