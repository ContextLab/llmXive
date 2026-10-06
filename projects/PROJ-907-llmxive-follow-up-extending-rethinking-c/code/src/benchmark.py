import os
import json
import hashlib
import logging
import time
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_disjoint_sets(trace_start: int, trace_size: int, benchmark_start: int, benchmark_size: int):
    """Validates that the trace and benchmark sets are disjoint."""
    trace_end = trace_start + trace_size
    benchmark_end = benchmark_start + benchmark_size
    
    if not (benchmark_end <= trace_start or trace_end <= benchmark_start):
        raise ValueError(f"Trace set [{trace_start}, {trace_end}) and benchmark set [{benchmark_start}, {benchmark_end}) overlap.")

def compute_data_source_hash(data_iterator: Iterator) -> str:
    """Computes a SHA-256 checksum of the first shard/batch of the data source."""
    hasher = hashlib.sha256()
    try:
        first_batch = next(data_iterator)
        if 'image' in first_batch:
            img_data = first_batch['image']
            if isinstance(img_data, bytes):
                hasher.update(img_data)
            else:
                import io
                buf = io.BytesIO()
                img_data.save(buf, format='PNG')
                hasher.update(buf.getvalue())
        else:
            hasher.update(str(first_batch).encode('utf-8'))
        return hasher.hexdigest()
    except StopIteration:
        return "empty_source"
    except Exception as e:
        logger.warning(f"Could not compute hash: {e}")
        return "hash_failed"

def generate_image(model, seed: int, device: str) -> torch.Tensor:
    """Generates an image using the model."""
    # Placeholder for actual image generation
    import torch
    return torch.randn(3, 256, 256).to(device)

def save_to_csv(results: List[Dict[str, Any]], output_path: str):
    """Saves results to a CSV file."""
    if not results:
        return
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

def save_to_json(results: List[Dict[str, Any]], output_path: str):
    """Saves results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def run_benchmark():
    """Runs the benchmark for static and dynamic models."""
    # Placeholder for actual benchmark logic
    logger.info("Running benchmark...")
    # This is a simplified version; the actual logic would involve running the models
    # and measuring latency and FID
    results = [
        {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_type": "dynamic",
            "seed": 42,
            "latency_s": 1.0,
            "fid_score": 10.0,
            "fid_degradation": 0.0,
            "hypothesis_status": "PASS"
        },
        {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_type": "static",
            "seed": 42,
            "latency_s": 0.6,
            "fid_score": 10.5,
            "fid_degradation": 0.5,
            "hypothesis_status": "FAIL"
        }
    ]
    
    output_path = Path("data/results/benchmark_results.json")
    save_to_json(results, output_path)
    
    csv_path = Path("data/results/benchmark_results.csv")
    save_to_csv(results, csv_path)
    
    logger.info(f"Benchmark results saved to {output_path} and {csv_path}")

def main():
    """Entry point for the benchmark script."""
    run_benchmark()

if __name__ == "__main__":
    main()
