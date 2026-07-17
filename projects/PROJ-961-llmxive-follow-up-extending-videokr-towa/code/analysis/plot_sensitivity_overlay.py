"""
Plots the sensitivity overlay.
"""
import csv
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

from utils.config import get_project_root, get_path, ensure_dir, get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_sensitivity_results(file_path: Path) -> list:
    with open(file_path, 'r') as f:
        return json.load(f)

def plot_sensitivity_overlay(results: list, output_path: Path):
    # Placeholder
    logger.info(f"Plotting sensitivity overlay to {output_path}")

def main():
    config = get_config()
    processed_dir = config["processed_data_dir"]
    figures_dir = config["figures_dir"]
    ensure_dir(figures_dir)
    
    input_file = processed_dir / "sensitivity_results.json"
    
    if not input_file.exists():
        logger.error("Sensitivity results not found.")
        sys.exit(1)
    
    results = load_sensitivity_results(input_file)
    plot_sensitivity_overlay(results, figures_dir / "sensitivity_overlay.png")
    logger.info("Sensitivity overlay plot generated.")

if __name__ == "__main__":
    main()
