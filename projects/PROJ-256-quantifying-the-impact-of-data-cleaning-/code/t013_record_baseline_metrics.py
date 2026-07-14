import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from analysis import run_baseline_analysis, save_json_file
from utils import setup_logging, compute_file_checksum
from config import get_config

logger = logging.getLogger(__name__)

def format_metric_value(value: Any, precision: int = 3) -> Any:
    """Format metric value with specified precision."""
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, precision)
    if isinstance(value, list):
        return [format_metric_value(v, precision) for v in value]
    if isinstance(value, dict):
        return {k: format_metric_value(v, precision) for k, v in value.items()}
    return value

def log_metrics_summary(metrics: Dict[str, Any]) -> None:
    """Log summary of baseline metrics."""
    logger.info("=" * 60)
    logger.info("BASELINE METRICS SUMMARY")
    logger.info("=" * 60)
    
    if "datasets" not in metrics:
        logger.warning("No datasets found in metrics")
        return
    
    for dataset in metrics["datasets"]:
        name = dataset.get("dataset_name", "unknown")
        n_rows = dataset.get("n_rows", 0)
        t_test = dataset.get("t_test", {})
        regression = dataset.get("regression", {})
        cohen_d = dataset.get("cohen_d")
        
        logger.info(f"Dataset: {name} (n={n_rows})")
        
        p_val = t_test.get("p_value")
        if p_val is not None:
            logger.info(f"  T-test p-value: {p_val:.6f}")
            ci_lower = t_test.get("ci_lower")
            ci_upper = t_test.get("ci_upper")
            if ci_lower is not None and ci_upper is not None:
                logger.info(f"  95% CI: [{ci_lower:.6f}, {ci_upper:.6f}]")
        
        r_sq = regression.get("r_squared")
        if r_sq is not None:
            logger.info(f"  Regression R²: {r_sq:.6f}")
        
        if cohen_d is not None:
            logger.info(f"  Cohen's d: {cohen_d:.6f}")
        
        logger.info("-" * 40)

def process_dataset_for_baseline(dataset_path: str, output_path: str) -> bool:
    """
    Process a single dataset for baseline metrics recording.
    
    Args:
        dataset_path: Path to the dataset CSV file
        output_path: Path to write the baseline_metrics.json
      
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing dataset: {dataset_path}")
    
    # Run baseline analysis
    config = get_config().to_dict()
    config["outcome_col"] = config.get("outcome_col", "outcome")
    config["group_col"] = config.get("group_col", "group")
    
    success = run_baseline_analysis(
        raw_dir=dataset_path,
        output_file=output_path,
        config=config
    )
    
    if not success:
        logger.error(f"Failed to analyze dataset: {dataset_path}")
        return False
    
    # Validate and format output
    try:
        with open(output_path, 'r') as f:
            metrics = json.load(f)
        
        # Validate p-values are in (0, 1)
        for dataset in metrics.get("datasets", []):
            t_test = dataset.get("t_test", {})
            p_val = t_test.get("p_value")
            if p_val is not None:
                if not (0 < p_val < 1):
                    logger.warning(f"P-value {p_val} out of range (0,1) for {dataset.get('dataset_name')}")
            
            # Validate CI bounds are finite
            ci_lower = t_test.get("ci_lower")
            ci_upper = t_test.get("ci_upper")
            if ci_lower is not None and ci_upper is not None:
                if not (np.isfinite(ci_lower) and np.isfinite(ci_upper)):
                    logger.warning(f"Non-finite CI bounds for {dataset.get('dataset_name')}")
        
        # Format with 3 decimal precision
        formatted_metrics = format_metric_value(metrics, precision=3)
        
        # Write formatted metrics
        with open(output_path, 'w') as f:
            json.dump(formatted_metrics, f, indent=2)
        
        # Compute checksum
        checksum = compute_file_checksum(output_path)
        logger.info(f"Saved baseline metrics to {output_path} (checksum: {checksum[:16]}...)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing metrics: {e}")
        return False

def main():
    """Main entry point for T013: Record baseline metrics."""
    setup_logging("INFO")
    
    config = get_config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("OUTPUT_PATH", "data/processed")
    output_file = os.path.join(output_file, "baseline_metrics.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    logger.info(f"Recording baseline metrics to {output_file}")
    logger.info(f"Source directory: {raw_dir}")
    
    # Check if raw data exists
    if not os.path.exists(raw_dir):
        logger.error(f"Raw data directory not found: {raw_dir}")
        # Try to create it and download if needed
        os.makedirs(raw_dir, exist_ok=True)
        logger.warning(f"Created empty directory: {raw_dir}")
        logger.warning("No datasets found. Please download datasets first (T011).")
        # Create empty metrics file
        empty_metrics = {
            "timestamp": datetime.now().isoformat(),
            "config": {"raw_dir": raw_dir},
            "datasets": [],
            "note": "No datasets found in raw directory"
        }
        save_json_file(empty_metrics, output_file)
        logger.info(f"Created empty baseline metrics file: {output_file}")
        return
    
    # Process all datasets
    success = run_baseline_analysis(
        raw_dir=raw_dir,
        output_file=output_file,
        config=config.to_dict()
    )
    
    if success:
        # Log summary
        with open(output_file, 'r') as f:
            metrics = json.load(f)
        log_metrics_summary(metrics)
        logger.info("T013 completed successfully")
    else:
        logger.error("T013 failed to process any datasets")
        sys.exit(1)

if __name__ == "__main__":
    main()
