import os
import sys
import json
import glob
import logging
import argparse
from pathlib import Path

# Ensure the code directory is in the path for imports when running as script
_code_root = Path(__file__).parent
if str(_code_root) not in sys.path:
    sys.path.insert(0, str(_code_root))

from config import get_config, PRIMARY_MATCHING_THRESHOLD
from extraction import extract_perspective_features
from matching import build_tfidf_vectors, find_top_matches, run_matching_pipeline
from data_loader import prepare_sensitivity_thresholds
from data_collection import aggregate_reader_scores
from analysis import run_regression_analysis, run_sensitivity_sweep, generate_scatter_plot
from utils import compute_artifact_hash, scan_for_pii

def setup_logging():
    """Configure logging to file and console."""
    os.makedirs("data/logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("data/logs/pipeline.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("pipeline")

def run_extraction_step(args):
    """Run the perspective extraction pipeline."""
    logger = setup_logging()
    logger.info(f"Starting extraction from {args.input_dir}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Run extraction
    results = extract_perspective_features(args.input_dir)
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Extraction complete. Results saved to {args.output}")
    return results

def run_matching_step(args):
    """Run the matching validation step.
    
    This implements T025: Match perspective features against a target moral judgement
    dataset using a specific threshold (defaulting to PRIMARY_MATCHING_THRESHOLD).
    """
    logger = setup_logging()
    logger.info(f"Starting matching: input={args.input}, target={args.target}")
    
    # Load perspective features
    with open(args.input, 'r') as f:
        perspective_features = json.load(f)
    
    # Load target moral judgement dataset
    import pandas as pd
    target_df = pd.read_csv(args.target)
    
    # Run matching pipeline
    # The matching logic expects texts from perspective_features and target texts from target_df
    # We need to align them based on story_id or content similarity
    
    # Prepare data for matching
    # perspective_features contains: story_id, raw_text, pronoun_density_1st, etc.
    # target_df contains: story_id, text, moral_judgement_score
    
    # We will match perspective features to target stories based on text similarity
    # using the TF-IDF approach defined in matching.py
    
    # Extract texts for vectorization
    source_texts = [item['raw_text'] for item in perspective_features]
    target_texts = target_df['text'].tolist()
    
    # Build TF-IDF vectors
    source_vectors, target_vectors = build_tfidf_vectors(
        source_texts, target_texts, exclude_pronouns=True
    )
    
    # Find matches for each source story
    threshold = args.threshold if args.threshold else PRIMARY_MATCHING_THRESHOLD
    logger.info(f"Using matching threshold: {threshold}")
    
    results = []
    for i, source_item in enumerate(perspective_features):
        query_vector = source_vectors[i]
        matches = find_top_matches(
            query_vector, 
            target_vectors, 
            k=3, 
            threshold=threshold
        )
        
        for rank, match in enumerate(matches, 1):
            results.append({
                'story_id': source_item['story_id'],
                'match_id': match['story_id'],
                'similarity_score': float(match['similarity']),
                'rank': rank,
                'threshold_used': threshold
            })
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Matching complete. {len(results)} matches saved to {args.output}")
    return results

def run_thresholds_step(args):
    """Prepare sensitivity thresholds."""
    logger = setup_logging()
    logger.info("Preparing sensitivity thresholds")
    
    thresholds_data = prepare_sensitivity_thresholds()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(thresholds_data, f, indent=2)
    
    logger.info(f"Thresholds saved to {args.output}")
    return thresholds_data

def run_aggregation_step(args):
    """Aggregate perspective features with reader responses."""
    logger = setup_logging()
    logger.info("Starting aggregation step")
    
    # Load inputs
    with open(args.features, 'r') as f:
        perspective_features = json.load(f)
    
    responses_df = pd.read_csv(args.responses)
    
    # Aggregate
    aggregated = aggregate_reader_scores(perspective_features, responses_df)
    
    # Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    aggregated.to_csv(args.output, index=False)
    
    logger.info(f"Aggregation complete. Results saved to {args.output}")
    return aggregated

def run_analysis_step(args):
    """Run full analysis pipeline."""
    logger = setup_logging()
    logger.info("Starting analysis step")
    
    # Load dataset
    dataset = pd.read_csv(args.input)
    
    # Run regression
    regression_results = run_regression_analysis(dataset)
    
    # Apply Bonferroni correction
    bonf_p = apply_bonferroni_correction([regression_results['p_value']])
    regression_results['bonferroni_adjusted_p'] = bonf_p[0]
    
    # Calculate VIF
    vif_warning = calculate_vif(dataset)
    regression_results['vif_warning'] = vif_warning
    
    # Generate plot
    generate_scatter_plot(args.input, args.output.replace('.json', '.png'))
    
    # Add sample size
    regression_results['sample_size'] = len(dataset)
    
    # Save results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(regression_results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {args.output}")
    return regression_results

def run_sensitivity_step(args):
    """Run sensitivity analysis sweep."""
    logger = setup_logging()
    logger.info("Starting sensitivity analysis")
    
    # Load inputs
    thresholds_data = json.load(open(args.thresholds))
    thresholds = thresholds_data['thresholds']
    
    dataset = pd.read_csv(args.dataset)
    
    # Run sweep
    results = run_sensitivity_sweep(
        matching_results_path=args.matching_results,
        thresholds_path=args.thresholds,
        dataset_path=args.dataset
    )
    
    # Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Results saved to {args.output}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Narrative Perspective Analysis Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extraction command
    extract_parser = subparsers.add_parser('extract', help='Extract perspective features')
    extract_parser.add_argument('--input-dir', required=True, help='Input directory with story files')
    extract_parser.add_argument('--output', required=True, help='Output JSON file path')
    
    # Matching command (T025)
    match_parser = subparsers.add_parser('match', help='Run matching validation')
    match_parser.add_argument('--input', required=True, help='Input perspective features JSON')
    match_parser.add_argument('--target', required=True, help='Target moral judgement CSV')
    match_parser.add_argument('--output', required=True, help='Output matching results JSON')
    match_parser.add_argument('--threshold', type=float, default=None, help='Matching threshold (default: 0.30)')
    
    # Thresholds command
    thresh_parser = subparsers.add_parser('prepare-thresholds', help='Prepare sensitivity thresholds')
    thresh_parser.add_argument('--output', required=True, help='Output thresholds JSON file')
    
    # Aggregation command
    agg_parser = subparsers.add_parser('aggregate', help='Aggregate data')
    agg_parser.add_argument('--features', required=True, help='Perspective features JSON')
    agg_parser.add_argument('--responses', required=True, help='Reader responses CSV')
    agg_parser.add_argument('--output', required=True, help='Output aggregated CSV')
    
    # Analysis command
    analysis_parser = subparsers.add_parser('analyze', help='Run analysis')
    analysis_parser.add_argument('--input', required=True, help='Input dataset CSV')
    analysis_parser.add_argument('--output', required=True, help='Output analysis results JSON')
    
    # Sensitivity command
    sens_parser = subparsers.add_parser('sensitivity', help='Run sensitivity analysis')
    sens_parser.add_argument('--matching-results', required=True, help='Matching results JSON')
    sens_parser.add_argument('--thresholds', required=True, help='Thresholds JSON')
    sens_parser.add_argument('--dataset', required=True, help='Aligned dataset CSV')
    sens_parser.add_argument('--output', required=True, help='Output sensitivity report JSON')
    
    # All command
    all_parser = subparsers.add_parser('all', help='Run full pipeline')
    all_parser.add_argument('--config', default='code/config.py', help='Config file path')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        run_extraction_step(args)
    elif args.command == 'match':
        run_matching_step(args)
    elif args.command == 'prepare-thresholds':
        run_thresholds_step(args)
    elif args.command == 'aggregate':
        run_aggregation_step(args)
    elif args.command == 'analyze':
        run_analysis_step(args)
    elif args.command == 'sensitivity':
        run_sensitivity_step(args)
    elif args.command == 'all':
        setup_logging()
        # Run full pipeline
        # Step 1: Extract (if needed)
        # Step 2: Prepare thresholds
        # Step 3: Match
        # Step 4: Aggregate
        # Step 5: Analyze
        # Step 6: Sensitivity
        logging.info("Full pipeline execution not fully implemented yet.")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
