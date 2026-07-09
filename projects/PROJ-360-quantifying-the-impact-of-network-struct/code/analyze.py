import os
import json
import logging
import csv
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple
import statistics

import numpy as np
from scipy import stats

# Local imports
from config import get_config

def setup_analysis_logger() -> logging.Logger:
    """Set up the logger for analysis tasks."""
    logger = logging.getLogger("analysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_metrics_csv() -> List[Dict[str, Any]]:
    """Load metrics from data/processed/metrics.csv."""
    metrics_path = Path("data/processed/metrics.csv")
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}")
    
    data = []
    with open(metrics_path, 'r', newline='', encoding='utf-8') as f:
        # Skip comment lines if present (e.g., # DIAGNOSTICS...)
        lines = f.readlines()
        content_lines = [l for l in lines if not l.strip().startswith('#')]
        
        if not content_lines:
            raise ValueError("Metrics file is empty or contains only comments.")
        
        reader = csv.DictReader(content_lines)
        for row in reader:
            data.append(row)
    return data

def get_network_metrics() -> List[str]:
    """Return the list of network metric column names."""
    return ["average_degree", "average_shortest_path", "clustering_coefficient"]

def get_thermal_conductivity_col() -> str:
    """Return the column name for thermal conductivity."""
    return "thermal_conductivity_scalar"

def calculate_vif(df: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for network metrics.
    Input: List of dicts from metrics.csv.
    Output: Dict mapping metric name to VIF value.
    """
    # Implementation deferred to T020. 
    # Placeholder raises NotImplementedError to prevent silent failure if called early.
    raise NotImplementedError("VIF calculation is implemented in T020.")

def log_vif_results(vif_values: Dict[str, float], logger: logging.Logger) -> None:
    """Log VIF results to power_analysis.log."""
    # Implementation deferred to T020/T021.
    pass

def compute_correlations(data: List[Dict[str, Any]], logger: logging.Logger) -> Dict[str, Any]:
    """
    Compute Pearson and Spearman correlations between network metrics and thermal conductivity.
    
    Returns a dictionary structure suitable for JSON serialization.
    """
    metrics_cols = get_network_metrics()
    target_col = get_thermal_conductivity_col()
    
    # Extract numeric vectors
    X = {col: [] for col in metrics_cols}
    Y = []
    
    for row in data:
        for col in metrics_cols:
            try:
                val = float(row[col])
                if np.isnan(val):
                    val = np.nan
                X[col].append(val)
            except (ValueError, TypeError):
                X[col].append(np.nan)
        try:
            Y.append(float(row[target_col]))
        except (ValueError, TypeError):
            Y.append(np.nan)
    
    # Filter out rows where target or any metric is NaN for correlation
    # We need to align indices. Since we built lists, we can zip and filter.
    valid_indices = []
    for i in range(len(Y)):
        if not np.isnan(Y[i]):
            valid = True
            for col in metrics_cols:
                if np.isnan(X[col][i]):
                    valid = False
                    break
            if valid:
                valid_indices.append(i)
    
    logger.info(f"Using {len(valid_indices)} valid samples for correlation analysis.")
    
    results = {}
    for col in metrics_cols:
        x_vals = [X[col][i] for i in valid_indices]
        y_vals = [Y[i] for i in valid_indices]
        
        if len(x_vals) < 2:
            logger.warning(f"Not enough data for {col}")
            results[col] = {"pearson_r": None, "pearson_p": None, "spearman_r": None, "spearman_p": None}
            continue

        # Pearson
        try:
            p_r, p_p = stats.pearsonr(x_vals, y_vals)
        except Exception as e:
            logger.error(f"Pearson correlation failed for {col}: {e}")
            p_r, p_p = None, None

        # Spearman
        try:
            s_r, s_p = stats.spearmanr(x_vals, y_vals)
        except Exception as e:
            logger.error(f"Spearman correlation failed for {col}: {e}")
            s_r, s_p = None, None

        results[col] = {
            "pearson_r": float(p_r) if p_r is not None else None,
            "pearson_p": float(p_p) if p_p is not None else None,
            "spearman_r": float(s_r) if s_r is not None else None,
            "spearman_p": float(s_p) if s_p is not None else None
        }
    
    return results

def apply_bonferroni_correction(correlations: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to the p-values of the correlation tests.
    
    Args:
        correlations: Output from compute_correlations.
        alpha: Family-wise error rate (default 0.05).
    
    Returns:
        Updated correlations dict with 'bonferroni_p' and 'is_significant' keys.
    """
    n_tests = len(correlations)
    if n_tests == 0:
        return correlations

    adjusted_alpha = alpha / n_tests
    logger = logging.getLogger("analysis")
    logger.info(f"Applying Bonferroni correction: {n_tests} tests, adjusted alpha = {adjusted_alpha:.6f}")

    for metric, values in correlations.items():
        p_pearson = values.get("pearson_p")
        p_spearman = values.get("spearman_p")
        
        if p_pearson is not None:
            corrected_p = min(p_pearson * n_tests, 1.0)
            values["bonferroni_p_pearson"] = corrected_p
            values["is_significant_pearson"] = corrected_p < alpha
        
        if p_spearman is not None:
            corrected_p = min(p_spearman * n_tests, 1.0)
            values["bonferroni_p_spearman"] = corrected_p
            values["is_significant_spearman"] = corrected_p < alpha
    
    return correlations

def run_kfold_cross_validation() -> None:
    """Placeholder for T023. Implementation deferred."""
    raise NotImplementedError("K-fold cross-validation is implemented in T023.")

def main():
    """
    Main entry point for analysis tasks.
    Specifically handles T016 (Correlations) and T017 (Bonferroni Correction).
    """
    logger = setup_analysis_logger()
    logger.info("Starting analysis pipeline (T016/T017).")

    try:
        data = load_metrics_csv()
        logger.info(f"Loaded {len(data)} rows from metrics.csv.")
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    # T016: Compute correlations
    correlations = compute_correlations(data, logger)
    
    # Save raw correlations
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    output_path = results_dir / "correlations.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(correlations, f, indent=2)
    logger.info(f"Saved raw correlations to {output_path}")

    # T017: Apply Bonferroni correction
    corrected_correlations = apply_bonferroni_correction(correlations, alpha=0.05)
    
    # Save corrected results (overwrite or append? Spec implies storing results in correlations.json)
    # We will update the existing file with the corrected values.
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(corrected_correlations, f, indent=2)
    logger.info(f"Saved Bonferroni-corrected correlations to {output_path}")
    
    # Log summary
    logger.info("Bonferroni correction completed.")
    for metric, values in corrected_correlations.items():
        sig_pearson = values.get("is_significant_pearson", False)
        sig_spearman = values.get("is_significant_spearman", False)
        logger.info(f"{metric}: Pearson sig={sig_pearson}, Spearman sig={sig_spearman}")

if __name__ == "__main__":
    main()