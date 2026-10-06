#!/usr/bin/env python3
"""
Script to generate cross-dataset comparison visualization for stability correlations.

This script aggregates stability correlation results from multiple genomic datasets
(GEO, TCGA, ENCODE) and produces a comparative bar chart visualization.

Usage:
    python code/scripts/generate_cross_dataset_visualization.py
    
Output:
    artifacts/cross_dataset_comparison.png
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Union

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ensure_directories, PROJECT_ROOT as CONFIG_PROJECT_ROOT
from src.report import generate_cross_dataset_comparison

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_aggregated_results(results_file: Union[str, Path]) -> List[Dict]:
    """
    Load aggregated stability results from a JSON file.
    
    Args:
        results_file: Path to JSON file containing aggregated results
        
    Returns:
        List of result dictionaries
    """
    results_file = Path(results_file)
    
    if not results_file.exists():
        raise FileNotFoundError(f"Results file not found: {results_file}")
        
    with open(results_file, 'r') as f:
        data = json.load(f)
        
    # Ensure we have a list of results
    if isinstance(data, dict):
        # If it's a single result, wrap it in a list
        if 'source' in data and 'stability_correlation' in data:
            return [data]
        # If it's a dict of sources, convert to list
        elif 'results' in data:
            return data['results']
            
    return data

def main():
    """
    Main entry point for generating cross-dataset comparison visualization.
    """
    # Default paths
    results_file = CONFIG_PROJECT_ROOT / "data" / "aggregated_stability_results.json"
    output_path = CONFIG_PROJECT_ROOT / "artifacts" / "cross_dataset_comparison.png"
    
    logger.info(f"Loading results from: {results_file}")
    
    try:
        # Load aggregated results
        if results_file.exists():
            results = load_aggregated_results(results_file)
            logger.info(f"Loaded {len(results)} dataset results")
        else:
            logger.warning(f"Results file not found at {results_file}. "
                         "This is expected if no datasets have been processed yet. "
                         "Generating placeholder visualization.")
            results = []
        
        # Generate visualization
        logger.info("Generating cross-dataset comparison visualization...")
        output_path = generate_cross_dataset_comparison(results, output_path)
        
        logger.info(f"Visualization successfully generated: {output_path}")
        print(f"SUCCESS: Visualization saved to {output_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generating visualization: {e}", exc_info=True)
        print(f"ERROR: Failed to generate visualization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
