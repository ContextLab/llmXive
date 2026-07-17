import os
import sys
import json
import pickle
import warnings
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from scipy import stats

# Import from project structure (relative to code/)
# Note: In execution context, sys.path is adjusted to include 'code' root
from evaluation.metrics import calculate_metrics, load_test_data, load_models, get_predictions

# Constants
RANDOM_SEED = 42
SENSITIVITY_ITERATIONS = 100
SENSITIVITY_SUBSET_SIZE = 100
OUTPUT_PATH = Path("data/sensitivity_analysis.json")

def load_metrics_from_disk(metrics_path: Path) -> Dict[str, Any]:
    """Load metrics from the metrics output file."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_vif_results(vif_path: Path) -> Dict[str, Any]:
    """Load VIF results from disk."""
    if not vif_path.exists():
        raise FileNotFoundError(f"VIF results file not found: {vif_path}")
    with open(vif_path, 'r') as f:
        return json.load(f)

def load_lrt_results(lrt_path: Path) -> Dict[str, Any]:
    """Load Likelihood Ratio Test results from disk."""
    if not lrt_path.exists():
        raise FileNotFoundError(f"LRT results file not found: {lrt_path}")
    with open(lrt_path, 'r') as f:
        return json.load(f)

def calculate_delong_auc_diff(y_true: np.ndarray, y_pred_full: np.ndarray, y_pred_null: np.ndarray) -> float:
    """
    Calculate the difference in AUC between full and null models.
    Note: This is a simplified version; a full DeLong implementation would be more complex.
    """
    auc_full = roc_auc_score(y_true, y_pred_full)
    auc_null = roc_auc_score(y_true, y_pred_null)
    return auc_full - auc_null

def run_statistical_comparison(delongs_diffs: List[float]) -> Dict[str, float]:
    """
    Run statistical comparison on the distribution of AUC differences.
    Returns mean, std, and 95% CI.
    """
    if not delongs_diffs:
        return {"mean": 0.0, "std": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}
    
    mean_diff = np.mean(delongs_diffs)
    std_diff = np.std(delongs_diffs)
    
    # 95% Confidence Interval using t-distribution
    n = len(delongs_diffs)
    if n > 1:
        se = std_diff / np.sqrt(n)
        ci_lower = mean_diff - stats.t.ppf(0.975, n-1) * se
        ci_upper = mean_diff + stats.t.ppf(0.975, n-1) * se
    else:
        ci_lower = mean_diff
        ci_upper = mean_diff
        
    return {
        "mean": float(mean_diff),
        "std": float(std_diff),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }

def map_lrt_to_sc001(lrt_results: Dict[str, Any]) -> Dict[str, Any]:
    """Map LRT results to SC-001 criteria."""
    p_value = lrt_results.get("p_value", 1.0)
    is_significant = p_value < 0.05
    return {
        "sc001_criteria": "Met" if is_significant else "Not Met",
        "p_value": p_value,
        "interpretation": "Full model significantly better than null" if is_significant else "No significant improvement"
    }

def map_vif_to_sc003(vif_results: Dict[str, Any]) -> Dict[str, Any]:
    """Map VIF results to SC-003 criteria."""
    max_vif = vif_results.get("max_vif", 0)
    is_acceptable = max_vif <= 5.0
    return {
        "sc003_criteria": "Met" if is_acceptable else "Not Met",
        "max_vif": max_vif,
        "interpretation": "No multicollinearity detected" if is_acceptable else "Multicollinearity detected"
    }

def generate_final_summary(metrics: Dict[str, Any], vif: Dict[str, Any], lrt: Dict[str, Any], sensitivity: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the final summary report."""
    sc001 = map_lrt_to_sc001(lrt)
    sc003 = map_vif_to_sc003(vif)
    
    # Main hypothesis test
    hypothesis_supported = (
        sc001["sc001_criteria"] == "Met" and 
        sensitivity["mean_delta_auc"] > 0 and
        sensitivity["ci_lower"] > 0
    )
    
    return {
        "hypothesis": "Flavor and role predict compatibility beyond frequency",
        "supported": hypothesis_supported,
        "evidence": {
            "lrt_p_value": lrt.get("p_value"),
            "auc_delta_mean": sensitivity["mean_delta_auc"],
            "auc_delta_std": sensitivity["std_delta_auc"],
            "auc_delta_ci_95": [sensitivity["ci_lower"], sensitivity["ci_upper"]],
            "vif_max": vif.get("max_vif"),
            "sc001_status": sc001["sc001_criteria"],
            "sc003_status": sc003["sc003_criteria"]
        },
        "sensitivity_analysis": sensitivity,
        "summary_text": f"Analysis supports hypothesis: {hypothesis_supported}. "
                        f"Mean AUC delta: {sensitivity['mean_delta_auc']:.4f} (std: {sensitivity['std_delta_auc']:.4f}, "
                        f"95% CI: [{sensitivity['ci_lower']:.4f}, {sensitivity['ci_upper']:.4f}]). "
                        f"LRT p-value: {lrt.get('p_value', 'N/A'):.4f}."
    }

def run_sensitivity_analysis(
    test_data_path: Path,
    models_path: Path,
    output_path: Path,
    n_iterations: int = SENSITIVITY_ITERATIONS,
    subset_size: int = SENSITIVITY_SUBSET_SIZE,
    seed: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by re-running evaluation on random subsets of the test set.
    
    This verifies the stability of the ΔAUC result by sampling 'subset_size' rows
    from the test set, 'n_iterations' times, and calculating the AUC difference
    for each iteration.
    
    Args:
        test_data_path: Path to the processed test data CSV
        models_path: Path to the saved models (pickle)
        output_path: Path to save the sensitivity analysis results
        n_iterations: Number of bootstrap iterations
        subset_size: Size of the random subset for each iteration
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing sensitivity analysis results
    """
    # Set random seed
    random.seed(seed)
    np.random.seed(seed)
    
    print(f"Loading test data from {test_data_path}...")
    try:
        # Load full test data
        # Assuming the metrics module has a function to load raw data or we load directly
        # Since load_test_data in metrics.py might return processed metrics, we need the raw dataframe
        # We will attempt to load the CSV directly as the 'test_data_path' usually points to the split CSV
        df = pd.read_csv(test_data_path)
        
        # Ensure we have necessary columns
        required_cols = ['compatibility_label', 'full_model_pred', 'null_model_pred']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            # Try to load predictions from models if not in CSV
            # Fallback: Load models and predict
            with open(models_path, 'rb') as f:
                models = pickle.load(f)
            
            # We need features to predict. This assumes the CSV has features or we need to reconstruct.
            # For this task, we assume the test data CSV already has predictions or we can derive them.
            # If not, we might need to re-run prediction logic.
            # Given the constraints, we assume the CSV has the predictions or we can calculate AUC from available columns.
            # Let's assume the CSV has 'y_true', 'y_pred_full', 'y_pred_null' or similar.
            # If the column names are different, we map them.
            pass
        
        # Standardize column names for this function
        if 'compatibility_label' in df.columns:
            y_true_col = 'compatibility_label'
        elif 'y_true' in df.columns:
            y_true_col = 'y_true'
        else:
            raise ValueError("Cannot find true label column in test data")
        
        if 'full_model_pred' in df.columns:
            y_pred_full_col = 'full_model_pred'
        elif 'y_pred_full' in df.columns:
            y_pred_full_col = 'y_pred_full'
        else:
            # Attempt to load models and predict
            # This part might need adjustment based on actual data structure
            raise NotImplementedError("Prediction columns missing; model re-prediction logic required.")
            
        if 'null_model_pred' in df.columns:
            y_pred_null_col = 'null_model_pred'
        elif 'y_pred_null' in df.columns:
            y_pred_null_col = 'y_pred_null'
        else:
            raise NotImplementedError("Prediction columns missing; model re-prediction logic required.")

        y_true = df[y_true_col].values
        y_pred_full = df[y_pred_full_col].values
        y_pred_null = df[y_pred_null_col].values

    except FileNotFoundError:
        raise FileNotFoundError(f"Test data file not found at {test_data_path}")
    except Exception as e:
        raise RuntimeError(f"Error loading test data: {e}")

    print(f"Running {n_iterations} sensitivity iterations with subset size {subset_size}...")
    
    delong_diffs = []
    
    for i in range(n_iterations):
        # Random subset
        indices = np.random.choice(len(df), size=min(subset_size, len(df)), replace=False)
        
        y_true_sub = y_true[indices]
        y_pred_full_sub = y_pred_full[indices]
        y_pred_null_sub = y_pred_null[indices]
        
        # Calculate AUC difference
        try:
            auc_full = roc_auc_score(y_true_sub, y_pred_full_sub)
            auc_null = roc_auc_score(y_true_sub, y_pred_null_sub)
            diff = auc_full - auc_null
            delong_diffs.append(diff)
        except ValueError:
            # Handle cases where subset might have only one class
            delong_diffs.append(np.nan)
    
    # Filter out NaNs
    delong_diffs = [d for d in delong_diffs if not np.isnan(d)]
    
    if not delong_diffs:
        raise RuntimeError("No valid AUC differences calculated in sensitivity analysis.")
    
    # Calculate statistics
    mean_diff = np.mean(delong_diffs)
    std_diff = np.std(delong_diffs)
    
    # 95% CI
    n = len(delong_diffs)
    if n > 1:
        se = std_diff / np.sqrt(n)
        ci_lower = mean_diff - stats.t.ppf(0.975, n-1) * se
        ci_upper = mean_diff + stats.t.ppf(0.975, n-1) * se
    else:
        ci_lower = mean_diff
        ci_upper = mean_diff
    
    results = {
        "method": "Bootstrap Sensitivity Analysis",
        "n_iterations": n_iterations,
        "subset_size": subset_size,
        "seed": seed,
        "mean_delta_auc": float(mean_diff),
        "std_delta_auc": float(std_diff),
        "ci_lower_95": float(ci_lower),
        "ci_upper_95": float(ci_upper),
        "distribution": delong_diffs[:10], # Store first 10 for debugging/inspection
        "total_valid_iterations": len(delong_diffs)
    }
    
    # Save to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Sensitivity analysis complete. Results saved to {output_path}")
    return results

def main():
    """Main entry point for the report generation and sensitivity analysis."""
    # Define paths
    base_path = Path("data")
    test_data_path = base_path / "test_split.csv" # Assuming this is the output of T019
    models_path = base_path / "models.pkl" # Assuming models are saved here
    metrics_path = base_path / "evaluation_metrics.json"
    vif_path = base_path / "vif_results.json"
    lrt_path = base_path / "lrt_results.json"
    sensitivity_output_path = base_path / "sensitivity_analysis.json"
    final_report_path = base_path / "final_report.json"

    # 1. Run Sensitivity Analysis
    print("Starting Sensitivity Analysis (T041)...")
    try:
        sensitivity_results = run_sensitivity_analysis(
            test_data_path=test_data_path,
            models_path=models_path,
            output_path=sensitivity_output_path
        )
    except FileNotFoundError as e:
        print(f"Error: Could not find required data for sensitivity analysis: {e}")
        print("Note: This task requires the test split and model predictions to be available.")
        # In a real pipeline, we would fail loudly here
        sys.exit(1)
    
    # 2. Load other required results
    try:
        metrics = load_metrics_from_disk(metrics_path)
        vif = load_vif_results(vif_path)
        lrt = load_lrt_results(lrt_path)
    except FileNotFoundError as e:
        print(f"Error: Missing prerequisite file: {e}")
        sys.exit(1)

    # 3. Generate Final Summary
    final_summary = generate_final_summary(metrics, vif, lrt, sensitivity_results)
    
    # Save final report
    with open(final_report_path, 'w') as f:
        json.dump(final_summary, f, indent=2)
    
    print(f"Final report generated at {final_report_path}")
    print(f"Hypothesis Supported: {final_summary['supported']}")
    print(f"Summary: {final_summary['summary_text']}")
    
    return final_summary

if __name__ == "__main__":
    main()