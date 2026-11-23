"""
Task T037: Verify hold-out R² score against the 95th percentile threshold
and record result in data/processed/model_significance.json.

This script loads the model results from T030/T036, the null threshold from T031,
compares the hold-out R² score, and saves a JSON report.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports if running from code/
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import setup_logging, get_logger
from config import get_config

def main():
    # Setup logging
    log_path = Path("data/processed/run.log")
    logger = setup_logging(log_file=log_path)
    logger.info("Starting T037: Model Significance Verification")

    config = get_config()
    base_dir = Path(config.get("BASE_DIR", Path(__file__).parent.parent))
    processed_dir = base_dir / "data" / "processed"
    models_dir = base_dir / "data" / "models"

    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Paths for input artifacts
    null_threshold_path = processed_dir / "null_threshold.json"
    # The model results are saved by T036/T030. We expect a file containing the metrics.
    # Based on T036, we look for model metrics or a specific results file.
    # Assuming the main pipeline saves metrics to model_metrics.json or similar.
    # We will try to load the specific output from the modeling pipeline.
    # T036 saves artifacts to data/models. T031 saves threshold to data/processed.
    # T030/T036 likely produce a summary of the run.
    # Let's assume the main run saves a 'model_results.json' or we load from the saved model pickle's metadata.
    # However, the task specifically says "Verify hold-out R² score against the 95th percentile threshold (from T031)".
    # We need the hold-out R² score.
    
    # Check if null threshold exists (from T031)
    if not null_threshold_path.exists():
        logger.error(f"Required artifact missing: {null_threshold_path}. T031 must be completed.")
        raise FileNotFoundError(f"Null threshold file not found: {null_threshold_path}")

    with open(null_threshold_path, 'r') as f:
        null_data = json.load(f)
    
    threshold_95 = null_data.get("threshold_95_percentile")
    if threshold_95 is None:
        logger.error("Threshold 95th percentile not found in null_threshold.json")
        raise ValueError("Invalid null_threshold.json format")
    
    logger.info(f"Loaded 95th percentile threshold: {threshold_95}")

    # Locate the hold-out R² score
    # T036 saves model artifacts. T030/T031/T032/T033 logic usually outputs a summary.
    # We assume the modeling pipeline saved a summary file 'model_performance.json' or similar.
    # If not, we might need to load the model and re-evaluate, but T036 implies artifacts are saved.
    # Let's look for a standard metrics file saved by the pipeline.
    metrics_path = processed_dir / "model_metrics.json"
    
    if not metrics_path.exists():
        # Fallback: try to find any json in models dir that might have the score
        # Or raise error if strictly required by spec
        logger.warning(f"Metrics file {metrics_path} not found. Attempting to locate model results...")
        # If the pipeline saved to models_dir, we might need to load the model and predict on a held-out set.
        # However, T036 says "Save model artifacts...". T030 says "Nested CV".
        # The hold-out score usually comes from the outer loop or a specific test set.
        # Assuming the pipeline saved the final R² to a known location or we must load the model.
        # For this implementation, we assume the pipeline produced 'model_metrics.json' in processed_dir.
        # If T030/T036 didn't save it there, we might need to reconstruct or error.
        # Given the constraints, we assume the previous steps saved the metric.
        raise FileNotFoundError(f"Model metrics file not found: {metrics_path}. Ensure T030/T036 saved results.")

    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    hold_out_r2 = metrics.get("hold_out_r2")
    if hold_out_r2 is None:
        logger.error("Hold-out R² score not found in model metrics.")
        raise ValueError("Missing hold_out_r2 in model_metrics.json")
    
    logger.info(f"Hold-out R² score: {hold_out_r2}")

    # Perform verification
    is_significant = hold_out_r2 > threshold_95
    
    result = {
        "task_id": "T037",
        "hold_out_r2": hold_out_r2,
        "threshold_95_percentile": threshold_95,
        "is_significant": is_significant,
        "interpretation": "Model performance exceeds 95% of null distribution" if is_significant else "Model performance does not exceed 95% of null distribution",
        "timestamp": str(Path(__file__).parent.parent / "data" / "processed" / "model_significance.json") # Just a placeholder for timestamp logic if needed
    }

    output_path = processed_dir / "model_significance.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Verification complete. Result saved to {output_path}")
    logger.info(f"Significance: {is_significant}")

    return result

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Verification failed")
        sys.exit(1)