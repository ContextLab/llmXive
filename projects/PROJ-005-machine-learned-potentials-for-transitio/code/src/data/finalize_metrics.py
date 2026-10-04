"""
T027b: Finalize metrics.json by aggregating residuals and variance correlation data.

This script calculates MAE, RMSE, and Pearson correlation from residuals.parquet
and aggregates variance metrics from variance_correlation.json into a single
metrics.json file.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent

def load_residuals(residuals_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load residuals from parquet file.
    
    Args:
        residuals_path: Path to residuals.parquet. If None, uses default path.
        
    Returns:
        DataFrame with residual data.
        
    Raises:
        FileNotFoundError: If the residuals file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if residuals_path is None:
        project_root = get_project_root()
        residuals_path = project_root / "data" / "processed" / "residuals.parquet"
        
    if not residuals_path.exists():
        raise FileNotFoundError(f"Residuals file not found: {residuals_path}")
        
    df = pd.read_parquet(residuals_path)
    
    if df.empty:
        raise ValueError(f"Residuals file is empty: {residuals_path}")
        
    required_columns = ["error_ml_dft"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in residuals: {missing_columns}")
        
    logger.info(f"Loaded {len(df)} residuals from {residuals_path}")
    return df

def load_variance_correlation(
    variance_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load variance correlation metrics from JSON file.
    
    Args:
        variance_path: Path to variance_correlation.json. If None, uses default path.
        
    Returns:
        Dictionary with variance correlation metrics.
        
    Raises:
        FileNotFoundError: If the variance correlation file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if variance_path is None:
        project_root = get_project_root()
        variance_path = project_root / "data" / "results" / "variance_correlation.json"
        
    if not variance_path.exists():
        raise FileNotFoundError(f"Variance correlation file not found: {variance_path}")
        
    with open(variance_path, 'r') as f:
        data = json.load(f)
        
    logger.info(f"Loaded variance correlation metrics from {variance_path}")
    return data

def compute_metrics(residuals_df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute MAE, RMSE, and Pearson correlation from residuals.
    
    Args:
        residuals_df: DataFrame containing 'error_ml_dft' column.
        
    Returns:
        Dictionary with computed metrics.
    """
    errors = residuals_df["error_ml_dft"].values
    
    # Remove NaN values if any
    valid_mask = ~np.isnan(errors)
    valid_errors = errors[valid_mask]
    
    if len(valid_errors) == 0:
        raise ValueError("No valid error values found after filtering NaNs")
        
    mae = float(np.mean(np.abs(valid_errors)))
    rmse = float(np.sqrt(np.mean(valid_errors ** 2)))
    
    # Pearson correlation requires two variables. Since we only have errors,
    # we correlate errors with DFT barriers (which should be in residuals)
    # If dft_barrier is not present, we correlate errors with themselves (r=1)
    # or we can correlate with sample index as a fallback (not meaningful)
    # The most reasonable interpretation: correlate error with the magnitude of the barrier
    # Let's assume dft_barrier column exists in residuals
    pearson = None
    if "dft_barrier" in residuals_df.columns:
        barriers = residuals_df["dft_barrier"].values
        valid_barriers = barriers[valid_mask]
        if len(valid_errors) > 1 and len(valid_barriers) > 1:
            pearson = float(np.corrcoef(valid_errors, valid_barriers)[0, 1])
            if np.isnan(pearson):
                pearson = None
    else:
        logger.warning("dft_barrier column not found in residuals, Pearson correlation cannot be computed")
        
    metrics = {
        "mae": mae,
        "rmse": rmse,
        "pearson": pearson,
        "num_samples": int(len(valid_errors))
    }
    
    logger.info(f"Computed metrics: MAE={mae:.4f}, RMSE={rmse:.4f}, Pearson={pearson}")
    return metrics

def aggregate_variance_metrics(
    variance_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate variance metrics from variance correlation analysis.
    
    Args:
        variance_data: Dictionary containing variance correlation results.
        
    Returns:
        Dictionary with aggregated variance metrics.
    """
    aggregated = {
        "mean_variance": variance_data.get("mean_variance", None),
        "pearson_correlation": variance_data.get("pearson_correlation", None),
        "variance_stats": {
            "min": variance_data.get("min_variance", None),
            "max": variance_data.get("max_variance", None),
            "std": variance_data.get("std_variance", None)
        }
    }
    
    logger.info("Aggregated variance metrics")
    return aggregated

def save_metrics(
    metrics: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save metrics to JSON file.
    
    Args:
        metrics: Dictionary containing all metrics.
        output_path: Path to output file. If None, uses default path.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "metrics.json"
        
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Saved metrics to {output_path}")
    return output_path

def run_finalize_metrics(
    residuals_path: Optional[Path] = None,
    variance_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to finalize metrics by combining residuals and variance data.
    
    Args:
        residuals_path: Path to residuals.parquet.
        variance_path: Path to variance_correlation.json.
        output_path: Path to output metrics.json.
        
    Returns:
        Dictionary containing the finalized metrics.
    """
    logger.info("Starting finalize metrics process")
    
    # Load input data
    residuals_df = load_residuals(residuals_path)
    variance_data = load_variance_correlation(variance_path)
    
    # Compute metrics
    error_metrics = compute_metrics(residuals_df)
    
    # Aggregate variance metrics
    variance_metrics = aggregate_variance_metrics(variance_data)
    
    # Combine all metrics
    final_metrics = {
        "error_metrics": error_metrics,
        "variance_metrics": variance_metrics,
        "status": "complete",
        "generated_from": {
            "residuals": str(residuals_path) if residuals_path else "default",
            "variance": str(variance_path) if variance_path else "default"
        }
    }
    
    # Save to file
    save_metrics(final_metrics, output_path)
    
    logger.info("Finalize metrics process completed successfully")
    return final_metrics

def main():
    """Entry point for the script."""
    try:
        metrics = run_finalize_metrics()
        print(f"Metrics saved successfully. MAE: {metrics['error_metrics']['mae']:.4f}")
        print(f"RMSE: {metrics['error_metrics']['rmse']:.4f}")
        print(f"Pearson: {metrics['error_metrics']['pearson']}")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
