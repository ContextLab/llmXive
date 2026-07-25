import argparse
import json
import logging
import os
import sys
from pathlib import Path

from evaluate import setup_logging, load_features, load_model, calculate_metrics, calculate_baseline_mae, perform_permutation_test, evaluate_model, save_results

def parse_args():
    parser = argparse.ArgumentParser(description="Write evaluation results to JSON.")
    parser.add_argument("--features_path", type=str, default="data/processed/features.json",
                        help="Path to the features JSON file.")
    parser.add_argument("--model_path", type=str, default="results/model.pkl",
                        help="Path to the trained model pickle file.")
    parser.add_argument("--output_path", type=str, default="results/results.json",
                        help="Path to write the results JSON file.")
    parser.add_argument("--n_permutations", type=int, default=1000,
                        help="Number of permutations for the permutation test.")
    parser.add_argument("--random_state", type=int, default=42,
                        help="Random state for reproducibility.")
    return parser.parse_args()

def save_results_to_json(results_dict, output_path):
    """
    Serializes the evaluation results dictionary to a JSON file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2)
    
    logging.info(f"Results successfully written to {output_path}")

def main():
    args = parse_args()
    logger = setup_logging("write_results")
    
    try:
        # Load features and model
        logger.info(f"Loading features from {args.features_path}")
        features_data = load_features(args.features_path)
        
        logger.info(f"Loading model from {args.model_path}")
        model = load_model(args.model_path)
        
        # Prepare data
        X = features_data['X']
        y = features_data['y']
        
        # Calculate metrics
        logger.info("Calculating metrics...")
        metrics = calculate_metrics(model, X, y)
        
        # Perform permutation test
        logger.info(f"Performing permutation test with {args.n_permutations} permutations...")
        p_value = perform_permutation_test(model, X, y, n_permutations=args.n_permutations, 
                                           random_state=args.random_state)
        
        # Compile results
        results = {
            "r2_score": metrics['r2_score'],
            "mae": metrics['mae'],
            "p_value": p_value,
            "n_permutations": args.n_permutations,
            "random_state": args.random_state
        }
        
        # Save results
        save_results_to_json(results, args.output_path)
        
        logger.info("Pipeline execution completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())