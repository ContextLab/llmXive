import argparse
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

from config import get_stimuli_dir, get_processed_dir, get_project_root
from utils.logging import get_logger
from stimuli.manipulator import process_single_image, calculate_complexity_score
from data.loader import generate_mock_visual_genome

def load_test_images(logger: logging.Logger) -> List[Path]:
    """
    Load test images for benchmarking.
    If no real images exist in data/stimuli, generate a small set of mock images
    to ensure the benchmark can run.
    """
    stimuli_dir = get_stimuli_dir()
    if not stimuli_dir.exists():
        stimuli_dir.mkdir(parents=True, exist_ok=True)

    # Check for existing images
    existing_images = list(stimuli_dir.glob("*.png")) + list(stimuli_dir.glob("*.jpg"))
    
    if not existing_images:
        logger.info("No existing images found. Generating mock test images for benchmark...")
        # Generate a small set of mock images for benchmarking
        generate_mock_visual_genome(count=5, output_dir=stimuli_dir)
        existing_images = list(stimuli_dir.glob("*.png")) + list(stimuli_dir.glob("*.jpg"))
    
    if not existing_images:
        raise RuntimeError("Failed to generate or find any test images for benchmarking.")
    
    logger.info(f"Found {len(existing_images)} test images for benchmarking.")
    return existing_images

def benchmark_single_image(image_path: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Benchmark the processing time for a single image through the full manipulation pipeline.
    Returns a dictionary with timing details and success status.
    """
    result = {
        "image_path": str(image_path),
        "image_name": image_path.name,
        "success": False,
        "times": {},
        "error": None
    }
    
    try:
        # Measure time for initial complexity calculation
        start = time.perf_counter()
        initial_score = calculate_complexity_score(image_path)
        result["times"]["complexity_initial"] = time.perf_counter() - start
        
        # Measure time for enhanced detail manipulation
        start = time.perf_counter()
        enhanced_path = process_single_image(image_path, "enhance", output_dir=get_processed_dir())
        result["times"]["enhance"] = time.perf_counter() - start
        
        # Measure time for reduced detail manipulation
        start = time.perf_counter()
        reduced_path = process_single_image(image_path, "reduce", output_dir=get_processed_dir())
        result["times"]["reduce"] = time.perf_counter() - start
        
        # Total time
        result["times"]["total"] = result["times"]["complexity_initial"] + result["times"]["enhance"] + result["times"]["reduce"]
        result["success"] = True
        result["output_files"] = [str(enhanced_path), str(reduced_path)] if enhanced_path and reduced_path else []
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error benchmarking {image_path.name}: {e}")
    
    return result

def run_benchmark(output_file: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Run the full benchmark on all available test images.
    Ensures total processing time per image is under 30 seconds.
    """
    images = load_test_images(logger)
    results = []
    total_time = 0.0
    max_time = 0.0
    slow_images = []
    
    logger.info(f"Starting benchmark on {len(images)} images...")
    
    for img_path in images:
        logger.info(f"Benchmarking: {img_path.name}")
        result = benchmark_single_image(img_path, logger)
        results.append(result)
        
        if result["success"]:
            total_time += result["times"]["total"]
            if result["times"]["total"] > max_time:
                max_time = result["times"]["total"]
            if result["times"]["total"] >= 30.0:
                slow_images.append({
                    "name": img_path.name,
                    "time": result["times"]["total"]
                })
        else:
            logger.warning(f"Failed to benchmark {img_path.name}: {result['error']}")
    
    summary = {
        "total_images": len(images),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "total_time_seconds": total_time,
        "average_time_seconds": total_time / len(images) if images else 0,
        "max_time_seconds": max_time,
        "target_seconds": 30.0,
        "target_met": max_time < 30.0,
        "slow_images": slow_images,
        "detailed_results": results
    }
    
    # Write results to JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Benchmark complete. Results saved to {output_file}")
    logger.info(f"Average time: {summary['average_time_seconds']:.2f}s, Max time: {summary['max_time_seconds']:.2f}s")
    
    if not summary["target_met"]:
        logger.warning(f"TARGET NOT MET: {len(slow_images)} image(s) exceeded 30s limit.")
        for slow in slow_images:
            logger.warning(f"  - {slow['name']}: {slow['time']:.2f}s")
    else:
        logger.info("TARGET MET: All images processed in under 30 seconds.")
    
    return summary

def main():
    parser = argparse.ArgumentParser(description="Benchmark image manipulation performance")
    parser.add_argument("--output", type=str, default="data/processed/benchmark_results.json",
                      help="Path to output JSON file")
    parser.add_argument("--log-level", type=str, default="INFO",
                      choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                      help="Logging level")
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger("benchmark", level=args.log_level)
    
    # Run benchmark
    output_path = Path(args.output)
    run_benchmark(output_path, logger)

if __name__ == "__main__":
    main()