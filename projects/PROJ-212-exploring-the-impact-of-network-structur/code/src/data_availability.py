"""
Data availability checking and state management.
Implements logic to set regression_blocked flag based on raw data count.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any
import yaml

logger = logging.getLogger(__name__)

def check_data_availability(raw_dir: Path, threshold: int = 10) -> Dict[str, Any]:
    """
    Check the number of files in the raw data directory.
    
    If the count is below the threshold, returns a state dict with
    regression_blocked set to True. Otherwise, sets it to False.
    
    Args:
        raw_dir: Path to the data/raw directory.
        threshold: Minimum number of files required (default 10).
        
    Returns:
        Dict with 'regression_blocked' boolean and 'file_count'.
    """
    state = {
        "file_count": 0,
        "regression_blocked": True
    }
    
    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return state
        
    files = [f for f in raw_dir.iterdir() if f.is_file()]
    count = len(files)
    state["file_count"] = count
    
    if count >= threshold:
        state["regression_blocked"] = False
        logger.info(f"Data availability check passed: {count} files found (>= {threshold}).")
    else:
        logger.warning(f"Data availability check failed: {count} files found (< {threshold}). Regression blocked.")
        
    return state

def write_state_file(state: Dict[str, Any], output_path: Path) -> None:
    """
    Write the data availability state to a YAML file.
    
    Args:
        state: The state dictionary to write.
        output_path: Path to the output YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    logger.info(f"State written to {output_path}")

def main() -> None:
    """
    Main entry point for the data availability check script.
    Reads config for paths, checks data, and writes state file.
    """
    # Import config here to avoid circular imports if this module is imported elsewhere
    # Assuming config.yaml is at project root
    from config import load_config, get_paths
    
    config = load_config()
    paths = get_paths(config)
    
    raw_dir = paths['raw_data']
    state_file = paths['state'] / 'data_availability.yaml'
    
    logger.info(f"Checking data availability in {raw_dir}")
    
    state = check_data_availability(raw_dir, threshold=config.get('thresholds', {}).get('min_files', 10))
    write_state_file(state, state_file)
    
    if state['regression_blocked']:
        logger.warning("Regression analysis is blocked due to insufficient data.")
    else:
        logger.info("Sufficient data available. Regression analysis can proceed.")

if __name__ == '__main__':
    # Setup basic logging for script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
