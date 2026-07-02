"""
Module to save robustness check results to JSON.
This module implements task T027: Save robustness results to outputs/robustness_results.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import load_config, ensure_directories

logger = logging.getLogger(__name__)


def save_robustness_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save robustness check results to a JSON file.

    Args:
        results: Dictionary containing robustness check results including:
            - full_sample: Full sample regression results
            - high_engagement_subset: High engagement subset regression results
            - comparison: Comparison metrics (coefficient differences, significance changes)
            - metadata: Additional metadata (correlation threshold, sample sizes, etc.)
        output_path: Optional path to save results. If None, uses config default.

    Returns:
        Path to the saved file.

    Raises:
        FileNotFoundError: If output directory does not exist and cannot be created.
        json.JSONDecodeError: If results cannot be serialized to JSON.
    """
    config = load_config()
    if output_path is None:
        output_path = Path(config.get("output_dir", "outputs")) / "robustness_results.json"
    
    # Ensure directory exists
    ensure_directories([output_path.parent])
    
    # Convert any non-serializable objects (numpy types, etc.)
    def serialize(obj):
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [serialize(item) for item in obj]
        else:
            # For numpy types and other objects, convert to string or float
            try:
                return float(obj)
            except (TypeError, ValueError):
                return str(obj)

    serializable_results = serialize(results)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2)
        logger.info(f"Robustness results saved to {output_path}")
        return output_path
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to save robustness results: {e}")
        raise


def main():
    """
    Main entry point for saving robustness results.
    This function is called when the script is run directly.
    It loads the results from the robustness check (produced by T026)
    and saves them to outputs/robustness_results.json.
    """
    # Setup logging
    from logging_config import setup_logging
    setup_logging()

    # Load configuration
    config = load_config()
    logger.info("Starting robustness results save process")

    # The results should be passed in or loaded from a temporary location.
    # For this implementation, we assume the robustness check (T026) 
    # has already computed the results and we are just saving them.
    # In a real pipeline, results would be passed as arguments or loaded from a cache.
    
    # Example: Load results from a temporary file if T026 saved them there,
    # or construct them here if this script is the final step.
    # Since T026 runs the check, we'll assume the results are available
    # via a standard location or we re-run the check logic to get them.
    
    # For the purpose of this task, we will call the robustness check logic
    # to generate the results and then save them.
    from robustness import run_robustness_check
    from config import get_dataset_url

    data_path = Path(config.get("processed_data_path", "data/processed/analysis_data.csv"))
    if not data_path.exists():
        logger.error(f"Processed data not found at {data_path}. Run data ingestion and cleaning first.")
        sys.exit(1)

    logger.info(f"Loading data from {data_path} for robustness check")
    
    # Run the robustness check to get results
    results = run_robustness_check(data_path)
    
    if results is None:
        logger.warning("Robustness check returned no results. Skipping save.")
        return

    # Save the results
    output_path = save_robustness_results(results)
    logger.info(f"Successfully saved robustness results to {output_path}")


if __name__ == "__main__":
    main()
