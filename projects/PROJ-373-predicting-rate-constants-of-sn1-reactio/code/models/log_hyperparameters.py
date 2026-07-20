import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Import from local project structure
from config import TrainingConfig, ensure_dirs

def setup_logging() -> logging.Logger:
    """Configure logging for the hyperparameter logging script."""
    logger = logging.getLogger("hyperparameter_log")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_hyperparameter_log(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load the hyperparameter search log from the training stage.
    Expects a JSON file where each entry contains config and metrics.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Hyperparameter log not found at {log_path}")
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of results in {log_path}, got {type(data)}")
    
    return data

def format_hyperparameter_entry(entry: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Extract and format a single hyperparameter entry into the required CSV row format.
    
    Expected input structure (from train.py):
    {
        "config_id": int,
        "config": {
            "learning_rate": float,
            "hidden_dim": int,
            "dropout": float,
            ...
        },
        "metrics": {
            "r2_val": float,
            "mae_val": float,
            ...
        }
    }
    """
    config = entry.get("config", {})
    metrics = entry.get("metrics", {})
    
    return {
        "config_id": entry.get("config_id", index),
        "learning_rate": config.get("learning_rate", 0.0),
        "hidden_dim": config.get("hidden_dim", 0),
        "dropout": config.get("dropout", 0.0),
        "r2_val": metrics.get("r2_val", 0.0),
        "mae_val": metrics.get("mae_val", 0.0)
    }

def generate_hyperparameter_log(
    results: List[Dict[str, Any]], 
    output_path: Path, 
    top_n: int = 10
) -> None:
    """
    Generate a CSV file with the top N hyperparameter configurations based on validation R².
    
    Args:
        results: List of raw result dictionaries from training.
        output_path: Path where the CSV will be saved.
        top_n: Number of top configurations to include.
    """
    # Sort by validation R² descending
    sorted_results = sorted(results, key=lambda x: x.get("metrics", {}).get("r2_val", -float('inf')), reverse=True)
    
    # Select top N
    top_results = sorted_results[:top_n]
    
    # Format entries
    formatted_rows = [format_hyperparameter_entry(row, i) for i, row in enumerate(top_results)]
    
    # Write to CSV
    os.makedirs(output_path.parent, exist_ok=True)
    fieldnames = ["config_id", "learning_rate", "hidden_dim", "dropout", "r2_val", "mae_val"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(formatted_rows)
    
    logging.info(f"Saved top {len(formatted_rows)} hyperparameter configurations to {output_path}")

def main():
    """Main entry point for the hyperparameter logging script."""
    parser = argparse.ArgumentParser(description="Log top hyperparameter configurations to CSV.")
    parser.add_argument(
        "--log-path", 
        type=str, 
        default="artifacts/training_results.json",
        help="Path to the JSON log of training results."
    )
    parser.add_argument(
        "--output-path", 
        type=str, 
        default="artifacts/hyperparameter_search.csv",
        help="Path to save the CSV output."
    )
    parser.add_argument(
        "--top-n", 
        type=int, 
        default=10,
        help="Number of top configurations to log."
    )
    
    args = parser.parse_args()
    logger = setup_logging()
    
    try:
        results = load_hyperparameter_log(Path(args.log_path))
        generate_hyperparameter_log(results, Path(args.output_path), args.top_n)
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import csv
    main()
