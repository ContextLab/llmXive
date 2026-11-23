import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

def aggregate_stability_metrics(stable_input: str, unstable_input: str, output_csv: str):
    """
    Aggregates stable and unstable stability results into a single CSV.
    Excludes unstable results from statistical analysis inputs but records them.
    """
    logger = logging.getLogger("stability_metrics_generator")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)

    all_rows = []

    # Process stable results
    stable_path = Path(stable_input)
    if stable_path.exists():
        with open(stable_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    all_rows.append({
                        'config_id': data['config_id'],
                        'kernel_type': data['kernel_type'],
                        'l2_error': data['l2_error'],
                        'max_diff': data['max_diff'],
                        'status': 'stable'
                    })

    # Process unstable results (flagged but excluded from stats)
    unstable_path = Path(unstable_input)
    if unstable_path.exists():
        with open(unstable_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    all_rows.append({
                        'config_id': data['config_id'],
                        'kernel_type': data['kernel_type'],
                        'l2_error': data['l2_error'],
                        'max_diff': data['max_diff'],
                        'status': 'unstable'
                    })

    # Write CSV
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['config_id', 'kernel_type', 'l2_error', 'max_diff', 'status']
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(f"Aggregated {len(all_rows)} stability metrics to {output_csv}")
    stable_count = sum(1 for r in all_rows if r['status'] == 'stable')
    unstable_count = sum(1 for r in all_rows if r['status'] == 'unstable')
    logger.info(f"Stable: {stable_count}, Unstable: {unstable_count}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Aggregate stability metrics into CSV.")
    parser.add_argument("--stable-input", type=str, required=True, help="Path to stable results JSONL")
    parser.add_argument("--unstable-input", type=str, required=True, help="Path to unstable audit JSONL")
    parser.add_argument("--output", type=str, default="data/results/stability_metrics.csv", help="Output CSV path")
    args = parser.parse_args()
    aggregate_stability_metrics(args.stable_input, args.unstable_input, args.output)

if __name__ == "__main__":
    main()
