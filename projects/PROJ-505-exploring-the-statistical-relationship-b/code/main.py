"""
Main entry point for the entire pipeline.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
from utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

def load_results_from_json(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)

def aggregate_results(results_paths: list) -> dict:
    """Aggregate results from multiple JSON files."""
    aggregated = {}
    for path in results_paths:
        try:
            data = load_results_from_json(Path(path))
            aggregated.update(data)
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
    return aggregated

def generate_summary_artifacts(aggregated_results: dict, output_dir: Path) -> None:
    """Generate summary artifacts (CSV/JSON) for review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON summary
    json_path = output_dir / "summary.json"
    with open(json_path, 'w') as f:
        json.dump(aggregated_results, f, indent=2)
    
    # Convert to CSV if applicable
    if 'params' in aggregated_results:
        df = pd.DataFrame([aggregated_results['params']])
        csv_path = output_dir / "summary.csv"
        df.to_csv(csv_path, index=False)
    
    logger.info(f"Summary artifacts saved to {output_dir}")

def main():
    """Entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Run the full analysis pipeline.")
    parser.add_argument("--output", type=str, default="data/artifacts", help="Output directory")
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    
    # Placeholder for loading results from previous steps
    results_paths = [
        "data/artifacts/regression_results.json",
        "data/artifacts/cross_validation_results.json",
        "data/artifacts/permutation_results.json",
        "data/artifacts/sensitivity_results.json"
    ]
    
    aggregated = aggregate_results(results_paths)
    generate_summary_artifacts(aggregated, output_dir)

if __name__ == "__main__":
    main()
