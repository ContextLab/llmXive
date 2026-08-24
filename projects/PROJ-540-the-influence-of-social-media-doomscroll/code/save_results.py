import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from config import load_config, ensure_directories
from model import run_initial_correlations, calculate_correlation
from exceptions import PowerLimitationError

logger = logging.getLogger(__name__)

def save_correlation_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save correlation results to a JSON file.
    
    Args:
        results: Dictionary containing correlation results (coefficients, p-values, etc.)
        output_path: Optional path to save the results. Defaults to config setting.
        
    Returns:
        Path to the saved file.
        
    Raises:
        IOError: If the file cannot be written.
    """
    config = load_config()
    if output_path is None:
        output_dir = Path(config.get('output_dir', 'outputs'))
        ensure_directories([output_dir])
        output_path = output_dir / 'correlation_results.json'
    
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
    logger.info("Starting correlation analysis and saving results...")
    
    config = load_config()
    data_path = Path(config.get('processed_data_path', 'data/processed/analysis_data.csv'))
    
    if not data_path.exists():
        logger.error(f"Processed data file not found: {data_path}")
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    
    # Run correlation analysis
    try:
        correlation_results = run_initial_correlations(data_path)
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        raise
    
    # Save results
    save_path = save_correlation_results(correlation_results)
    logger.info(f"Correlation analysis completed successfully. Results saved to {save_path}")

if __name__ == "__main__":
    # Setup basic logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    main()