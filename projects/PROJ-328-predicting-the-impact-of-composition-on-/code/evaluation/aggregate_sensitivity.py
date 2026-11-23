"""
Aggregate Sensitivity Metrics (Task T035b).

Reads the raw sensitivity analysis results from T029c and generates a
synthesized summary table with human-readable interpretations.

Input:  data/processed/sensitivity_analysis.yaml
Output: data/processed/sensitivity_summary.yaml
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

INPUT_FILE = Path("data/processed/sensitivity_analysis.yaml")
OUTPUT_FILE = Path("data/processed/sensitivity_summary.yaml")

def load_sensitivity_analysis(path: Path) -> List[Dict[str, Any]]:
    """Load the raw sensitivity analysis YAML."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Handle both list format and dict with 'results' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        raise ValueError(f"Unexpected format in {path}")

def interpret_fraction(fraction: float) -> str:
    """
    Generate a human-readable interpretation for the fraction exceeding threshold.
    
    - High (> 0.8): The model consistently exceeds this performance level.
    - Moderate (0.4 - 0.8): The model exceeds this level in a significant portion of samples.
    - Low (< 0.4): The model rarely exceeds this performance level.
    """
    if fraction >= 0.8:
        return "High confidence: Model consistently exceeds this performance threshold."
    elif fraction >= 0.4:
        return "Moderate confidence: Model exceeds this threshold in a significant portion of bootstrap samples."
    else:
        return "Low confidence: Model rarely exceeds this performance threshold."

def aggregate_sensitivity_metrics(input_path: Path, output_path: Path) -> None:
    """
    Read sensitivity analysis and generate a summary table with interpretations.
    
    Output schema:
    - threshold (float)
    - fraction_exceeding (float)
    - interpretation (str)
    """
    logger.info(f"Loading sensitivity analysis from {input_path}")
    raw_data = load_sensitivity_analysis(input_path)
    
    if not raw_data:
        logger.warning("Sensitivity analysis data is empty. Generating empty summary.")
        summary = []
    else:
        summary = []
        for entry in raw_data:
            threshold = float(entry.get('threshold', 0.0))
            fraction = float(entry.get('fraction_exceeding', 0.0))
            interpretation = interpret_fraction(fraction)
            
            summary.append({
                'threshold': round(threshold, 4),
                'fraction_exceeding': round(fraction, 4),
                'interpretation': interpretation
            })
    
    # Sort by threshold for better readability
    summary.sort(key=lambda x: x['threshold'])
    
    logger.info(f"Writing sensitivity summary to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(summary, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Successfully generated summary with {len(summary)} entries.")

def main():
    """Entry point for the script."""
    logger.info("Starting sensitivity metrics aggregation (T035b).")
    
    try:
        aggregate_sensitivity_metrics(INPUT_FILE, OUTPUT_FILE)
        logger.info("T035b completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during aggregation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()