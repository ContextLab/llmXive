import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    return obj

def save_single_model_metrics(model_metrics: Dict[str, Any], output_path: Path) -> None:
    """Save metrics for a single model."""
    # Convert numpy types
    metrics = convert_numpy_types(model_metrics)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved model metrics to {output_path}")

def save_model_metrics(all_metrics: Dict[str, Dict[str, Any]], output_path: str) -> None:
    """
    Save metrics for all models.
    
    Args:
        all_metrics: Dictionary mapping model names to their metrics
        output_path: Path to save the metrics file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types
    metrics = convert_numpy_types(all_metrics)
    
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved all model metrics to {output_path}")

def main():
    """Main entry point for the metrics saving script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Save model metrics to JSON')
    parser.add_argument('--input', type=str, required=True, help='Input metrics file (JSON)')
    parser.add_argument('--output', type=str, required=True, help='Output metrics file')
    
    args = parser.parse_args()
    
    try:
        # Load input metrics
        with open(args.input, 'r') as f:
            metrics = json.load(f)
        
        # Save metrics
        save_model_metrics(metrics, args.output)
        
        logger.info("Metrics saved successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import sys
    main()
