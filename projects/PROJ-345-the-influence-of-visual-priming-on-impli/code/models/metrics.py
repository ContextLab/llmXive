import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import json
from pathlib import Path
import logging

from config import get_path

logger = logging.getLogger(__name__)

# --- Existing VIF and Collinearity Functions (Preserved) ---

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each feature."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    vif_data = {}
    X = df[features].dropna()
    if X.empty:
        return vif_data
    
    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    for i, feature in enumerate(features):
        try:
            vif = variance_inflation_factor(X_const.values, i)
            vif_data[feature] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature}: {e}")
            vif_data[feature] = np.nan
    
    return vif_data

def check_collinearity(vif_results: Dict[str, float], threshold: float = 5.0) -> bool:
    """Check if any VIF exceeds the threshold."""
    for feature, vif in vif_results.items():
        if vif > threshold:
            logger.warning(f"High collinearity detected for {feature} (VIF={vif:.2f})")
            return True
    return False

def run_vif_analysis(data: pd.DataFrame, features: List[str], output_path: Optional[Path] = None) -> Dict[str, float]:
    """Run VIF analysis and optionally save results."""
    vif_results = calculate_vif(data, features)
    has_collinearity = check_collinearity(vif_results)
    
    result = {
        "vif_values": vif_results,
        "has_high_collinearity": has_collinearity,
        "threshold": 5.0
    }
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
    
    return result

# --- Existing Benjamini-Hochberg Function (Preserved) ---

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg procedure to control FDR.
    Returns a list of booleans indicating whether each hypothesis is rejected.
    """
    import numpy as np
    
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate thresholds
    ranks = np.arange(1, n + 1)
    thresholds = (ranks / n) * alpha
    
    # Find the largest k such that p_(k) <= threshold_(k)
    reject = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_p_values[i] <= thresholds[i]:
            reject[i:] = True
            break
    
    # Map back to original order
    final_reject = np.zeros(n, dtype=bool)
    final_reject[sorted_indices] = reject
    
    return final_reject.tolist()

# --- Existing Convergence Metrics (Preserved) ---

def calculate_model_convergence_metrics(convergence_log: List[Dict]) -> Dict[str, Any]:
    """Calculate convergence success rate from a log of attempts."""
    total = len(convergence_log)
    if total == 0:
        return {"convergence_rate": 0.0, "total_attempts": 0}
    
    successes = sum(1 for entry in convergence_log if entry.get("converged", False))
    rate = successes / total if total > 0 else 0.0
    
    return {
        "convergence_rate": rate,
        "total_attempts": total,
        "successes": successes,
        "threshold": 0.80
    }

def save_convergence_metrics(metrics: Dict[str, Any], output_path: Path):
    """Save convergence metrics to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

# --- Existing Effect Size Functions (Preserved) ---

def calculate_cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """Calculate Cohen's d effect size."""
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(), group2.std()
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def calculate_partial_eta_squared(ss_effect: float, ss_error: float) -> float:
    """Calculate partial eta-squared."""
    if ss_effect + ss_error == 0:
        return 0.0
    return ss_effect / (ss_effect + ss_error)

def bootstrap_effect_size(data: pd.DataFrame, column: str, group_col: str, n_boot: int = 1000, seed: int = 42) -> Tuple[float, float, float]:
    """Calculate effect size with bootstrap confidence intervals."""
    np.random.seed(seed)
    
    groups = data[group_col].unique()
    if len(groups) < 2:
        return 0.0, 0.0, 0.0
    
    g1, g2 = groups[0], groups[1]
    s1 = data[data[group_col] == g1][column]
    s2 = data[data[group_col] == g2][column]
    
    original_d = calculate_cohens_d(s1, s2)
    
    boot_d = []
    for _ in range(n_boot):
        b1 = s1.sample(n=len(s1), replace=True, random_state=np.random.randint(0, 10000))
        b2 = s2.sample(n=len(s2), replace=True, random_state=np.random.randint(0, 10000))
        boot_d.append(calculate_cohens_d(b1, b2))
    
    ci_low, ci_high = np.percentile(boot_d, [2.5, 97.5])
    return original_d, ci_low, ci_high

def calculate_effect_sizes_with_bootstrap(data: pd.DataFrame, column: str, group_col: str) -> Dict[str, float]:
    """Calculate effect sizes and save them."""
    d, low, high = bootstrap_effect_size(data, column, group_col)
    return {
        "cohen_d": d,
        "ci_lower": low,
        "ci_upper": high
    }

def save_effect_sizes(effects: Dict[str, float], output_path: Path):
    """Save effect sizes to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(effects, f, indent=2)

# --- NEW: Alpha Sensitivity Analysis Implementation (T035) ---

def calculate_sensitivity_analysis(
    p_values: List[float], 
    alphas: Optional[List[float]] = None
) -> List[Dict[str, float]]:
    """
    Perform alpha sensitivity analysis by sweeping significance thresholds.
    
    Args:
        p_values: List of p-values from hypothesis tests.
        alphas: List of alpha thresholds to test. Defaults to [0.001, 0.01, 0.05, 0.10].
    
    Returns:
        List of dictionaries with 'alpha' and 'significance_rate'.
    """
    if not p_values:
        logger.warning("No p-values provided for sensitivity analysis.")
        return []
    
    if alphas is None:
        # Standard levels as per FR-006 and task description
        alphas = [0.001, 0.01, 0.05, 0.10]
    
    results = []
    n_tests = len(p_values)
    
    for alpha in sorted(alphas):
        # Count how many p-values are <= alpha
        significant_count = sum(1 for p in p_values if p <= alpha)
        significance_rate = significant_count / n_tests if n_tests > 0 else 0.0
        
        results.append({
            "alpha": alpha,
            "significance_rate": significance_rate
        })
    
    return results

def run_sensitivity_analysis(
    model_results_path: Path, 
    output_path: Path,
    p_value_column: str = "pvalue",
    alphas: Optional[List[float]] = None
) -> pd.DataFrame:
    """
    Run sensitivity analysis on model results and save to CSV.
    
    Args:
        model_results_path: Path to the CSV/JSON containing model results with p-values.
        output_path: Path to save the sensitivity_analysis.csv.
        p_value_column: Name of the column containing p-values.
        alphas: List of alpha thresholds to test.
    
    Returns:
        DataFrame containing the sensitivity analysis results.
    """
    logger.info(f"Running sensitivity analysis on {model_results_path}")
    
    # Load model results
    if model_results_path.suffix == '.csv':
        df = pd.read_csv(model_results_path)
    elif model_results_path.suffix == '.json':
        with open(model_results_path, 'r') as f:
            data = json.load(f)
            # Assume flat structure or handle nested as needed
            df = pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame(data)
    else:
        raise ValueError(f"Unsupported file format: {model_results_path.suffix}")
    
    if p_value_column not in df.columns:
        # Fallback: try to find a column containing 'p'
        possible_cols = [c for c in df.columns if 'p' in c.lower()]
        if possible_cols:
            p_value_column = possible_cols[0]
            logger.warning(f"Column '{p_value_column}' not found. Using '{p_value_column}' instead.")
        else:
            raise KeyError(f"Could not find p-value column '{p_value_column}' in {model_results_path}")
    
    # Extract valid p-values (drop NaNs)
    p_values = df[p_value_column].dropna().tolist()
    
    if not p_values:
        logger.warning("No valid p-values found for sensitivity analysis.")
        # Create empty result with headers
        result_df = pd.DataFrame(columns=["alpha", "significance_rate"])
    else:
        analysis_results = calculate_sensitivity_analysis(p_values, alphas)
        result_df = pd.DataFrame(analysis_results)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    result_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis saved to {output_path}")
    
    return result_df

def main():
    """Main entry point for running sensitivity analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run alpha sensitivity analysis on model results.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=str(get_path("processed") / "lmm_results.csv"),
        help="Path to model results CSV containing p-values."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(get_path("processed") / "sensitivity_analysis.csv"),
        help="Path to output sensitivity analysis CSV."
    )
    parser.add_argument(
        "--p-column", 
        type=str, 
        default="pvalue",
        help="Column name containing p-values."
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    try:
        df = run_sensitivity_analysis(
            model_results_path=input_path,
            output_path=output_path,
            p_value_column=args.p_column
        )
        print(f"Sensitivity Analysis Complete. Output: {output_path}")
        print(df)
        return 0
    except Exception as e:
        logger.error(f"Error running sensitivity analysis: {e}")
        return 1

if __name__ == "__main__":
    exit(main())