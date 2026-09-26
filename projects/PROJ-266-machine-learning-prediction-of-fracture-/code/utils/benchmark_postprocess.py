"""
Post-process generator benchmark results.

Reads raw benchmark data from data/benchmarks/generator_runtime_raw.json
and writes aggregated results to data/benchmarks/generator_runtime.json.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure paths are relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_BENCHMARK_PATH = PROJECT_ROOT / "data" / "benchmarks" / "generator_runtime_raw.json"
OUTPUT_BENCHMARK_PATH = PROJECT_ROOT / "data" / "benchmarks" / "generator_runtime.json"

def load_raw_benchmark():
    """Load raw benchmark data from JSON file."""
    if not RAW_BENCHMARK_PATH.exists():
        raise FileNotFoundError(
            f"Raw benchmark file not found: {RAW_BENCHMARK_PATH}. "
            "Please run code/utils/benchmark_gen.py first."
        )
    
    with open(RAW_BENCHMARK_PATH, 'r') as f:
        return json.load(f)

def process_benchmark(raw_data):
    """
    Process raw benchmark data into final format.
    
    Ensures numeric types are correct (float for time, images_per_second).
    """
    total_time = float(raw_data.get('total_time_seconds', 0.0))
    num_images = int(raw_data.get('num_images', 0))
    
    if total_time <= 0 or num_images <= 0:
        raise ValueError(
            f"Invalid benchmark data: total_time={total_time}, num_images={num_images}"
        )
    
    images_per_second = num_images / total_time
    
    processed = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "num_images": num_images,
        "total_time_seconds": total_time,
        "images_per_second": round(images_per_second, 4),
        "image_size": raw_data.get('image_size', 128),
        "metadata_file": "data/raw/metadata.json"
    }
    
    return processed

def save_benchmark(processed_data):
    """Save processed benchmark data to JSON file."""
    OUTPUT_BENCHMARK_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_BENCHMARK_PATH, 'w') as f:
        json.dump(processed_data, f, indent=2)
    
    print(f"Benchmark results saved to: {OUTPUT_BENCHMARK_PATH}")
    return OUTPUT_BENCHMARK_PATH

def main():
    """Main entry point for benchmark post-processing."""
    print("Loading raw benchmark data...")
    raw_data = load_raw_benchmark()
    
    print("Processing benchmark results...")
    processed_data = process_benchmark(raw_data)
    
    print("Saving processed benchmark data...")
    output_path = save_benchmark(processed_data)
    
    # Verification output
    print(f"\nBenchmark Summary:")
    print(f"  Total images: {processed_data['num_images']}")
    print(f"  Total time: {processed_data['total_time_seconds']:.4f} seconds")
    print(f"  Images per second: {processed_data['images_per_second']:.4f}")
    print(f"  Image size: {processed_data['image_size']}x{processed_data['image_size']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())