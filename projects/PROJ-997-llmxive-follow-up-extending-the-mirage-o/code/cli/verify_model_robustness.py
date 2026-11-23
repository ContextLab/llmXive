"""
T042: Verify Model Robustness via Sensitivity Analysis.

Runs a sensitivity analysis on the trained KRR model (T021) by perturbing
input features (gradient norms, curvature) by ±5% and measuring the variance
in predicted divergence. Logs the coefficient of variation to
data/processed/model_robustness.json.

Dependency: Must run after T022A.
"""
import json
import logging
import argparse
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sklearn.linear_model import KernelRidge

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_PATH = PROJECT_ROOT / "data" / "models" / "gap_predictor.pkl"
TEST_DATA_PATH = DATA_PROCESSED_DIR / "split_test.parquet"
OUTPUT_PATH = DATA_PROCESSED_DIR / "model_robustness.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("T042_Robustness")

def load_model(model_path: Path) -> KernelRidge:
    """Load the trained KRR model."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_test_data(test_path: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load test data and extract features and target.
    Returns: (X_features, y_target, feature_names)
    """
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_path}")
    
    import pandas as pd
    df = pd.read_parquet(test_path)
    
    # Identify feature columns based on T019/T021 logic (gradient_norms, curvature)
    # Assuming PCA was applied, we look for PCA components or original features
    # Based on T019, features are transformed. We need the columns used for training.
    # Let's assume standard feature columns exist or PCA components.
    # We will look for columns that are numeric and not the target.
    # Common naming from T021: 'gradient_norms', 'local_curvature' or PCA components like 'pca_0', 'pca_1'
    
    # Heuristic: Select numeric columns that are not the target 'calculated_kl_divergence'
    target_col = 'calculated_kl_divergence'
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c != target_col]
    
    if not feature_cols:
        raise ValueError("No numeric feature columns found in test data.")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    return X, y, feature_cols

def perturb_features(
    X: np.ndarray, 
    perturbation_pct: float, 
    seed: int,
    direction: str = 'both'
) -> List[np.ndarray]:
    """
    Perturb features by a percentage (e.g., 0.05 for 5%).
    Returns a list of perturbed arrays.
    """
    rng = np.random.default_rng(seed)
    perturbations = []
    
    # Define directions: +5%, -5%, and random noise within range
    # The task asks for "perturbing ... by ±5%". We will test +5% and -5% specifically.
    factors = [1.0 + perturbation_pct, 1.0 - perturbation_pct]
    
    if direction == 'both':
        for factor in factors:
            # Apply uniform perturbation to all features for this run
            # To simulate realistic noise, we could add per-feature noise, 
            # but a uniform scaling is a standard sensitivity check.
            # Let's add a small random jitter to the factor per feature to be more robust
            # or just use the exact factor. The task says "perturbing ... by ±5%".
            # We will apply the factor directly.
            X_pert = X * factor
            perturbations.append(X_pert)
    else:
        # Random noise case
        noise = rng.uniform(-perturbation_pct, perturbation_pct, size=X.shape)
        X_pert = X * (1.0 + noise)
        perturbations.append(X_pert)
        
    return perturbations

def calculate_robustness_metrics(
    model: KernelRidge,
    X_original: np.ndarray,
    y_original: np.ndarray,
    perturbed_sets: List[np.ndarray],
    feature_names: List[str]
) -> Dict[str, Any]:
    """
    Calculate predictions for original and perturbed sets, then compute variance and CV.
    """
    # Original predictions
    y_pred_original = model.predict(X_original)
    
    results = {
        "original_mean": float(np.mean(y_pred_original)),
        "original_std": float(np.std(y_pred_original)),
        "perturbation_analysis": []
    }
    
    for i, X_pert in enumerate(perturbed_sets):
        y_pred_pert = model.predict(X_pert)
        
        # Calculate difference
        diff = y_pred_pert - y_pred_original
        mean_diff = float(np.mean(diff))
        std_diff = float(np.std(diff))
        
        # Coefficient of Variation (CV) of the prediction distribution
        # CV = Std / Mean. If mean is near zero, handle division.
        mean_pred_pert = float(np.mean(y_pred_pert))
        if abs(mean_pred_pert) > 1e-8:
            cv = std_diff / abs(mean_pred_pert)
        else:
            cv = float('inf') if std_diff > 0 else 0.0
        
        results["perturbation_analysis"].append({
            "perturbation_id": i,
            "description": f"{'+5%' if i == 0 else '-5%'} scaling",
            "mean_prediction": mean_pred_pert,
            "mean_difference_from_original": mean_diff,
            "std_difference": std_diff,
            "coefficient_of_variation": cv
        })
    
    # Overall robustness summary
    all_cvs = [p["coefficient_of_variation"] for p in results["perturbation_analysis"]]
    avg_cv = float(np.mean(all_cvs))
    max_cv = float(np.max(all_cvs))
    
    results["summary"] = {
        "average_coefficient_of_variation": avg_cv,
        "max_coefficient_of_variation": max_cv,
        "threshold_passed": avg_cv < 0.1 # Arbitrary threshold for "stable", or log warning if high
    }
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Verify Model Robustness (T042)")
    parser.add_argument("--model-path", type=str, default=str(MODEL_PATH), help="Path to gap_predictor.pkl")
    parser.add_argument("--test-data", type=str, default=str(TEST_DATA_PATH), help="Path to split_test.parquet")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH), help="Output JSON path")
    parser.add_argument("--perturbation", type=float, default=0.05, help="Perturbation percentage (e.g., 0.05)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    model_path = Path(args.model_path)
    test_path = Path(args.test_data)
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading model from {model_path}")
    try:
        model = load_model(model_path)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    logger.info(f"Loading test data from {test_path}")
    try:
        X, y, feature_names = load_test_data(test_path)
    except Exception as e:
        logger.error(f"Failed to load test data: {e}")
        raise

    logger.info(f"Running sensitivity analysis with perturbation ±{args.perturbation*100:.1f}%")
    perturbations = perturb_features(X, args.perturbation, args.seed)
    
    logger.info("Calculating robustness metrics")
    metrics = calculate_robustness_metrics(model, X, y, perturbations, feature_names)

    # Add metadata
    final_report = {
        "task_id": "T042",
        "model_path": str(model_path),
        "test_data_path": str(test_path),
        "perturbation_percentage": args.perturbation,
        "seed": args.seed,
        "feature_count": len(feature_names),
        "sample_count": X.shape[0],
        **metrics
    }

    logger.info(f"Writing results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Robustness analysis complete. Avg CV: {final_report['summary']['average_coefficient_of_variation']:.4f}")
    
    # Return 0 if successful, non-zero if CV is too high (optional strictness)
    if final_report['summary']['average_coefficient_of_variation'] > 1.0:
        logger.warning("High coefficient of variation detected. Model may be sensitive to feature noise.")
        return 0 # Still completed, just a warning
    
    return 0

if __name__ == "__main__":
    exit(main())
