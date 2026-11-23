import os
import sys
import json
import logging
import pickle
from pathlib import Path
import numpy as np
from sklearn.metrics import balanced_accuracy_score, f1_score
from typing import Dict, Any, Tuple, List

# Import from project utilities
from utils.config import get_models_dir, get_processed_dir, get_seed
from models.stratified_permutation import run_stratified_permutation_test

# Configure logging for the evaluation module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model_and_metrics() -> Tuple[Any, Dict[str, Any]]:
    """Load the trained Random Forest model and training metrics."""
    models_dir = get_models_dir()
    model_path = models_dir / "random_forest.pkl"
    metrics_path = models_dir / "training_metrics.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not metrics_path.exists():
        raise FileNotFoundError(f"Training metrics file not found: {metrics_path}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    with open(metrics_path, 'r') as f:
        training_metrics = json.load(f)

    logger.info(f"Loaded model from {model_path}")
    logger.info(f"Loaded training metrics from {metrics_path}")
    return model, training_metrics

def load_species_profiles() -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """Load species profiles data for evaluation."""
    processed_dir = get_processed_dir()
    profiles_path = processed_dir / "species_profiles.csv"

    if not profiles_path.exists():
        raise FileNotFoundError(f"Species profiles file not found: {profiles_path}")

    import pandas as pd
    df = pd.read_csv(profiles_path)

    # Identify land cover columns (assuming they start with specific prefixes or are numeric)
    # Based on merge_and_buffer, columns are like 'forest_prop_100m', etc.
    # We need to separate features (X), target (y), and stratification key (species_id)
    
    if 'species_id' not in df.columns or 'foraging_guild' not in df.columns:
        raise ValueError("Species profiles must contain 'species_id' and 'foraging_guild' columns")

    target_col = 'foraging_guild'
    strat_col = 'species_id'
    
    # Features are all columns except target and stratification
    feature_cols = [col for col in df.columns if col not in [target_col, strat_col]]
    
    X = df[feature_cols].values
    y = df[target_col].values
    strat = df[strat_col].values

    logger.info(f"Loaded {len(df)} species profiles with {len(feature_cols)} features")
    return X, y, strat, feature_cols

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate balanced accuracy and per-class F1 scores."""
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average='macro')
    f1_weighted = f1_score(y_true, y_pred, average='weighted')
    
    # Per-class F1
    classes = np.unique(y_true)
    f1_per_class = {}
    for cls in classes:
        f1_per_class[str(cls)] = f1_score(y_true == cls, y_pred == cls)

    metrics = {
        "balanced_accuracy": float(bal_acc),
        "f1_macro": float(f1_macro),
        "f1_weighted": float(f1_weighted),
        "f1_per_class": f1_per_class
    }
    
    logger.info(f"Calculated metrics: Balanced Acc={bal_acc:.4f}, F1 Macro={f1_macro:.4f}")
    return metrics

def run_evaluation(model: Any, X: np.ndarray, y: np.ndarray, strat: np.ndarray) -> Dict[str, Any]:
    """Run the full evaluation including stratified permutation test."""
    seed = get_seed()
    alpha = 0.05
    n_permutations = 1000  # As specified in task description

    # 1. Generate predictions
    y_pred = model.predict(X)
    
    # 2. Calculate observed metrics
    observed_metrics = calculate_metrics(y, y_pred)
    observed_accuracy = observed_metrics["balanced_accuracy"]
    
    logger.info(f"Observed Balanced Accuracy: {observed_accuracy:.4f}")

    # 3. Run Stratified Permutation Test
    logger.info(f"Starting Stratified Permutation Test (n={n_permutations}, seed={seed})...")
    
    try:
        p_value, null_distribution = run_stratified_permutation_test(
            X, y, strat, 
            model=model, 
            n_permutations=n_permutations, 
            random_state=seed,
            metric_func=lambda yt, yp: balanced_accuracy_score(yt, yp)
        )
    except Exception as e:
        logger.error(f"Permutation test failed: {e}")
        # Fallback to a simple placeholder if the specialized function fails, 
        # but log it as a critical issue. However, per constraints, we should 
        # let the real logic run. We assume the imported function works.
        raise e

    logger.info(f"Permutation test completed. P-value: {p_value:.4f}")

    # 4. Determine pass/fail
    is_significant = p_value < alpha
    status = "PASS" if is_significant else "FAIL"

    evaluation_results = {
        "seed": seed,
        "alpha": alpha,
        "n_permutations": n_permutations,
        "observed_metrics": observed_metrics,
        "p_value": float(p_value),
        "is_significant": bool(is_significant),
        "status": status,
        "null_distribution_stats": {
            "mean": float(np.mean(null_distribution)),
            "std": float(np.std(null_distribution)),
            "min": float(np.min(null_distribution)),
            "max": float(np.max(null_distribution))
        }
    }

    return evaluation_results

def save_results(results: Dict[str, Any]) -> str:
    """Save evaluation results to JSON."""
    models_dir = get_models_dir()
    output_path = models_dir / "evaluation_results.json"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_path}")
    return str(output_path)

def main():
    """Main entry point for the evaluation script."""
    logger.info("Starting Evaluation Pipeline...")
    
    try:
        # Load artifacts
        model, train_metrics = load_model_and_metrics()
        X, y, strat, feature_cols = load_species_profiles()
        
        # Run evaluation
        results = run_evaluation(model, X, y, strat)
        
        # Save results
        output_path = save_results(results)
        
        # Log final summary
        logger.info("="*50)
        logger.info("EVALUATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Seed: {results['seed']}")
        logger.info(f"Alpha Threshold: {results['alpha']}")
        logger.info(f"Observed Balanced Accuracy: {results['observed_metrics']['balanced_accuracy']:.4f}")
        logger.info(f"P-value: {results['p_value']:.4f}")
        logger.info(f"Status: {results['status']}")
        logger.info(f"Result saved to: {output_path}")
        logger.info("="*50)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())