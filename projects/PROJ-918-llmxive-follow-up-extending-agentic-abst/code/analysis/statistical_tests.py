import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Ensure logging is configured
try:
    from logging_config import setup_logging
    setup_logging()
except ImportError:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def load_simulation_results(path: str) -> pd.DataFrame:
    """
    Load simulation results from a JSON or Parquet file.
    Expects a file with columns including 'turn_number', 'token_usage', and condition labels.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {path}")

    if file_path.suffix == '.parquet':
        return pd.read_parquet(file_path)
    elif file_path.suffix == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    elif file_path.suffix == '.csv':
        return pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

def perform_mann_whitney_u_test(group_a: np.ndarray, group_b: np.ndarray) -> Dict[str, float]:
    """
    Perform Mann-Whitney U test to compare two independent samples.
    Returns statistic and p-value.
    """
    statistic, p_value = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "test": "mann_whitney_u"
    }

def perform_kolmogorov_smirnov_test(group_a: np.ndarray, group_b: np.ndarray) -> Dict[str, float]:
    """
    Perform Two-sample Kolmogorov-Smirnov test.
    Returns statistic and p-value.
    """
    statistic, p_value = stats.ks_2samp(group_a, group_b)
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "test": "kolmogorov_smirnov"
    }

def calculate_cohens_d(group_a: np.ndarray, group_b: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size.
    """
    n1, n2 = len(group_a), len(group_b)
    var1, var2 = np.var(group_a, ddof=1), np.var(group_b, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    d = (np.mean(group_a) - np.mean(group_b)) / pooled_std
    return float(d)

def calculate_variance_inflation_factor(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for a set of features.
    VIF measures how much the variance of an estimated regression coefficient increases 
    if your predictors are correlated.
    
    Args:
        df: DataFrame containing the features.
        features: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping feature name to VIF score.
    """
    if len(features) < 2:
        logger.warning("VIF calculation requires at least two features.")
        return {f: 0.0 for f in features}

    # Add constant for intercept if not present (statsmodels requires it)
    # We create a temporary dataframe with just the features of interest
    X = df[features].copy()
    
    # Handle any NaNs by dropping rows (VIF calculation requires complete cases)
    if X.isnull().any().any():
        logger.warning("NaNs detected in features for VIF calculation. Dropping incomplete rows.")
        X = X.dropna()
    
    if X.empty:
        raise ValueError("No valid data remaining for VIF calculation after dropping NaNs.")

    # Add constant column for intercept
    X_const = sm.add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_const.values, i)
            vif_data[col] = float(vif)
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = float('nan')
    
    return vif_data

def generate_statistical_report(results_path: str, output_path: str) -> Dict[str, Any]:
    """
    Generate a comprehensive statistical report including:
    1. Mann-Whitney U test
    2. Kolmogorov-Smirnov test
    3. Cohen's d
    4. Collinearity diagnostics (VIF)
    
    Args:
        results_path: Path to the simulation results file.
        output_path: Path to save the JSON report.
        
    Returns:
        Dictionary containing the report data.
    """
    logger.info(f"Loading simulation results from {results_path}")
    df = load_simulation_results(results_path)
    
    report = {
        "data_summary": {
            "total_rows": len(df),
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict()
        },
        "tests": {}
    }

    # Identify columns for token usage and condition if they exist
    # Assuming standard schema from previous tasks: 'token_usage' and 'condition' or 'label'
    token_col = None
    condition_col = None
    
    for col in df.columns:
        if 'token' in col.lower() or 'usage' in col.lower():
            token_col = col
        if 'condition' in col.lower() or 'label' in col.lower() or 'group' in col.lower():
            condition_col = col

    if token_col and condition_col and condition_col in df.columns:
        groups = df[condition_col].unique()
        if len(groups) >= 2:
            g1_name, g2_name = groups[0], groups[1]
            g1 = df[df[condition_col] == g1_name][token_col].dropna().values
            g2 = df[df[condition_col] == g2_name][token_col].dropna().values
            
            if len(g1) > 0 and len(g2) > 0:
                report["tests"]["mann_whitney_u"] = perform_mann_whitney_u_test(g1, g2)
                report["tests"]["kolmogorov_smirnov"] = perform_kolmogorov_smirnov_test(g1, g2)
                report["tests"]["cohens_d"] = {
                    "value": calculate_cohens_d(g1, g2),
                    "group_a": g1_name,
                    "group_b": g2_name
                }
                logger.info(f"Statistical tests completed for {token_col} vs {condition_col}")
        else:
            logger.warning(f"Only one group found in {condition_col}: {groups}")
    else:
        logger.warning(f"Could not identify token usage or condition columns. Available: {df.columns.tolist()}")

    # Collinearity Diagnostics (VIF)
    # Select numeric features that might be correlated (e.g., turn_number, token_usage, search_count)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Filter out the target/label if it's numeric but not a predictor
    # Heuristic: exclude columns with 'label', 'condition', 'id' in name
    predictor_candidates = [c for c in numeric_cols if not any(k in c.lower() for k in ['label', 'condition', 'id', 'group'])]
    
    if len(predictor_candidates) >= 2:
        logger.info(f"Calculating VIF for features: {predictor_candidates}")
        vif_results = calculate_variance_inflation_factor(df, predictor_candidates)
        report["collinearity_diagnostics"] = {
            "features_analyzed": predictor_candidates,
            "vif_scores": vif_results,
            "interpretation": {
                "low_collinearity": "< 5",
                "moderate_collinearity": "5 - 10",
                "high_collinearity": "> 10"
            }
        }
    else:
        logger.warning(f"Insufficient numeric predictors for VIF analysis. Found: {predictor_candidates}")
        report["collinearity_diagnostics"] = {
            "error": "Insufficient numeric predictors",
            "found": predictor_candidates
        }

    # Save report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Statistical report saved to {output_path}")
    return report

def plot_distribution_comparison(group_a: np.ndarray, group_b: np.ndarray, labels: Tuple[str, str], output_path: str):
    """
    Plot distribution comparison (histogram + KDE) for two groups.
    """
    plt.figure(figsize=(10, 6))
    sns.kdeplot(group_a, label=labels[0], fill=True, alpha=0.4)
    sns.kdeplot(group_b, label=labels[1], fill=True, alpha=0.4)
    plt.title("Distribution Comparison")
    plt.xlabel("Value")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file)
    plt.close()
    logger.info(f"Distribution plot saved to {output_path}")

def main():
    """
    Main entry point for statistical analysis.
    """
    # Default paths can be overridden by environment or config
    results_path = os.getenv("SIMULATION_RESULTS_PATH", "data/processed/simulation_results.parquet")
    report_path = os.getenv("STATISTICAL_REPORT_PATH", "data/results/statistical_report.json")
    
    if not os.path.exists(results_path):
        logger.error(f"Input file not found: {results_path}")
        sys.exit(1)
    
    try:
        generate_statistical_report(results_path, report_path)
        logger.info("Statistical analysis completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()