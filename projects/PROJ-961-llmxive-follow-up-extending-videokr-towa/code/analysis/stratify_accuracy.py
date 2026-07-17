"""
Stratifies accuracy by hop bin.
"""
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

from utils.config import get_project_root, get_path, ensure_dir, get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_annotated_data(file_path: Path) -> list:
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def bin_hop_length(hops: int) -> str:
    if hops == 1: return "1-hop"
    if hops == 2: return "2-hop"
    if hops >= 3: return "3+ hops"
    return "unresolvable"

def calculate_accuracy_by_bin(records: list) -> dict:
    bin_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    for rec in records:
        hops = int(rec.get("chain_length", -1))
        if hops < 0: continue
        
        bin_label = bin_hop_length(hops)
        bin_stats[bin_label]["total"] += 1
        if rec.get("correctness") == "True" or rec.get("correctness") == "true" or rec.get("correctness") == "1":
            bin_stats[bin_label]["correct"] += 1
    
    results = {}
    for bin_label, stats in bin_stats.items():
        if stats["total"] > 0:
            results[bin_label] = {
                "accuracy": stats["correct"] / stats["total"],
                "count": stats["total"],
                "correct": stats["correct"]
            }
        else:
            results[bin_label] = {"accuracy": 0.0, "count": 0, "correct": 0}
    return results

def write_results(results: dict, output_path: Path):
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    config = get_config()
    processed_dir = config["processed_data_dir"]
    input_file = processed_dir / "annotated_videokr.csv"
    output_file = processed_dir / "accuracy_by_bin.json"
    
    if not input_file.exists():
        logger.error("Annotated data not found.")
        sys.exit(1)
    
    records = load_annotated_data(input_file)
    results = calculate_accuracy_by_bin(records)
    write_results(results, output_file)
    logger.info(f"Stratification complete. Output: {output_file}")

if __name__ == "__main__":
    main()
