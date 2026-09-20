"""
Helper script to save regression results.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import load_config, ensure_directories
from model import run_full_analysis

logger = logging.getLogger(__name__)

def save_regression_results(results: Dict[str, Any], output_path: Path) -> Path:
    """Saves regression results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved to {output_path}")
    return output_path

def main():
    """Main entry point."""
    config = load_config()
    ensure_directories()
    
    input_path = Path(config['paths']['processed_data']) / 'analysis_data.csv'
    output_path = Path(config['paths']['outputs']) / 'regression_results.json'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data not found: {input_path}")
    
    import pandas as pd
    df = pd.read_csv(input_path)
    full_results = run_full_analysis(df)
    
    # Save just regression part if needed, or full
    save_regression_results(full_results['regression'], output_path)

if __name__ == '__main__':
    main()
