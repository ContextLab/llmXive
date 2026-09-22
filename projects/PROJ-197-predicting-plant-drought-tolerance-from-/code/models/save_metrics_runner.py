"""
Runner script to aggregate all model metrics, comparison results, and validation
logs into a single JSON file at data/logs/metrics.json for reproducibility.

This implements T030: Ensure all metrics and logs are written to data/logs/metrics.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
from config import get_config

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.metrics_logger import log_model_result, log_validation_result, log_comparison_report
from utils.logging import DataPipelineLog

def aggregate_metrics():
    """
    Collects all metrics from previous steps and writes them to data/logs/metrics.json.
    
    This function:
    1. Loads the metrics saved by evaluate.py (save_metrics)
    2. Loads the comparison report from compare.py
    3. Loads validation results
    4. Aggregates everything into a single JSON structure
    5. Writes to data/logs/metrics.json
    """
    config = get_config()
    metrics_path = Path(config['paths']['metrics_output'])
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = DataPipelineLog(config)
    logger.log_event("metrics_aggregation", "Starting metrics aggregation")
    
    aggregated_data = {
        "metadata": {
            "project": "PROJ-197-predicting-plant-drought-tolerance-from-",
            "task": "T030",
            "description": "Aggregated metrics for reproducibility",
            "config": {
                "random_seed": config.get('random_seed', 42),
                "species_count": config.get('species_list', []) and len(config.get('species_list', [])) or 0
            }
        },
        "model_metrics": {},
        "validation_results": {},
        "comparison_results": {},
        "pipeline_logs": []
    }
    
    # 1. Load model metrics from evaluate.py output
    evaluate_metrics_path = Path(config['paths']['processed_data']) / "model_metrics.json"
    if evaluate_metrics_path.exists():
        with open(evaluate_metrics_path, 'r') as f:
            aggregated_data["model_metrics"] = json.load(f)
        logger.log_event("metrics_aggregation", f"Loaded model metrics from {evaluate_metrics_path}")
    else:
        logger.log_event("metrics_aggregation", f"Warning: Model metrics file not found at {evaluate_metrics_path}", level="WARNING")
    
    # 2. Load comparison results from compare.py output
    comparison_path = Path(config['paths']['processed_data']) / "comparison_results.json"
    if comparison_path.exists():
        with open(comparison_path, 'r') as f:
            aggregated_data["comparison_results"] = json.load(f)
        logger.log_event("metrics_aggregation", f"Loaded comparison results from {comparison_path}")
    else:
        logger.log_event("metrics_aggregation", f"Warning: Comparison results file not found at {comparison_path}", level="WARNING")
        
    # 3. Load validation results
    validation_path = Path(config['paths']['processed_data']) / "validation_results.json"
    if validation_path.exists():
        with open(validation_path, 'r') as f:
            aggregated_data["validation_results"] = json.load(f)
        logger.log_event("metrics_aggregation", f"Loaded validation results from {validation_path}")
    else:
        logger.log_event("metrics_aggregation", f"Warning: Validation results file not found at {validation_path}", level="WARNING")
    
    # 4. Write the aggregated metrics to the final location
    with open(metrics_path, 'w') as f:
        json.dump(aggregated_data, f, indent=2, default=str)
    
    logger.log_event("metrics_aggregation", f"Successfully wrote aggregated metrics to {metrics_path}")
    return metrics_path

def main():
    """Main entry point for the metrics aggregation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        metrics_path = aggregate_metrics()
        logging.info(f"Metrics aggregation complete. Output: {metrics_path}")
        
        # Verify the file exists and is readable
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                data = json.load(f)
                logging.info(f"Aggregated metrics contains keys: {list(data.keys())}")
                logging.info(f"Model metrics keys: {list(data.get('model_metrics', {}).keys())}")
        else:
            logging.error(f"Failed to create metrics file at {metrics_path}")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Error during metrics aggregation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()