import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from code.config import Config

logger = logging.getLogger(__name__)

def load_metrics_from_csv(metrics_path: Path) -> List[Dict[str, Any]]:
    """
    Load metrics from CSV file.
    
    Args:
        metrics_path: Path to metrics CSV
        
    Returns:
        List of metric dictionaries
    """
    metrics = []
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                metrics.append(row)
    return metrics

def validate_metric_value(metric_name: str, value: float, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """
    Validate a metric value is within bounds.
    
    Args:
        metric_name: Metric name
        value: Metric value
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        True if valid, False otherwise
    """
    if min_val is not None and value < min_val:
        logger.error(f"{metric_name}={value} is below minimum {min_val}")
        return False
    if max_val is not None and value > max_val:
        logger.error(f"{metric_name}={value} is above maximum {max_val}")
        return False
    return True

def validate_metrics(metrics: List[Dict[str, Any]]) -> bool:
    """
    Validate all metrics.
    
    Args:
        metrics: List of metric dictionaries
        
    Returns:
        True if all valid, False otherwise
    """
    all_valid = True
    
    for metric in metrics:
        # Validate modularity (Q >= 0)
        if "modularity" in metric:
            val = float(metric["modularity"])
            if not validate_metric_value("modularity", val, min_val=0.0):
                all_valid = False
                
        # Validate efficiency (Eff >= 0)
        for eff_type in ["global_efficiency", "local_efficiency"]:
            if eff_type in metric:
                val = float(metric[eff_type])
                if not validate_metric_value(eff_type, val, min_val=0.0):
                    all_valid = False
                    
        # Check for NaN/Infinity
        for key, val in metric.items():
            try:
                v = float(val)
                if not (v == v): # NaN check
                    logger.error(f"{key} is NaN")
                    all_valid = False
                if abs(v) == float('inf'):
                    logger.error(f"{key} is Infinity")
                    all_valid = False
            except (ValueError, TypeError):
                pass
                
    return all_valid

def run_validation(config: Config) -> bool:
    """
    Run validation on network metrics.
    
    Args:
        config: Configuration object
        
    Returns:
        True if valid, False otherwise
    """
    metrics_path = config.NETWORK_METRICS_PATH
    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        return False
        
    metrics = load_metrics_from_csv(metrics_path)
    
    if not metrics:
        logger.warning("No metrics found to validate")
        return True
        
    is_valid = validate_metrics(metrics)
    
    if not is_valid:
        logger.critical("Metric validation failed. Some values are out of bounds.")
        return False
        
    logger.info("Metric validation successful.")
    return True

def main():
    """Main entry point."""
    config = Config()
    run_validation(config)

if __name__ == "__main__":
    main()