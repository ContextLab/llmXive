import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
import logging

from code.data.synthetic_gen import generate_dataset
from code.utils.logger import get_logger

logger = get_logger(__name__)

def estimate_total_time(num_images: int, sample_time: float) -> float:
    """Estimate total time based on sample time and number of images."""
    if sample_time <= 0:
        return 0.0
    return num_images * sample_time

def run_benchmark(num_images: int = 100, output_dir: str = 'data/benchmarks') -> dict:
    """Run benchmark for synthetic dataset generation."""
    logger.info(f"Starting benchmark for {num_images} images")
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Warm up
    logger.info("Warming up generator...")
    try:
        generate_dataset(output_dir='/tmp/benchmark_warmup', num_images=5, image_size=64)
    except Exception as e:
        logger.warning(f"Warmup failed (ignoring): {e}")
    
    # Benchmark
    start_time = time.time()
    try:
        generate_dataset(output_dir='/tmp/benchmark_run', num_images=num_images, image_size=128)
    except Exception as e:
        logger.error(f"Benchmark generation failed: {e}")
        raise
    end_time = time.time()
    
    total_time = end_time - start_time
    images_per_second = num_images / total_time if total_time > 0 else 0.0
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'num_images': num_images,
        'total_time_seconds': round(total_time, 4),
        'images_per_second': round(images_per_second, 2),
        'image_size': 128
    }
    
    # Save results
    output_path = os.path.join(output_dir, 'generator_runtime.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Benchmark complete: {total_time:.2f}s for {num_images} images")
    logger.info(f"Performance: {images_per_second:.2f} images/second")
    logger.info(f"Results saved to {output_path}")
    
    return results

def main():
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(description='Benchmark synthetic dataset generator')
    parser.add_argument('--num_images', type=int, default=100,
                      help='Number of images to generate for benchmark')
    parser.add_argument('--output_dir', type=str, default='data/benchmarks',
                      help='Output directory for benchmark results')
    
    args = parser.parse_args()
    
    run_benchmark(num_images=args.num_images, output_dir=args.output_dir)

if __name__ == '__main__':
    main()