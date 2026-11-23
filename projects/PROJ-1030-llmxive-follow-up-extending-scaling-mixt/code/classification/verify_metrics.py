import json
import argparse
from pathlib import Path
import logging

def verify_metrics_file(metrics_path: str) -> bool:
    """
    Verify that the metrics file exists and contains the expected structure.
    
    Args:
        metrics_path: Path to the metrics JSON file
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not Path(metrics_path).exists():
        logging.error(f"Metrics file not found: {metrics_path}")
        return False
    
    try:
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        required_keys = ["model_metrics", "baseline_f1", "improvement_over_baseline"]
        for key in required_keys:
            if key not in metrics:
                logging.error(f"Missing key in metrics file: {key}")
                return False
        
        model_metrics = metrics["model_metrics"]
        required_model_keys = ["f1", "precision", "recall"]
        for key in required_model_keys:
            if key not in model_metrics:
                logging.error(f"Missing key in model_metrics: {key}")
                return False
        
        logging.info("Metrics file is valid.")
        return True
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in metrics file: {e}")
        return False
    except Exception as e:
        logging.error(f"Error verifying metrics file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Verify metrics file.")
    parser.add_argument("--metrics_path", type=str, default="data/processed/evaluation_metrics.json", help="Path to metrics JSON file")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Verify metrics
    is_valid = verify_metrics_file(args.metrics_path)
    
    if is_valid:
        print("Metrics file is valid.")
    else:
        print("Metrics file is invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()
