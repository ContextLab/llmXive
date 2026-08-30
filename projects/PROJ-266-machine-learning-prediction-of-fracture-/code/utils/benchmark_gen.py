"""
Benchmark script for the synthetic microstructure generator.

Measures runtime of the generator (T005) and writes results to:
data/benchmarks/generator_runtime.json

Output schema:
{
  "total_time_seconds": float,
  "images_per_second": float,
  "num_images": int,
  "timestamp": str
}
"""
import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.synthetic_gen import generate_dataset, set_seed


def run_benchmark(num_images: int = 2000, seed: int = 42, output_dir: str = "data/raw") -> dict:
    """
    Run the synthetic generator and measure its performance.

    Args:
        num_images: Number of images to generate.
        seed: Random seed for reproducibility.
        output_dir: Directory to save generated images (relative to project root).

    Returns:
        Dictionary with benchmark metrics.
    """
    # Ensure output directory exists
    output_path = project_root / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    # Set seed for reproducibility
    set_seed(seed)

    # Clear existing images in output dir for clean benchmark
    for f in output_path.glob("*.png"):
        f.unlink()
    for f in output_path.glob("*.json"):
        f.unlink()

    # Record start time
    start_time = time.perf_counter()

    # Run generator
    images, metadata = generate_dataset(
        num_images=num_images,
        output_dir=str(output_path),
        seed=seed
    )

    # Record end time
    end_time = time.perf_counter()

    total_time = end_time - start_time
    images_per_second = num_images / total_time if total_time > 0 else 0.0

    results = {
        "total_time_seconds": round(total_time, 4),
        "images_per_second": round(images_per_second, 2),
        "num_images": num_images,
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "output_dir": str(output_path)
    }

    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark synthetic microstructure generator")
    parser.add_argument(
        "--num-images",
        type=int,
        default=2000,
        help="Number of images to generate for benchmarking (default: 2000)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory for generated images (default: data/raw)"
    )
    parser.add_argument(
        "--benchmark-output",
        type=str,
        default="data/benchmarks/generator_runtime.json",
        help="Path to write benchmark results (default: data/benchmarks/generator_runtime.json)"
    )

    args = parser.parse_args()

    # Ensure benchmark output directory exists
    benchmark_path = project_root / args.benchmark_output
    benchmark_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Running benchmark for {args.num_images} images...")
    results = run_benchmark(
        num_images=args.num_images,
        seed=args.seed,
        output_dir=args.output_dir
    )

    # Write results to JSON
    with open(benchmark_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Benchmark complete!")
    print(f"  Total time: {results['total_time_seconds']:.4f} seconds")
    print(f"  Images per second: {results['images_per_second']:.2f}")
    print(f"  Results written to: {benchmark_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
