import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logging_config import setup_logging

MODELS_DIR = Path("code/models")
METRICS_FILE = Path("data/processed/model_metrics.json")

def load_model_metrics() -> Optional[Dict[str, Any]]:
    """Load metrics from model files if they exist."""
    metrics = {}
    if not MODELS_DIR.exists():
        logging.warning("Models directory not found.")
        return None
    
    # Look for linear and rf metrics
    linear_path = MODELS_DIR / "linear_metrics.json"
    rf_path = MODELS_DIR / "rf_metrics.json"
    
    if linear_path.exists():
        with open(linear_path, 'r') as f:
            metrics['LinearRegression'] = json.load(f)
    if rf_path.exists():
        with open(rf_path, 'r') as f:
            metrics['RandomForest'] = json.load(f)
    
    if not metrics:
        logging.warning("No model metrics found.")
        return None
    
    return metrics

def aggregate_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate metrics into a single report."""
    report = {"models": metrics, "generated": True}
    return report

def main() -> int:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Generating model metrics...")
    
    metrics = load_model_metrics()
    if metrics is None:
        logger.warning("No metrics to generate. Creating empty report.")
        metrics = {}
    
    report = aggregate_metrics(metrics)
    
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Model metrics saved to {METRICS_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())