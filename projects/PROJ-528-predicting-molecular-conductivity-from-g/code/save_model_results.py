import os
import json
import logging
import argparse
from typing import Dict, Any, Optional
from code.config import DATA_PATH
from code.logging_config import setup_logging

def get_default_results() -> Dict[str, Any]:
    """Return the default structure for model_results.json."""
    return {
        "rf_r2": 0.0,
        "gb_r2": 0.0,
        "cv_scores": [],
        "sensitivity_analysis": {},
        "vif_scores": []
    }

def initialize_results_file(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Create or overwrite the model results JSON file with the default structure.
    
    Args:
        filepath: Path to the results file. Defaults to DATA_PATH/model_results.json.
        
    Returns:
        The initialized dictionary structure.
    """
    if filepath is None:
        filepath = os.path.join(DATA_PATH, "processed", "model_results.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    results = get_default_results()
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Initialized model results file at: {filepath}")
    return results

def load_results(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Load existing results from file.
    
    Args:
        filepath: Path to the results file.
        
    Returns:
        The loaded dictionary.
    """
    if filepath is None:
        filepath = os.path.join(DATA_PATH, "processed", "model_results.json")
        
    if not os.path.exists(filepath):
        return get_default_results()
        
    with open(filepath, 'r') as f:
        return json.load(f)

def save_results_to_json(results: Dict[str, Any], filepath: Optional[str] = None) -> None:
    """
    Save results dictionary to JSON file.
    
    Args:
        results: The results dictionary to save.
        filepath: Path to the results file.
    """
    if filepath is None:
        filepath = os.path.join(DATA_PATH, "processed", "model_results.json")
        
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
        
    logging.info(f"Saved model results to: {filepath}")

def main() -> None:
    """CLI entry point to initialize the model results file."""
    parser = argparse.ArgumentParser(description="Initialize or update model results JSON.")
    parser.add_argument(
        "--init", 
        action="store_true", 
        help="Initialize file with default structure (overwrite existing)."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None, 
        help="Output file path (default: data/processed/model_results.json)."
    )
    
    args = parser.parse_args()
    setup_logging()
    
    if args.init:
        initialize_results_file(args.output)
    else:
        # If not initializing, just ensure the file exists with defaults
        if not os.path.exists(args.output if args.output else os.path.join(DATA_PATH, "processed", "model_results.json")):
            initialize_results_file(args.output)
            logging.info("File did not exist. Initialized with defaults.")
        else:
            logging.info("File already exists. Use --init to overwrite.")

if __name__ == "__main__":
    main()
