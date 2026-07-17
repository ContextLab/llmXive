"""
Generates the sensitivity table.
"""
import csv
import json
import logging
import os
import sys
from pathlib import Path

from utils.config import get_project_root, get_path, ensure_dir, get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_sensitivity_results(file_path: Path) -> list:
    with open(file_path, 'r') as f:
        return json.load(f)

def format_p_value(p: float) -> str:
    return f"{p:.4f}"

def format_effect_size(e: float) -> str:
    return f"{e:.4f}"

def generate_table_markdown(results: list) -> str:
    lines = ["| Threshold | P-Value | Effect Size |", "|---|---|---|"]
    for r in results:
        lines.append(f"| {r['threshold']} | {format_p_value(r['p_value'])} | {format_effect_size(r['effect_size'])} |")
    return "\n".join(lines)

def generate_table_csv(results: list, output_path: Path):
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["threshold", "p_value", "effect_size"])
        writer.writeheader()
        writer.writerows(results)

def main():
    config = get_config()
    processed_dir = config["processed_data_dir"]
    input_file = processed_dir / "sensitivity_results.json"
    
    if not input_file.exists():
        logger.error("Sensitivity results not found.")
        sys.exit(1)
    
    results = load_sensitivity_results(input_file)
    md_content = generate_table_markdown(results)
    csv_path = processed_dir / "sensitivity_table.csv"
    generate_table_csv(results, csv_path)
    
    logger.info("Sensitivity table generated.")

if __name__ == "__main__":
    main()
