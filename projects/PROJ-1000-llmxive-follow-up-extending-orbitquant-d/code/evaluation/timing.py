"""
code/evaluation/timing.py
Implements wall-clock inference timing for Static vs Dynamic rotation methods.

This module orchestrates the timing experiment:
1. Loads prompts from the diverse set (data/processed/diverse_prompts.csv).
2. Runs inference using the Static Baseline (T011) and records time.
3. Runs inference using the Dynamic Router (T024/T025) and records time.
4. Computes statistics (mean, std, overhead %) and saves to data/processed/timing_results.json.

Dependencies:
- code/config.py
- code/quantization/static_baseline.py
- code/quantization/w2a4_engine.py
- code/analysis/router.py
- code/analysis/load_matrices.py
- code/models/flux_wan_loader.py
- code/utils/gpu_offload.py
"""

import os
import sys
import json
import time
import logging
import csv
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Project imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from quantization.static_baseline import StaticRotationBaseline
from quantization.w2a4_engine import W2A4Engine
from analysis.router import EntropyRouter
from analysis.load_matrices import MatrixLoader
from models.flux_wan_loader import ModelLoader
from utils.gpu_offload import check_gpu_availability, GPUOffloadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/timing_run.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
WARMUP_ITERATIONS = 2
TIMING_ITERATIONS = 10

def load_prompts_for_timing(config: Config) -> List[Dict[str, Any]]:
    """
    Loads a subset of prompts for timing analysis from diverse_prompts.csv.
    Uses a fixed seed for reproducibility if the file is large.
    """
    prompts_path = config.PROMPTS_PATH
    if not os.path.exists(prompts_path):
        raise FileNotFoundError(f"Prompts file not found: {prompts_path}")
    
    prompts = []
    logger.info(f"Loading prompts from {prompts_path}")
    
    with open(prompts_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'caption' in row and row['caption'] and len(row['caption'].strip()) > 0:
                prompts.append({
                    'id': row.get('id', 'unknown'),
                    'caption': row['caption'],
                    'source': row.get('source', 'unknown')
                })
    
    if not prompts:
        raise ValueError("No valid prompts found in the dataset.")
    
    # Limit to a manageable number for timing (e.g., 20) to fit within wall-clock budget
    # but ensure it's enough for statistical significance
    limit = min(len(prompts), config.TIMING_PROMPT_COUNT)
    logger.info(f"Using {limit} prompts for timing analysis (total available: {len(prompts)})")
    
    return prompts[:limit]

def run_static_inference(
    prompts: List[Dict[str, Any]],
    model_loader: ModelLoader,
    baseline: StaticRotationBaseline,
    config: Config
) -> List[float]:
    """
    Runs inference using the Static Rotation Baseline and measures wall-clock time.
    Returns a list of execution times (in seconds) for each prompt.
    """
    logger.info("Starting Static Baseline Inference Timing")
    times = []
    
    device = config.DEVICE
    logger.info(f"Running on device: {device}")
    
    # Warmup
    logger.info(f"Running {WARMUP_ITERATIONS} warmup iterations...")
    for _ in range(WARMUP_ITERATIONS):
        # Use a dummy prompt for warmup to ensure model is loaded and hooks are ready
        _ = model_loader.generate_single(prompt="warmup test", device=device)
    
    # Timing loop
    for i, p in enumerate(prompts):
        logger.info(f"Static Inference [{i+1}/{len(prompts)}]: {p['id']}")
        start = time.perf_counter()
        
        try:
            # Generate image using static baseline
            # The DiTWrapper handles the generation loop and activation capture
            # We assume the baseline is already configured with the static matrix
            model_loader.set_quantization_engine(baseline)
            _ = model_loader.generate_single(prompt=p['caption'], device=device)
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            logger.info(f"  -> Completed in {elapsed:.4f}s")
            
        except Exception as e:
            logger.error(f"Error during static inference for {p['id']}: {e}")
            # If GPU fails, we should not continue silently
            if "cuda" in str(device).lower() or "gpu" in str(device).lower():
                raise GPUOffloadError(f"GPU failure during static inference: {e}")
            raise
    
    return times

def run_dynamic_inference(
    prompts: List[Dict[str, Any]],
    model_loader: ModelLoader,
    router: EntropyRouter,
    matrices_loader: MatrixLoader,
    config: Config
) -> List[float]:
    """
    Runs inference using the Dynamic Router and measures wall-clock time.
    Returns a list of execution times (in seconds) for each prompt.
    """
    logger.info("Starting Dynamic Router Inference Timing")
    times = []
    
    device = config.DEVICE
    logger.info(f"Running on device: {device}")
    
    # Load matrices
    logger.info("Loading pre-computed rotation matrices...")
    matrices = matrices_loader.load()
    if not matrices:
        raise ValueError("Failed to load rotation matrices for dynamic inference.")
    router.set_matrices(matrices)
    
    # Warmup
    logger.info(f"Running {WARMUP_ITERATIONS} warmup iterations...")
    for _ in range(WARMUP_ITERATIONS):
        _ = model_loader.generate_single(prompt="warmup test", device=device)
    
    # Timing loop
    for i, p in enumerate(prompts):
        logger.info(f"Dynamic Inference [{i+1}/{len(prompts)}]: {p['id']}")
        start = time.perf_counter()
        
        try:
            # 1. Compute entropy for the prompt
            entropy = router.compute_entropy(p['caption'])
            
            # 2. Select matrix based on entropy
            matrix_idx = router.route(entropy)
            
            # 3. Configure engine with selected matrix
            # The W2A4Engine needs to be updated with the specific matrix for this step
            dynamic_engine = W2A4Engine()
            dynamic_engine.set_rotation_matrix(matrices[matrix_idx])
            model_loader.set_quantization_engine(dynamic_engine)
            
            # 4. Generate image
            _ = model_loader.generate_single(prompt=p['caption'], device=device)
            
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            logger.info(f"  -> Completed in {elapsed:.4f}s (Entropy: {entropy:.4f}, Matrix: {matrix_idx})")
            
        except Exception as e:
            logger.error(f"Error during dynamic inference for {p['id']}: {e}")
            if "cuda" in str(device).lower() or "gpu" in str(device).lower():
                raise GPUOffloadError(f"GPU failure during dynamic inference: {e}")
            raise
    
    return times

def compute_statistics(times: List[float]) -> Dict[str, float]:
    """Computes mean, std, min, max, and median for a list of times."""
    if not times:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "median": 0.0}
    
    arr = np.array(times)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
        "count": len(times)
    }

def save_timing_results(
    static_results: Dict[str, Any],
    dynamic_results: Dict[str, Any],
    output_path: Path
) -> None:
    """Saves the timing analysis results to a JSON file."""
    report = {
        "static_baseline": static_results,
        "dynamic_router": dynamic_results,
        "comparison": {
            "overhead_seconds": dynamic_results["stats"]["mean"] - static_results["stats"]["mean"],
            "overhead_percent": (
                (dynamic_results["stats"]["mean"] - static_results["stats"]["mean"]) 
                / static_results["stats"]["mean"] * 100
            ) if static_results["stats"]["mean"] > 0 else 0.0
        }
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Timing results saved to {output_path}")

def main() -> None:
    """Main entry point for the timing analysis."""
    config = Config()
    output_path = config.TIMING_RESULTS_PATH
    
    logger.info("Starting Timing Analysis Pipeline (T033)")
    logger.info(f"Output path: {output_path}")
    
    # 1. Check GPU availability
    try:
        check_gpu_availability(config.DEVICE)
    except GPUOffloadError as e:
        logger.error(f"GPU check failed: {e}")
        # In a real scenario, this might trigger offload, but for this script
        # we assume the environment is already set up or the offload logic
        # is handled externally. If we are on CPU and it's too slow, we might fail.
        if not torch.cuda.is_available():
            logger.warning("Running on CPU. Timing results may not reflect GPU performance.")
    
    # 2. Load Prompts
    try:
        prompts = load_prompts_for_timing(config)
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        sys.exit(1)
    
    # 3. Initialize Components
    try:
        model_loader = ModelLoader(config)
        baseline = StaticRotationBaseline(config)
        router = EntropyRouter(config)
        matrices_loader = MatrixLoader(config)
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)
    
    # 4. Run Static Inference
    static_times = []
    try:
        static_times = run_static_inference(prompts, model_loader, baseline, config)
    except Exception as e:
        logger.error(f"Static inference failed: {e}")
        sys.exit(1)
    
    # 5. Run Dynamic Inference
    dynamic_times = []
    try:
        dynamic_times = run_dynamic_inference(prompts, model_loader, router, matrices_loader, config)
    except Exception as e:
        logger.error(f"Dynamic inference failed: {e}")
        sys.exit(1)
    
    # 6. Compute Statistics
    static_stats = compute_statistics(static_times)
    dynamic_stats = compute_statistics(dynamic_times)
    
    logger.info(f"Static Mean: {static_stats['mean']:.4f}s (+/- {static_stats['std']:.4f}s)")
    logger.info(f"Dynamic Mean: {dynamic_stats['mean']:.4f}s (+/- {dynamic_stats['std']:.4f}s)")
    
    # 7. Save Results
    save_timing_results(
        {"stats": static_stats, "raw_times": static_times},
        {"stats": dynamic_stats, "raw_times": dynamic_times},
        output_path
    )
    
    logger.info("Timing Analysis Complete.")

if __name__ == "__main__":
    main()