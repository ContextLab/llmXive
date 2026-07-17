"""
Module: code/eval/scale_analysis.py
Task: T027a - Pre-check: Calculate mean SASA of the dataset and log scale.

This script performs a pre-check on the processed dataset to determine the
scale of the target variable (SASA). It calculates the mean SASA and logs
a warning if the mean is significantly larger than the absolute thresholds
{0.01, 0.05, 0.1} Å², documenting the potential for low success rates.

It writes the analysis results to results/reports/scale_analysis.json
to be consumed by the sensitivity analysis report (T030).
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

from utils.logging import setup_logging, get_logger
from utils.config import get_data_dir, get_results_dir

def load_processed_data_stats(data_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Loads the processed dataset statistics from the expected location.
    We expect the preprocessing step (T014/T017) to have generated a 
    statistics file or we read directly from the processed parquet/csv if available.
    
    For this task, we assume the processed data is in `data/processed/processed_molecules.parquet`
    or a similar summary file. If not, we attempt to load the main processed file.
    """
    processed_path = data_dir / "processed" / "processed_molecules.parquet"
    stats_path = data_dir / "processed" / "dataset_statistics.json"
    
    logger = get_logger(__name__)
    
    # Try to load pre-calculated stats if available
    if stats_path.exists():
        try:
            with open(stats_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load pre-calculated stats: {e}. Attempting direct read.")
    
    # Fallback: Try to load the parquet file directly if pandas is available
    # This ensures we don't fail if the stats file wasn't generated yet but data is.
    if processed_path.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(processed_path)
            if 'sasa' in df.columns:
                return {
                    "mean_sasa": float(df['sasa'].mean()),
                    "std_sasa": float(df['sasa'].std()),
                    "min_sasa": float(df['sasa'].min()),
                    "max_sasa": float(df['sasa'].max()),
                    "count": int(len(df)),
                    "source": "direct_parquet_read"
                }
            else:
                logger.error(f"Column 'sasa' not found in {processed_path}. Columns: {df.columns.tolist()}")
                return None
        except ImportError:
            logger.error("Pandas not available to read parquet fallback.")
            return None
        except Exception as e:
            logger.error(f"Failed to read parquet file: {e}")
            return None
    
    logger.error(f"Processed data not found at {processed_path} and stats not at {stats_path}")
    return None

def analyze_sasa_scale(data_dir: Path, results_dir: Path) -> Dict[str, Any]:
    """
    Analyzes the scale of SASA values in the dataset.
    
    Returns a dictionary containing:
    - mean_sasa: The calculated mean
    - scale_warning: Boolean indicating if mean >> 0.1
    - justification: Text explaining the threshold choice relative to scale
    - raw_stats: The raw statistics loaded
    """
    logger = get_logger(__name__)
    logger.info("Starting SASA scale analysis (Task T027a)...")
    
    stats = load_processed_data_stats(data_dir)
    
    if stats is None:
        logger.error("Could not load dataset statistics. Aborting analysis.")
        return {
            "status": "failed",
            "reason": "Could not load dataset statistics"
        }
    
    mean_sasa = stats.get("mean_sasa")
    if mean_sasa is None:
        logger.error("Mean SASA not found in loaded statistics.")
        return {
            "status": "failed",
            "reason": "Mean SASA not found in statistics"
        }
    
    logger.info(f"Dataset Mean SASA: {mean_sasa:.4f} Å²")
    logger.info(f"Dataset Std SASA: {stats.get('std_sasa', 'N/A')} Å²")
    
    # Thresholds defined in FR-006
    thresholds = [0.01, 0.05, 0.1]
    threshold_scale = 0.1
    
    # Check if mean is significantly larger than the largest threshold
    # "Significantly" here means > 10x the largest threshold (0.1) or simply >> 0.1
    # Given typical molecular SASA (e.g., benzene ~100 Å², larger molecules > 500 Å²),
    # the mean will almost certainly be >> 0.1.
    
    is_scale_mismatch = mean_sasa > (threshold_scale * 10) # 1.0 Å²
    
    warning_msg = ""
    justification = ""
    
    if is_scale_mismatch:
        warning_msg = (
            f"WARNING: Mean SASA ({mean_sasa:.4f} Å²) is significantly larger than "
            f"the absolute thresholds {thresholds}. "
            f"Success rates for thresholds {thresholds} may be effectively zero (deferred) "
            f"unless the metric is interpreted as relative error or the thresholds are scaled."
        )
        justification = (
            f"The selected absolute thresholds {{0.01, 0.05, 0.1}} Å² are orders of magnitude "
            f"smaller than the mean molecular surface area ({mean_sasa:.4f} Å²). "
            f"Consequently, achieving an MAE < 0.1 Å² is physically unrealistic for most "
            f"molecules in this dataset. This scale mismatch justifies the decision to "
            f"report success rates as 'deferred' or to interpret these thresholds as "
            f"relative error targets in the final sensitivity report (FR-006)."
        )
        logger.warning(warning_msg)
    else:
        justification = (
            f"The mean SASA ({mean_sasa:.4f} Å²) is within a comparable range to the "
            f"selected absolute thresholds. Absolute error metrics are appropriate."
        )
        logger.info("Scale analysis passed. Thresholds are appropriate for absolute error.")
    
    result = {
        "status": "success",
        "mean_sasa": mean_sasa,
        "std_sasa": stats.get("std_sasa"),
        "min_sasa": stats.get("min_sasa"),
        "max_sasa": stats.get("max_sasa"),
        "count": stats.get("count"),
        "thresholds_analyzed": thresholds,
        "is_scale_mismatch": is_scale_mismatch,
        "warning": warning_msg if is_scale_mismatch else None,
        "justification": justification
    }
    
    # Save report
    report_path = results_dir / "reports" / "scale_analysis.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Scale analysis report saved to {report_path}")
    return result

def main():
    setup_logging()
    logger = get_logger(__name__)
    
    data_dir = get_data_dir()
    results_dir = get_results_dir()
    
    result = analyze_sasa_scale(data_dir, results_dir)
    
    if result["status"] == "failed":
        logger.error(f"Analysis failed: {result.get('reason')}")
        sys.exit(1)
    
    logger.info("T027a Pre-check completed successfully.")
    return result

if __name__ == "__main__":
    main()