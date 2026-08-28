import argparse
import os
import sys
import csv
import random
import numpy as np

def generate_synthetic_data(size: int = 1000) -> list:
    """
    Generate synthetic data for fallback scenarios.
    Returns a list of dictionaries representing rows.
    """
    data = []
    for i in range(size):
        row = {
            "step": i,
            "model": "synthetic",
            "coherence_score": random.uniform(0.0, 1.0),
            "diversity_score": random.uniform(0.0, 1.0),
            "step_latency": random.uniform(0.001, 0.01),
            "timestamp": time.time() + i
        }
        data.append(row)
    return data

def write_csv(data: list, file_path: str):
    """Write data to a CSV file."""
    if not data:
        return
    fieldnames = data[0].keys()
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

import time

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for fallback")
    parser.add_argument("--size", type=int, default=1000, help="Number of rows to generate")
    parser.add_argument("--output", type=str, default="data/synthetic_small.csv", help="Output file path")
    args = parser.parse_args()

    data = generate_synthetic_data(args.size)
    write_csv(data, args.output)
    print(f"Generated {args.size} rows to {args.output}")

if __name__ == "__main__":
    main()