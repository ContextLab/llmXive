import os
import sys
import logging
import math
import pickle
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure project root is in path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required output directories exist."""
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def load_models(models_dir: Optional[Path] = None):
    """
    Load trained models from disk.
    Expected structure: models_dir/{model_type}_{property}.pkl
    """
    if models_dir is None:
        models_dir = PROJECT_ROOT / "models"
    
    if not models_dir.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    
    models = {}
    for model_file in models_dir.glob("*.pkl"):
        with open(model_file, 'rb') as f:
            model_data = pickle.load(f)
            # Assuming model_data is a dict with 'model' and metadata
            model_name = model_file.stem
            models[model_name] = model_data.get('model', model_data)
    
    return models

def load_test_data(data_path: Optional[Path] = None):
    """
    Load test data used for evaluation.
    Expected: data/processed/test_data.parquet or similar
    """
    import pandas as pd
    
    if data_path is None:
        # Try common locations
        possible_paths = [
            PROJECT_ROOT / "data" / "processed" / "test_data.parquet",
            PROJECT_ROOT / "data" / "processed" / "descriptors.parquet"
        ]
        data_path = None
        for p in possible_paths:
            if p.exists():
                data_path = p
                break
        
        if data_path is None:
            raise FileNotFoundError("Could not find test data in expected locations.")
    
    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def evaluate_model(model, X_test, y_test, model_name: str = "unknown"):
    """
    Evaluate a single model on test data.
    Returns dict with MAE, RMSE, R2.
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    return {
        "model_name": model_name,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    }

def generate_report(evaluation_results: List[Dict], output_path: Optional[Path] = None):
    """
    Generate a CSV report from evaluation results.
    """
    import pandas as pd
    
    if not evaluation_results:
        raise ValueError("No evaluation results to generate report.")
    
    df = pd.DataFrame(evaluation_results)
    
    if output_path is None:
        output_path = PROJECT_ROOT / "results" / "baseline_report.csv"
    
    df.to_csv(output_path, index=False)
    logger.info(f"Report saved to {output_path}")
    return output_path

def isolate_bottom_deferred(df: pd.DataFrame, target_col: str, quantile: float = 0.2):
    """
    Isolate the bottom quantile of a target property.
    Uses the full dataset distribution to determine the threshold.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    threshold = df[target_col].quantile(quantile)
    bottom_df = df[df[target_col] <= threshold]
    
    logger.info(f"Isolated {len(bottom_df)} samples (bottom {quantile*100:.1f}%) for {target_col} "
                f"(threshold: {threshold:.4f})")
    
    return bottom_df

def calculate_per_bin_mae(y_true: List[float], y_pred: List[float], bin_labels: List[int]):
    """
    Calculate MAE for each bin.
    """
    import numpy as np
    from sklearn.metrics import mean_absolute_error
    
    unique_bins = sorted(list(set(bin_labels)))
    bin_maes = {}
    
    for b in unique_bins:
        mask = np.array(bin_labels) == b
        if np.sum(mask) > 0:
            bin_maes[b] = mean_absolute_error(
                np.array(y_true)[mask],
                np.array(y_pred)[mask]
            )
        else:
            bin_maes[b] = None
    
    return bin_maes

def calculate_performance_degradation(skewed_results: Dict, balanced_results: Dict):
    """
    Calculate performance degradation: MAE_skewed - MAE_balanced for minority subset.
    """
    degradation = {}
    
    for prop in skewed_results:
        if prop in balanced_results:
            mae_skewed = skewed_results[prop]
            mae_balanced = balanced_results[prop]
            degradation[prop] = mae_skewed - mae_balanced
        else:
            logger.warning(f"Property {prop} missing in balanced results, skipping degradation calc.")
    
    return degradation

def calculate_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    d = (mean1 - mean2) / pooled_std
    """
    import numpy as np
    
    arr1 = np.array(group1)
    arr2 = np.array(group2)
    
    mean1 = np.mean(arr1)
    mean2 = np.mean(arr2)
    
    std1 = np.std(arr1, ddof=1)
    std2 = np.std(arr2, ddof=1)
    
    n1 = len(arr1)
    n2 = len(arr2)
    
    if n1 + n2 <= 2:
        raise ValueError("Need at least 3 samples total to calculate pooled std.")
    
    # Pooled standard deviation
    pooled_std = math.sqrt(((n1 - 1) * (std1 ** 2) + (n2 - 1) * (std2 ** 2)) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def power_analysis_z_test(effect_size: float = 0.5, alpha: float = 0.05, power: float = 0.8, 
                          two_sided: bool = True) -> int:
    """
    Calculate required sample size (number of seeds/iterations) for a z-test (or t-test approximation).
    
    Formula for two-sample t-test (approximated by z-test for large N):
    n = 2 * ((Z_alpha/2 + Z_beta) / effect_size)^2
    
    For one-sample or paired tests, the formula is slightly different but the logic holds.
    We assume a paired test context (comparing skewed vs balanced on same seeds).
    
    Returns the number of samples (seeds) per group. Since it's paired, this is total seeds.
    """
    from scipy.stats import norm
    
    # Z critical value for alpha (two-sided)
    if two_sided:
        z_alpha = norm.ppf(1 - alpha / 2)
    else:
        z_alpha = norm.ppf(1 - alpha)
    
    # Z critical value for power (beta = 1 - power)
    z_beta = norm.ppf(power)
    
    # Standard formula for sample size in two-sample test (approx)
    # For paired t-test, the variance of differences is used, but the structure is similar.
    # n = 2 * ( (z_alpha + z_beta) / d )^2  <-- This is for independent groups.
    # For paired, it's often: n = ( (z_alpha + z_beta) / d )^2 * 2? 
    # Actually, for paired t-test, the effect size d is defined on the differences.
    # The formula n = ( (z_alpha + z_beta) / d )^2 is standard for paired tests.
    
    # Let's use the standard paired test formula:
    # n = ((Z_alpha + Z_beta) / effect_size)^2
    # Note: scipy's TTestPower uses a slightly different internal logic, but this approximation is robust for planning.
    
    numerator = (z_alpha + z_beta) ** 2
    denominator = effect_size ** 2
    
    n = numerator / denominator
    
    return math.ceil(n)

def run_power_analysis(effect_size: float = 0.5, alpha: float = 0.05, power: float = 0.8, 
                       output_path: Optional[Path] = None):
    """
    Run power analysis to determine minimum number of seeds required.
    Outputs to results/power_analysis.json.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "results" / "power_analysis.json"
    
    ensure_directories()
    
    required_seeds = power_analysis_z_test(effect_size=effect_size, alpha=alpha, power=power)
    
    result = {
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "minimum_seeds_required": required_seeds,
        "description": "Minimum number of random seeds required for paired statistical testing "
                       f"(Cohen's d={effect_size}, power>={power}, alpha={alpha})."
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Power analysis complete. Required seeds: {required_seeds}. Saved to {output_path}")
    return result

def main():
    """
    Main entry point for T028: Power Analysis.
    """
    logger.info("Starting Power Analysis (T028)...")
    
    # Parameters from task description
    # Cohen's d = 0.5 (medium effect size)
    # Power >= 0.8
    # Alpha = 0.05
    effect_size = 0.5
    alpha = 0.05
    power = 0.8
    
    try:
        result = run_power_analysis(
            effect_size=effect_size,
            alpha=alpha,
            power=power
        )
        logger.info(f"Success: {result['minimum_seeds_required']} seeds required.")
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()