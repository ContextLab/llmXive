import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np
from scipy import stats

# Add code directory to path
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from config import METRICS_CSV_PATH, STATS_JSON_PATH
from logging_setup import setup_logging

def calculate_pearson_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate Pearson correlations for the specified metric pairs.
    Reads input from data/processed/metrics.csv (passed as df).
    Computes r and p-values for:
      - Entropy vs SA
      - Entropy vs QED
      - LZ vs SA
      - LZ vs QED
    """
    pairs = [
        ("entropy", "sa_score"),
        ("entropy", "qed"),
        ("lz_complexity", "sa_score"),
        ("lz_complexity", "qed")
    ]
    
    results = {}
    for x, y in pairs:
        if x in df.columns and y in df.columns:
            # Drop NaNs to ensure valid correlation calculation
            x_series = df[x].dropna()
            y_series = df[y].dropna()
            
            # Align indices after dropna to ensure pairs match
            common_idx = x_series.index.intersection(y_series.index)
            x_clean = x_series.loc[common_idx]
            y_clean = y_series.loc[common_idx]
            
            if len(x_clean) > 1:
                r, p = stats.pearsonr(x_clean, y_clean)
                results[f"{x}_vs_{y}"] = {
                    "r": float(r),
                    "p_value": float(p)
                }
            else:
                results[f"{x}_vs_{y}"] = {"r": None, "p_value": None}
        else:
            results[f"{x}_vs_{y}"] = {"r": None, "p_value": None}
    
    return results

def apply_multiple_comparison_correction(p_values: Dict[str, float]) -> Dict[str, float]:
    """
    Apply Bonferroni correction to p-values.
    """
    n = len(p_values)
    if n == 0:
        return {}
    corrected = {}
    for key, p in p_values.items():
        if p is not None:
            corrected[key] = min(p * n, 1.0)
        else:
            corrected[key] = None
    return corrected

def bootstrap_correlations(df: pd.DataFrame, n_iterations: int = 1000) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to estimate confidence intervals.
    """
    pairs = [
        ("entropy", "sa_score"),
        ("entropy", "qed"),
        ("lz_complexity", "sa_score"),
        ("lz_complexity", "qed")
    ]
    
    results = {}
    for x, y in pairs:
        if x not in df.columns or y not in df.columns:
            continue
        
        # Pre-clean data for speed
        x_series = df[x].dropna()
        y_series = df[y].dropna()
        common_idx = x_series.index.intersection(y_series.index)
        x_clean = x_series.loc[common_idx]
        y_clean = y_series.loc[common_idx]
        
        if len(x_clean) < 2:
            continue

        r_values = []
        n = len(x_clean)
        for _ in range(n_iterations):
            # Resample indices
            indices = np.random.choice(n, size=n, replace=True)
            sample_x = x_clean.iloc[indices].values
            sample_y = y_clean.iloc[indices].values
            
            try:
                r, _ = stats.pearsonr(sample_x, sample_y)
                r_values.append(r)
            except Exception:
                continue
        
        if not r_values:
            continue

        r_values = np.array(r_values)
        results[f"{x}_vs_{y}"] = {
            "mean_r": float(np.mean(r_values)),
            "ci_lower": float(np.percentile(r_values, 2.5)),
            "ci_upper": float(np.percentile(r_values, 97.5)),
            "std_dev": float(np.std(r_values))
        }
    
    return results

def main():
    """
    Main entry point for analysis.
    Reads from data/processed/metrics.csv and writes to reports/stats.json.
    Ensures 'associational' labeling is present in the output.
    """
    logger = setup_logging()
    logger.info("Starting analysis...")
    
    if not os.path.exists(METRICS_CSV_PATH):
        logger.error(f"Metrics file not found: {METRICS_CSV_PATH}")
        return False
    
    try:
        df = pd.read_csv(METRICS_CSV_PATH)
        logger.info(f"Loaded {len(df)} records for analysis from {METRICS_CSV_PATH}.")
    except Exception as e:
        logger.error(f"Failed to load metrics CSV: {e}")
        return False
    
    # Calculate correlations
    correlations = calculate_pearson_correlations(df)
    
    # Bootstrap
    bootstrap_results = bootstrap_correlations(df, n_iterations=1000)
    
    # Apply correction to p-values
    p_values = {k: v.get("p_value") for k, v in correlations.items() if isinstance(v, dict)}
    corrected_p = apply_multiple_comparison_correction(p_values)
    
    # Combine results
    output = {
        "study_type": "associational",
        "description": "Correlation analysis between molecular complexity metrics (Entropy, LZ) and drug-likeness metrics (SA, QED).",
        "pearson_correlations": correlations,
        "adjusted_p_values": corrected_p,
        "bootstrap_results": bootstrap_results,
        "sample_size": len(df)
    }
    
    # Ensure output directory exists
    stats_path = Path(STATS_JSON_PATH)
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    with open(STATS_JSON_PATH, "w") as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved analysis results to {STATS_JSON_PATH}")
    return True

if __name__ == "__main__":
    main()