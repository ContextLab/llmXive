import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.logging import setup_logger, log_bootstrap_result

# Configure logger
logger = setup_logger(__name__)

def load_correlation_data(results_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load correlation results from JSON or CSV.
    Expects data from T020a (correlation_results.csv or .json).
    """
    if results_path is None:
        results_path = PROJECT_ROOT / "data" / "processed" / "correlation_results.csv"
    
    if not results_path.exists():
        # Fallback to JSON if CSV doesn't exist
        json_path = results_path.with_suffix('.json')
        if not json_path.exists():
            raise FileNotFoundError(f"Correlation results not found at {results_path} or {json_path}")
        df = pd.read_json(json_path)
    else:
        df = pd.read_csv(results_path)
    
    # Ensure date column is datetime if present
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    return df

def run_bootstrap_resampling(
    data: pd.DataFrame,
    target_column: str,
    sunspot_column: str,
    n_iterations: int = 1000,
    block_size_days: int = 30,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform Moving Block Bootstrap (MBB) resampling to estimate confidence intervals
    for the maximum correlation coefficient.
    
    Args:
        data: DataFrame with time-series data.
        target_column: Column name for the target variable (e.g., He/p ratio).
        sunspot_column: Column name for sunspot numbers.
        n_iterations: Number of bootstrap iterations.
        block_size_days: Size of the block in days for MBB.
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary with bootstrap results (mean, std, CI, max_corr, etc.).
    """
    if seed is not None:
        np.random.seed(seed)
    
    if target_column not in data.columns or sunspot_column not in data.columns:
        raise ValueError(f"Columns {target_column} and/or {sunspot_column} not found in data.")
    
    # Remove NaNs
    valid_data = data[[target_column, sunspot_column]].dropna()
    if len(valid_data) < block_size_days:
        logger.warning(f"Data length ({len(valid_data)}) is less than block size ({block_size_days}). Adjusting block size.")
        block_size_days = max(1, len(valid_data) // 10)
    
    x = valid_data[target_column].values
    y = valid_data[sunspot_column].values
    n = len(x)
    
    # Calculate block size in indices (assuming daily data)
    # If data is not daily, we assume block_size_days maps to indices directly for simplicity
    # or we need a mapping. Assuming daily for now as per spec.
    block_size = block_size_days 
    
    num_blocks = int(np.ceil(n / block_size))
    bootstrap_max_corrs = []
    
    logger.info(f"Running MBB with {n_iterations} iterations, block_size={block_size}")
    
    for i in range(n_iterations):
        # Resample blocks
        indices = []
        while len(indices) < n:
            start_idx = np.random.randint(0, n - block_size + 1)
            indices.extend(range(start_idx, start_idx + block_size))
        
        # Truncate to original length
        indices = indices[:n]
        
        x_boot = x[indices]
        y_boot = y[indices]
        
        # Calculate correlation
        if len(np.unique(x_boot)) > 1 and len(np.unique(y_boot)) > 1:
            corr, _ = np.corrcoef(x_boot, y_boot)[0, 1], 0 # placeholder for p-value logic if needed
            if not np.isnan(corr):
                bootstrap_max_corrs.append(corr)
        else:
            # Degenerate case, skip or handle
            pass
    
    if not bootstrap_max_corrs:
        logger.error("Bootstrap resampling failed to generate valid correlations.")
        return {
            "mean": np.nan,
            "std": np.nan,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "width": np.nan,
            "status": "failed"
        }
    
    bootstrap_max_corrs = np.array(bootstrap_max_corrs)
    mean_corr = np.mean(bootstrap_max_corrs)
    std_corr = np.std(bootstrap_max_corrs)
    
    # 95% Confidence Interval
    ci_lower = np.percentile(bootstrap_max_corrs, 2.5)
    ci_upper = np.percentile(bootstrap_max_corrs, 97.5)
    width = ci_upper - ci_lower
    
    # Find max correlation in original data (for stability check)
    original_corr, _ = np.corrcoef(x, y)[0, 1], 0
    if np.isnan(original_corr): original_corr = 0
    
    stability_status = "stable"
    if abs(original_corr) > 0:
        stability_metric = width / abs(original_corr)
        if stability_metric > 0.5:
            stability_status = "unstable"
    
    result = {
        "mean": float(mean_corr),
        "std": float(std_corr),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "width": float(width),
        "original_max_corr": float(original_corr),
        "stability_status": stability_status,
        "block_size_days": block_size_days,
        "n_iterations": n_iterations,
        "status": "success"
    }
    
    log_bootstrap_result(
        f"Bootstrap completed for {target_column} vs {sunspot_column}. CI: [{ci_lower:.4f}, {ci_upper:.4f}]",
        result
    )
    
    return result

def save_bootstrap_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save bootstrap results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Bootstrap results saved to {output_path}")

def generate_bootstrap_summary(all_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Generate a summary DataFrame from multiple bootstrap runs."""
    summary_data = []
    for res in all_results:
        summary_data.append({
            "block_size_days": res.get("block_size_days"),
            "mean": res.get("mean"),
            "ci_lower": res.get("ci_lower"),
            "ci_upper": res.get("ci_upper"),
            "width": res.get("width"),
            "stability_status": res.get("stability_status"),
            "status": res.get("status")
        })
    return pd.DataFrame(summary_data)

def run_block_size_sensitivity_analysis(
    data: pd.DataFrame,
    target_column: str,
    sunspot_column: str,
    block_sizes: List[int] = [10, 20, 30, 40, 50],
    n_iterations: int = 1000,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Sensitivity analysis for MBB block size.
    
    Runs bootstrap for multiple block sizes and compares confidence interval widths.
    Flags if variation is > 10%.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "data" / "processed" / "bootstrap_block_sensitivity.json"
    
    logger.info(f"Starting block size sensitivity analysis for {target_column}")
    
    results = {}
    widths = []
    
    for bs in block_sizes:
        logger.info(f"Running bootstrap with block_size={bs}")
        res = run_bootstrap_resampling(
            data,
            target_column,
            sunspot_column,
            n_iterations=n_iterations,
            block_size_days=bs
        )
        results[str(bs)] = res
        if res["status"] == "success":
            widths.append(res["width"])
    
    # Analyze variation
    sensitivity_flag = "stable"
    if len(widths) >= 2:
        max_width = max(widths)
        min_width = min(widths)
        variation_pct = ((max_width - min_width) / min_width) * 100 if min_width > 0 else 0
        
        if variation_pct > 10:
            sensitivity_flag = "sensitive to block size"
            logger.warning(f"CI width variation is {variation_pct:.2f}% (>10%). Result flagged as sensitive.")
        else:
            logger.info(f"CI width variation is {variation_pct:.2f}%. Result is stable.")
    
    final_report = {
        "target_column": target_column,
        "sunspot_column": sunspot_column,
        "block_sizes_tested": block_sizes,
        "variation_threshold_percent": 10,
        "sensitivity_status": sensitivity_flag,
        "results": results
    }
    
    save_bootstrap_results(final_report, output_path)
    logger.info(f"Sensitivity analysis report saved to {output_path}")
    
    return final_report

def main():
    """
    Entry point for running the bootstrap block size sensitivity analysis.
    Reads from correlation_results.csv (or similar) and produces bootstrap_block_sensitivity.json.
    """
    logger.info("Starting bootstrap block size sensitivity analysis via main()")
    
    # Load data - assuming we have a unified timeseries or correlation results
    # For this analysis, we need the actual time series data to resample.
    # We will load the unified_timeseries.csv if available, or construct from correlation results if possible.
    # The task requires running on the correlation data. We assume the correlation data 
    # was derived from a time series. We need the raw time series for MBB.
    
    unified_path = PROJECT_ROOT / "data" / "processed" / "unified_timeseries.csv"
    
    if not unified_path.exists():
        logger.error(f"Unified timeseries not found at {unified_path}. Cannot run bootstrap.")
        sys.exit(1)
    
    df = pd.read_csv(unified_path)
    
    # We need to run this for He/p and Fe/p ratios.
    # Assuming columns 'he_p_ratio' and 'fe_p_ratio' exist, or calculate them if not.
    # If not present, we might need to calculate from helium_flux / proton_flux.
    
    target_columns = []
    if 'he_p_ratio' in df.columns:
        target_columns.append('he_p_ratio')
    if 'fe_p_ratio' in df.columns:
        target_columns.append('fe_p_ratio')
    
    # Fallback: calculate if columns missing
    if not target_columns:
        if 'helium_flux' in df.columns and 'proton_flux' in df.columns:
            df['he_p_ratio'] = df['helium_flux'] / df['proton_flux']
            target_columns.append('he_p_ratio')
        if 'iron_flux' in df.columns and 'proton_flux' in df.columns:
            df['fe_p_ratio'] = df['iron_flux'] / df['proton_flux']
            target_columns.append('fe_p_ratio')
    
    if not target_columns:
        logger.error("No valid target columns (He/p or Fe/p) found in unified timeseries.")
        sys.exit(1)
    
    sunspot_col = 'sunspot_number'
    if sunspot_col not in df.columns:
        logger.error(f"Sunspot column '{sunspot_col}' not found.")
        sys.exit(1)
    
    # Clean data for analysis (drop NaNs in ratios)
    clean_df = df.dropna(subset=target_columns + [sunspot_col])
    
    block_sizes = [10, 20, 30, 40, 50]
    n_iter = 1000
    
    all_reports = {}
    
    for col in target_columns:
        logger.info(f"Running sensitivity analysis for {col}")
        report = run_block_size_sensitivity_analysis(
            clean_df,
            col,
            sunspot_col,
            block_sizes=block_sizes,
            n_iterations=n_iter,
            output_path=PROJECT_ROOT / "data" / "processed" / f"bootstrap_block_sensitivity_{col}.json"
        )
        all_reports[col] = report
    
    # Save a combined report
    combined_path = PROJECT_ROOT / "data" / "processed" / "bootstrap_block_sensitivity.json"
    with open(combined_path, 'w') as f:
        json.dump(all_reports, f, indent=2)
    
    logger.info(f"All sensitivity analyses complete. Combined report at {combined_path}")

if __name__ == "__main__":
    main()