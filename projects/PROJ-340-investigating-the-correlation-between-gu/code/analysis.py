import os
import sys
import json
import random
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from typing import Dict, List, Any, Optional

def set_analysis_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if 'pd' in globals():
        pd.options.mode.chained_assignment = None

def check_distribution(data: pd.Series) -> Dict[str, Any]:
    """
    Check the distribution of a single variable.
    Returns a dictionary with distribution properties.
    """
    # Drop NaNs
    clean_data = data.dropna()
    if len(clean_data) < 3:
        return {
            "is_normal": False,
            "zero_fraction": 1.0,
            "skewness": 0.0,
            "reason": "Insufficient data"
        }
    
    # Shapiro-Wilk test for normality
    try:
        stat, p_value = stats.shapiro(clean_data)
        is_normal = p_value > 0.05
    except Exception:
        is_normal = False
        p_value = 0.0
    
    # Zero inflation check
    zero_fraction = (clean_data == 0).sum() / len(clean_data)
    
    # Skewness
    try:
        skewness = stats.skew(clean_data)
    except Exception:
        skewness = 0.0
    
    return {
        "is_normal": is_normal,
        "p_value": p_value,
        "zero_fraction": zero_fraction,
        "skewness": skewness,
        "reason": "Normal" if is_normal else "Non-Normal"
    }

def select_correlation_method(x: pd.Series, y: pd.Series, dist_info: Optional[Dict] = None) -> str:
    """
    Select the appropriate correlation method based on data distribution.
    
    Logic:
    1. If >30% zeros -> Spearman (or ZINB if implemented, defaulting to Spearman for robustness here)
    2. If Non-Normal (Shapiro p < 0.05) -> Spearman
    3. Otherwise -> Pearson
    """
    if dist_info is None:
        dist_info = check_distribution(x)
    
    # Priority 1: Zero Inflation
    if dist_info.get("zero_fraction", 0) > 0.30:
        return "spearman" # Robust to zeros and non-normality
    
    # Priority 2: Normality
    if not dist_info.get("is_normal", False):
        return "spearman"
    
    return "pearson"

def run_correlation_analysis(df: pd.DataFrame, predictors: List[str], outcomes: List[str], method: str = "auto") -> pd.DataFrame:
    """
    Run correlation analysis between predictors and outcomes.
    """
    results = []
    
    for outcome in outcomes:
        for predictor in predictors:
            pair = df[[outcome, predictor]].dropna()
            if len(pair) < 3:
                continue
            
            x = pair[predictor]
            y = pair[outcome]
            
            # Determine method
            current_method = method
            if method == "auto":
                dist_info = check_distribution(x)
                current_method = select_correlation_method(x, y, dist_info)
            
            if current_method == "pearson":
                corr, p_val = stats.pearsonr(x, y)
            else:
                corr, p_val = stats.spearmanr(x, y)
            
            results.append({
                "outcome": outcome,
                "predictor": predictor,
                "method": current_method,
                "correlation": corr,
                "p_value": p_val
            })
    
    return pd.DataFrame(results)

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction.
    Returns a list of booleans indicating if the result is significant.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    ranks = np.arange(1, n + 1)
    threshold = (ranks / n) * alpha
    
    # Find the largest k where p_k <= threshold
    significant = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_p_values[i] <= threshold[i]:
            significant[i:] = True
            break
    
    # Reorder to original indices
    final_significance = np.zeros(n, dtype=bool)
    final_significance[sorted_indices] = significant
    
    return final_significance.tolist()

def save_method_selection_log(log_data: List[Dict], output_path: str):
    """
    Save the method selection log to a JSON file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def main():
    """
    CLI entry point for analysis module.
    """
    parser = argparse.ArgumentParser(description="Run correlation analysis")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output JSON path")
    parser.add_argument("--predictors", type=str, nargs="+", required=True, help="Predictor columns")
    parser.add_argument("--outcomes", type=str, nargs="+", required=True, help="Outcome columns")
    
    args = parser.parse_args()
    
    df = pd.read_csv(args.input)
    results = run_correlation_analysis(df, args.predictors, args.outcomes)
    
    # Save results
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    results.to_json(args.output, orient="records", indent=2)
    print(f"Analysis results saved to {args.output}")

if __name__ == "__main__":
    main()
