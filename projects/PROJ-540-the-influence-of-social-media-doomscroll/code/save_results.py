"""
Helper script to save correlation results.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import load_config, ensure_directories
from model import run_initial_correlations

logger = logging.getLogger(__name__)

def save_correlation_results(correlations: Dict[str, Any], output_path: Path) -> Path:
    """Saves correlation results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(correlations, f, indent=2)
    logger.info(f"Saved to {output_path}")
    return output_path

def main():
    """Main entry point."""
    config = load_config()
    ensure_directories()
    
    input_path = Path(config['paths']['processed_data']) / 'analysis_data.csv'
    output_path = Path(config['paths']['outputs']) / 'correlation_results.json'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data not found: {input_path}")
    
    import pandas as pd
    df = pd.read_csv(input_path)
    correlations = run_initial_correlations(df)
    save_correlation_results(correlations, output_path)

if __name__ == '__main__':
    main()
