import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import random
import numpy as np
import pandas as pd
from scipy.stats import kendalltau

# Local imports matching API surface
from config import ensure_dirs
from utils.logger import setup_logging, get_logger
from models.train import run_random_search, save_results, TrainingConfig
from models.evaluate import run_evaluation
from analysis.interpret import load_model_and_weights, load_processed_data, prepare_graph_features, run_inference, calculate_r2, perform_perturbation_study

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def load_model_config(seed: int) -> TrainingConfig:
    """Create a training config with a specific random seed."""
    # Load base config from config.py if available, otherwise construct default
    # Assuming config.py exports a base config or we construct one here
    config = TrainingConfig(
        hidden_dim=64,
        num_layers=2,
        learning_rate=0.001,
        batch_size=32,
        epochs=50,
        random_seed=seed,
        dropout=0.1,
        weight_decay=1e-5
    )
    return config

def run_training_for_seed(seed: int, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Run a single training job with a specific seed and return metrics."""
    logger.info(f"Starting training with seed {seed}")
    
    try:
        # Set global random seeds
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        
        config = load_model_config(seed)
        
        # Run training (using the existing run_random_search but with fixed seed)
        # We need to adapt run_random_search to run a single config
        # For now, we'll call train_model directly if possible, or wrap it
        
        # Since run_random_search does a search, we'll need to modify approach
        # Let's assume we have a way to train with a single config
        # We'll use the existing infrastructure but force a single iteration
        
        # Placeholder for actual training logic - we need to integrate with existing train.py
        # The existing train.py has run_random_search which does multiple configs
        # We'll need to extract the single training logic or modify it
        
        # For this implementation, we'll assume we can call a training function
        # that takes a config and returns results
        
        # Since we don't have a direct single-config training function exposed,
        # we'll need to work with what's available
        
        # Let's assume we can modify run_random_search to accept a single config
        # or we create a wrapper
        
        # For now, we'll simulate the training result structure
        # In a real implementation, this would call the actual training pipeline
        
        # TODO: Integrate with actual training pipeline
        # This is a placeholder that should be replaced with actual training call
        result = {
            'seed': seed,
            'r2': 0.0,  # Will be replaced with actual value
            'mae': 0.0,
            'model_path': None,
            'config': config.__dict__
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Training failed for seed {seed}: {str(e)}")
        return None

def get_shap_rankings(model_path: str, logger: logging.Logger) -> Optional[List[int]]:
    """Load model, compute SHAP values, and return feature rankings."""
    try:
        # Load the trained model
        model, config = load_model_and_weights(model_path)
        
        # Load processed data
        X_train, y_train, X_val, y_val, X_test, y_test = load_processed_data()
        
        # Prepare features
        train_features = prepare_graph_features(X_train)
        
        # Compute SHAP values
        # This would use SHAP library with the model
        # For now, we'll simulate the ranking
        
        # In a real implementation:
        # import shap
        # explainer = shap.Explainer(model)
        # shap_values = explainer(train_features)
        # rankings = np.argsort(np.abs(shap_values).mean(axis=0))[::-1].tolist()
        
        # Placeholder - should be replaced with actual SHAP computation
        rankings = list(range(10))  # Simulated ranking of 10 features
        
        return rankings
        
    except Exception as e:
        logger.error(f"SHAP computation failed: {str(e)}")
        return None

def compute_kendall_tau_consistency(rankings_list: List[List[int]]) -> float:
    """Compute average Kendall's Tau correlation across all pairs of rankings."""
    if len(rankings_list) < 2:
        return 1.0  # Perfect consistency if only one ranking
    
    correlations = []
    n = len(rankings_list)
    
    for i in range(n):
        for j in range(i + 1, n):
            tau, _ = kendalltau(rankings_list[i], rankings_list[j])
            correlations.append(tau)
    
    return np.mean(correlations)

def generate_consistency_report(
    seeds: List[int],
    results: List[Dict[str, Any]],
    rankings: List[List[int]],
    consistency_metric: float,
    output_path: Path,
    logger: logging.Logger
):
    """Generate the SHAP consistency report in Markdown format."""
    with open(output_path, 'w') as f:
        f.write("# SHAP Consistency Report\n\n")
        f.write("This report evaluates the stability of feature importance rankings\n")
        f.write("across multiple training runs with different random seeds.\n\n")
        
        f.write("## Methodology\n\n")
        f.write("- **Number of seeds tested**: {}\n".format(len(seeds)))
        f.write("- **Consistency metric**: Kendall's Tau correlation\n")
        f.write("- **Stability threshold**: ≥ 0.7 considered stable\n\n")
        
        f.write("## Training Results\n\n")
        f.write("| Seed | R² | MAE | Status |\n")
        f.write("|------|----|-----|--------|\n")
        
        for seed, result in zip(seeds, results):
            if result:
                status = "✓" if result.get('r2', 0) > 0 else "✗"
                f.write("| {} | {:.4f} | {:.4f} | {} |\n".format(
                    seed, 
                    result.get('r2', 0), 
                    result.get('mae', 0), 
                    status
                ))
            else:
                f.write("| {} | - | - | Failed |\n".format(seed))
        
        f.write("\n## Consistency Analysis\n\n")
        f.write("### Kendall's Tau Correlations\n\n")
        
        if len(rankings) >= 2:
            f.write("Pairwise correlations between SHAP rankings:\n\n")
            f.write("| Seed Pair | Kendall's Tau |\n")
            f.write("|-----------|---------------|\n")
            
            n = len(rankings)
            for i in range(n):
                for j in range(i + 1, n):
                    tau, _ = kendalltau(rankings[i], rankings[j])
                    f.write("| {} vs {} | {:.4f} |\n".format(seeds[i], seeds[j], tau))
            
            f.write("\n### Overall Consistency\n\n")
            f.write("**Average Kendall's Tau**: {:.4f}\n\n".format(consistency_metric))
            
            if consistency_metric >= 0.7:
                f.write("✅ **Conclusion**: The model's feature importance rankings are **stable**\n")
                f.write("across different random seeds (Kendall's Tau ≥ 0.7).\n")
            elif consistency_metric >= 0.5:
                f.write("⚠️ **Conclusion**: The model's feature importance rankings show **moderate stability**\n")
                f.write("across different random seeds (0.5 ≤ Kendall's Tau < 0.7).\n")
            else:
                f.write("❌ **Conclusion**: The model's feature importance rankings are **unstable**\n")
                f.write("across different random seeds (Kendall's Tau < 0.5).\n")
        else:
            f.write("Insufficient data to compute consistency metrics.\n")
        
        f.write("\n## Recommendations\n\n")
        if consistency_metric >= 0.7:
            f.write("- The model is robust to random initialization.\n")
            f.write("- Feature importance findings can be considered reliable.\n")
        else:
            f.write("- Consider ensemble methods to improve stability.\n")
            f.write("- Increase training epochs or adjust hyperparameters.\n")
            f.write("- Re-evaluate feature selection process.\n")

def run_consistency_analysis():
    """Main function to run the SHAP consistency analysis."""
    logger = setup_logging("consistency_analysis")
    
    # Get seeds from config or use defaults
    seeds = [42, 123, 456, 789, 1011]  # Default seeds
    
    logger.info(f"Starting SHAP consistency analysis with {len(seeds)} seeds")
    
    # Ensure output directory exists
    artifacts_dir = PROJECT_ROOT / "artifacts"
    ensure_dirs(artifacts_dir)
    output_path = artifacts_dir / "shap_consistency_report.md"
    
    results = []
    rankings = []
    
    for seed in seeds:
        # Train model with specific seed
        result = run_training_for_seed(seed, logger)
        results.append(result)
        
        if result and result.get('model_path'):
            # Get SHAP rankings
            ranking = get_shap_rankings(result['model_path'], logger)
            if ranking:
                rankings.append(ranking)
        else:
            logger.warning(f"No model produced for seed {seed}")
    
    # Compute consistency metric
    if len(rankings) >= 2:
        consistency_metric = compute_kendall_tau_consistency(rankings)
    else:
        consistency_metric = 0.0
        logger.warning("Insufficient successful training runs to compute consistency")
    
    # Generate report
    generate_consistency_report(
        seeds=seeds,
        results=results,
        rankings=rankings,
        consistency_metric=consistency_metric,
        output_path=output_path,
        logger=logger
    )
    
    logger.info(f"Consistency report saved to {output_path}")
    return consistency_metric

def main():
    parser = argparse.ArgumentParser(description="Run SHAP consistency analysis")
    parser.add_argument("--seeds", type=int, nargs="+", default=None,
                      help="Random seeds to test (default: 5 predefined seeds)")
    args = parser.parse_args()
    
    if args.seeds:
        run_consistency_analysis(seeds=args.seeds)
    else:
        run_consistency_analysis()

if __name__ == "__main__":
    main()
