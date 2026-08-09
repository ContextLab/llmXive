import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from utils.config import get_config, set_seed
from diagnostics.collinearity import load_cleaned_data

def calculate_metrics_at_cutoff(
    df: pd.DataFrame,
    cutoff: float,
    target_col: str = "resolution_time_hours",
    predictor_col: str = "language",
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform a statistical test (Kruskal-Wallis) at a specific significance cutoff.
    
    This function groups data by predictor, performs the test, and returns whether
    the result is significant at the given cutoff.
    
    Returns:
        Dict with 'significant' (bool), 'statistic' (float), 'p_value' (float)
    """
    set_seed(seed)
    
    # Group by predictor
    groups = [group[target_col].values for name, group in df.groupby(predictor_col)]
    
    if len(groups) < 2:
        return {
            "significant": False,
            "statistic": 0.0,
            "p_value": 1.0,
            "error": "Insufficient groups for testing"
        }
    
    # Perform Kruskal-Wallis test
    try:
        statistic, p_value = stats.kruskal(*groups)
        significant = p_value < cutoff
        
        return {
            "significant": significant,
            "statistic": float(statistic),
            "p_value": float(p_value)
        }
    except Exception as e:
        logging.warning(f"Test failed at cutoff {cutoff}: {e}")
        return {
            "significant": False,
            "statistic": 0.0,
            "p_value": 1.0,
            "error": str(e)
        }

def run_parametric_bootstrap(
    df: pd.DataFrame,
    cutoff: float,
    n_resamples: int = 1000,
    target_col: str = "resolution_time_hours",
    predictor_col: str = "language",
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run parametric bootstrap to estimate stability of significance at a given cutoff.
    
    Parametric bootstrap here involves resampling the data with replacement (bootstrapping)
    and re-running the statistical test for each resample to see how often the result
    remains significant.
    
    Args:
        df: Input dataframe
        cutoff: Significance threshold
        n_resamples: Number of bootstrap resamples
        target_col: Column name for the outcome variable
        predictor_col: Column name for the grouping variable
        seed: Random seed for reproducibility
        
    Returns:
        Dict with stability proportion and raw p-values from resamples
    """
    set_seed(seed)
    
    logging.info(f"Running parametric bootstrap for cutoff {cutoff} with {n_resamples} resamples")
    
    significant_count = 0
    p_values = []
    
    n_samples = len(df)
    
    for i in range(n_resamples):
        # Bootstrap resample (sample with replacement)
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        resampled_df = df.iloc[indices].reset_index(drop=True)
        
        # Run test on resampled data
        result = calculate_metrics_at_cutoff(
            resampled_df, 
            cutoff=cutoff, 
            target_col=target_col, 
            predictor_col=predictor_col,
            seed=seed + i
        )
        
        if "error" not in result:
            p_values.append(result["p_value"])
            if result["significant"]:
                significant_count += 1
    
    stability_proportion = significant_count / n_resamples
    
    return {
        "cutoff": cutoff,
        "n_resamples": n_resamples,
        "significant_count": significant_count,
        "stability_proportion": float(stability_proportion),
        "p_values_sample": p_values[:10] if len(p_values) >= 10 else p_values, # Store first 10 for inspection
        "mean_p_value": float(np.mean(p_values)) if p_values else None
    }

def run_sensitivity_analysis(
    df: pd.DataFrame,
    cutoffs: List[float] = [0.01, 0.05, 0.1],
    n_resamples: int = 1000,
    target_col: str = "resolution_time_hours",
    predictor_col: str = "language",
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping across multiple cutoffs.
    
    Args:
        df: Cleaned dataset
        cutoffs: List of significance thresholds to test
        n_resamples: Number of bootstrap resamples per cutoff
        target_col: Outcome variable column
        predictor_col: Predictor variable column
        seed: Random seed
        
    Returns:
        Dictionary containing results for each cutoff
    """
    set_seed(seed)
    
    results = {
        "analysis_type": "parametric_bootstrap_sensitivity",
        "cutoffs_tested": cutoffs,
        "n_resamples_per_cutoff": n_resamples,
        "target_variable": target_col,
        "predictor_variable": predictor_col,
        "seed": seed,
        "results_by_cutoff": []
    }
    
    logging.info(f"Starting sensitivity analysis with cutoffs: {cutoffs}")
    
    for cutoff in cutoffs:
        logging.info(f"Processing cutoff: {cutoff}")
        bootstrap_result = run_parametric_bootstrap(
            df,
            cutoff=cutoff,
            n_resamples=n_resamples,
            target_col=target_col,
            predictor_col=predictor_col,
            seed=seed
        )
        
        results["results_by_cutoff"].append(bootstrap_result)
    
    # Add summary
    summary = []
    for res in results["results_by_cutoff"]:
        summary.append({
            "cutoff": res["cutoff"],
            "stability_proportion": res["stability_proportion"],
            "interpretation": f"Stable at {res['stability_proportion']*100:.1f}% of resamples"
        })
    
    results["summary"] = summary
    
    return results

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save sensitivity analysis results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    logging.info(f"Results saved to {output_path}")

def main() -> int:
    """Main entry point for sensitivity analysis task."""
    config = get_config()
    
    # Paths
    data_path = Path(config.get_path("cleaned_data"))
    output_path = Path(config.get_path("sensitivity_results"))
    
    if not data_path.exists():
        logging.error(f"Cleaned data not found at {data_path}")
        return 1
    
    # Load data
    logging.info(f"Loading cleaned data from {data_path}")
    df = load_cleaned_data(data_path)
    
    if df is None or df.empty:
        logging.error("Failed to load data or data is empty")
        return 1
    
    # Define parameters per FR-007
    cutoffs = [0.01, 0.05, 0.1]
    n_resamples = 1000 # Fixed seed and resample count for reproducibility
    seed = 42
    
    # Run analysis
    results = run_sensitivity_analysis(
        df,
        cutoffs=cutoffs,
        n_resamples=n_resamples,
        seed=seed
    )
    
    # Save results
    save_results(results, output_path)
    
    # Print summary to console
    print("\n--- Sensitivity Analysis Summary ---")
    for item in results["summary"]:
        print(f"Cutoff {item['cutoff']}: Stability Proportion = {item['stability_proportion']:.4f} ({item['interpretation']})")
    print("------------------------------------\n")
    
    return 0

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    sys.exit(main())
