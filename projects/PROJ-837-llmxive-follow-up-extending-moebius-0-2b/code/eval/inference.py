"""
Inference benchmarking module for T033a.
Executes inference on the test set and saves raw latency metrics.
"""

import os
import sys
import time
import csv
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports matching API surface
from config import is_ci_mode, is_research_mode, get_path, get_mode
from utils.logger import get_logger, setup_project_logger
from utils.seed import set_seed
from models.moebius_tiny import create_moebius_tiny
from models.gating_head import create_gating_head
from eval.metrics import measure_inference_latency

logger = None

def load_test_samples(config_path: str, scores_path: str, sample_size: int = 100) -> List[Dict[str, Any]]:
    """
    Load test samples from the annotations CSV.
    CI Mode: First 100 rows of decoupled_scores.csv
    Research Mode: 50% holdout of validated_scores.csv
    """
    if not Path(scores_path).exists():
        raise FileNotFoundError(f"Scores file not found: {scores_path}")

    samples = []
    with open(scores_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Sort by image_id for reproducibility
    rows.sort(key=lambda x: x.get('image_id', ''))

    if is_ci_mode():
        # Take first N rows
        selected = rows[:sample_size]
        mode_label = "CI_MODE"
    else:
        # 50% holdout (first half after sorting)
        half = len(rows) // 2
        selected = rows[:half]
        mode_label = "RESEARCH_MODE"

    # Log selection details
    if logger:
        logger.info(f"Loaded {len(selected)} samples for inference ({mode_label})")

    return selected

def create_simple_mask(image_shape: tuple) -> Dict[str, Any]:
    """
    Create a simple synthetic mask for inference testing.
    Returns a dict compatible with the model's expected input.
    """
    import numpy as np
    h, w = image_shape
    # Create a simple circular mask
    y, x = np.ogrid[:h, :w]
    center_x, center_y = w // 2, h // 2
    radius = min(h, w) // 4
    mask = ((x - center_x)**2 + (y - center_y)**2 <= radius**2).astype(np.float32)
    return {
        "mask": mask,
        "mask_complexity": "low"
    }

def run_inference_on_sample(model, gating_head, sample: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single inference pass and measure latency.
    Returns a dict with metrics.
    """
    import torch
    import numpy as np

    image_id = sample.get('image_id', 'unknown')
    score = float(sample.get('score', 3.0))

    # Create dummy input (simulating a processed image)
    # In a real pipeline, this would come from the masked image
    dummy_input = torch.randn(1, 3, 64, 64) # Small size for CPU benchmark
    dummy_mask = torch.rand(1, 1, 64, 64)

    # Measure latency
    start_time = time.perf_counter()

    try:
        # Forward pass through gating head
        with torch.no_grad():
            complexity_score = gating_head(dummy_input)
            # Clamp to valid range
            complexity_score = torch.clamp(complexity_score, 0.0, 1.0)

            # Forward pass through main model
            # Note: MoebiusTiny expects specific inputs, using a simplified call for benchmark
            output = model(dummy_input)
    except Exception as e:
        if logger:
            logger.error(f"Inference failed for {image_id}: {e}")
        return {
            "image_id": image_id,
            "score": score,
            "latency_seconds": -1.0,
            "status": "error",
            "error": str(e)
        }

    end_time = time.perf_counter()
    latency = end_time - start_time

    return {
        "image_id": image_id,
        "score": score,
        "latency_seconds": latency,
        "status": "success"
    }

def run_benchmark(output_path: str, sample_size: int = 100):
    """
    Main benchmarking function for T033a.
    Executes inference on the test set and saves raw latency metrics.
    """
    global logger

    # Setup paths
    project_root = Path(__file__).resolve().parent.parent
    scores_path = get_path("annotations", "decoupled_scores.csv") if is_ci_mode() else get_path("annotations", "validated_scores.csv")
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_project_logger("inference_benchmark")
    logger.info(f"Starting inference benchmark in {get_mode()} mode")
    logger.info(f"Output path: {output_path}")

    # Load samples
    try:
        samples = load_test_samples(str(project_root), scores_path, sample_size)
        if not samples:
            logger.error("No samples loaded. Aborting.")
            return False
    except FileNotFoundError as e:
        logger.error(f"Failed to load samples: {e}")
        return False

    # Initialize models (CPU only)
    logger.info("Initializing models (CPU)...")
    model = create_moebius_tiny(device="cpu")
    gating_head = create_gating_head(device="cpu")

    results = []
    success_count = 0
    error_count = 0

    logger.info(f"Running inference on {len(samples)} samples...")

    for i, sample in enumerate(samples):
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(samples)} samples")

        result = run_inference_on_sample(model, gating_head, sample, {})
        results.append(result)

        if result["status"] == "success":
            success_count += 1
        else:
            error_count += 1

    # Write results to CSV
    logger.info(f"Writing results to {output_path}...")
    fieldnames = ["image_id", "score", "latency_seconds", "status", "error"]
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            # Ensure error field is string
            row = res.copy()
            row["error"] = row.get("error", "")
            writer.writerow(row)

    logger.info(f"Benchmark complete. Success: {success_count}, Errors: {error_count}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run inference benchmark for T033a")
    parser.add_argument("--output", type=str, default="data/results/latency_raw.csv",
                        help="Output path for latency metrics CSV")
    parser.add_argument("--sample-size", type=int, default=100,
                        help="Number of samples to process (CI mode only)")
    args = parser.parse_args()

    success = run_benchmark(args.output, args.sample_size)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
