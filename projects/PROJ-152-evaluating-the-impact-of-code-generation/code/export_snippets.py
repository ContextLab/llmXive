"""
T018: Generate data/generated/snippets.csv from generation results.

Reads the raw generation output (JSON produced by code/generate.py),
calculates line counts, and writes a CSV with the required columns:
snippet_id, model, prompt_id, code, line_count, timestamp.

Expected output: N=90 rows (30 prompts * 3 models).
"""
import os
import json
import csv
import logging
from pathlib import Path
from datetime import datetime, timezone

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def load_generation_results(results_path: Path) -> list:
    """Load the JSON file containing all generated snippets."""
    if not results_path.exists():
        raise FileNotFoundError(
            f"Generation results file not found: {results_path}. "
            "Please run code/generate.py first to produce this file."
        )
    
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # The generator typically returns a list of dicts or a dict with a 'results' key.
    # We support both structures to be robust.
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(
            f"Unexpected format in {results_path}: expected a list or a dict with 'results' key."
        )

def calculate_line_count(code: str) -> int:
    """Count non-empty lines in the generated code."""
    if not code:
        return 0
    # Count lines that contain at least one non-whitespace character
    return sum(1 for line in code.splitlines() if line.strip())

def export_to_csv(results: list, output_path: Path) -> int:
    """
    Write the results to a CSV file with the required schema.
    
    Columns: snippet_id, model, prompt_id, code, line_count, timestamp
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["snippet_id", "model", "prompt_id", "code", "line_count", "timestamp"]
    count = 0
    current_time = datetime.now(timezone.utc).isoformat()

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for item in results:
            snippet_id = item.get("snippet_id")
            model = item.get("model")
            prompt_id = item.get("prompt_id")
            code = item.get("code", "")
            
            # Handle cases where code might be missing or None
            if code is None:
                code = ""

            line_count = calculate_line_count(code)

            row = {
                "snippet_id": snippet_id,
                "model": model,
                "prompt_id": prompt_id,
                "code": code,
                "line_count": line_count,
                "timestamp": current_time
            }
            writer.writerow(row)
            count += 1

    logger.info(f"Wrote {count} rows to {output_path}")
    return count

def main():
    """Main entry point for T018."""
    # Define paths based on project structure
    results_file = config.PROJECT_ROOT / "data" / "generated" / "generation_results.json"
    output_file = config.PROJECT_ROOT / "data" / "generated" / "snippets.csv"

    logger.info(f"Loading generation results from {results_file}...")
    results = load_generation_results(results_file)
    
    expected_count = 90  # 30 prompts * 3 models
    logger.info(f"Loaded {len(results)} snippets. Expected: {expected_count}.")
    
    if len(results) == 0:
        logger.warning("No snippets found in results. The CSV will be empty.")
    
    logger.info(f"Exporting to {output_file}...")
    count = export_to_csv(results, output_file)
    
    logger.info(f"Task T018 complete. Generated {count} rows in {output_file}.")
    return count

if __name__ == "__main__":
    main()
