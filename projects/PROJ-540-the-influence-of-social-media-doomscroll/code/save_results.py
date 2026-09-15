"""
Module to save correlation results to a JSON file.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import load_config, ensure_directories
from model import run_initial_correlations

logger = logging.getLogger(__name__)

def save_correlation_results(
    results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save correlation results to a JSON file.

    Args:
        results: Dictionary containing correlation results.
        output_path: Path to save the JSON file. If None, uses config default.

    Returns:
        Path to the saved file.
    """
    config = load_config()
    if output_path is None:
        output_path = Path(config.get('output_dir', 'outputs')) / 'correlation_results.json'
    
    ensure_directories([output_path.parent])
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Correlation results saved to {output_path}")
        return output_path
    except IOError as e:
        logger.error(f"Failed to save correlation results: {e}")
        raise

def main() -> None:
    """
    Main function to run correlation analysis and save results.
    """
    # Setup logging
    from logging_config import setup_logging
    setup_logging()
    
    config = load_config()
    
    # Load processed data
    data_path = Path(config.get('processed_data_path', 'data/processed/analysis_data.csv'))
    if not data_path.exists():
        logger.error(f"Processed data file not found: {data_path}")
        sys.exit(1)
    
    try:
        # Run correlation analysis
        logger.info("Running correlation analysis...")
        results = run_initial_correlations(data_path)
        
        # Save results
        output_path = Path(config.get('output_dir', 'outputs')) / 'correlation_results.json'
        save_correlation_results(results, output_path)
        
        logger.info("Correlation analysis and saving completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during correlation analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()