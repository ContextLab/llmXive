"""
Chunked Runner for Memory-Constrained Evaluation.
This script orchestrates the evaluation with dynamic chunk size adjustment
to ensure we stay within 7GB RAM.
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import torch
import psutil

# Import project modules
from utils.logger import get_logger
from config import get_path, is_ci_mode, get_mode
from utils.refactor_utils import ensure_directory
from eval.metrics import run_metrics_evaluation, InpaintingEvalDataset
from models.moebius_dynamic import create_moebius_dynamic

logger = get_logger(__name__)

# Constants
MAX_RAM_GB = 7.0
MIN_CHUNK_SIZE = 1
MAX_CHUNK_SIZE = 16
RAM_TOLERANCE_GB = 0.5

def get_available_ram_gb() -> float:
    """Get available RAM in GB."""
    mem = psutil.virtual_memory()
    return mem.available / (1024 ** 3)

def estimate_memory_usage(chunk_size: int, model_params: int = 10_000_000) -> float:
    """
    Estimate memory usage for a given chunk size.
    Approximation: Model params + Batch images + Activations
    Assumes 4 bytes per float (float32).
    """
    # Model weights (float32)
    model_mem_gb = (model_params * 4) / (1024 ** 3)
    
    # Batch images: Assuming 256x256x3 images, 3 channels (input, mask, output)
    # 256*256*3*4 bytes = ~0.75MB per image per tensor.
    # We have input, mask, output, and maybe intermediate features.
    # Let's estimate 5 tensors per image.
    image_mem_per_chunk_gb = (chunk_size * 256 * 256 * 3 * 4 * 5) / (1024 ** 3)
    
    # Inception features (if loaded) - ~100MB
    inception_mem_gb = 0.1
    
    total_gb = model_mem_gb + image_mem_per_chunk_gb + inception_mem_gb
    return total_gb

def run_safe_evaluation(
    model_path: str,
    dataset_path: str,
    annotations_path: str,
    output_dir: str,
    initial_chunk_size: int = 4
) -> Dict[str, Any]:
    """
    Run evaluation with automatic chunk size reduction if OOM is detected.
    """
    available_ram = get_available_ram_gb()
    logger.info(f"Available RAM: {available_ram:.2f} GB")
    
    chunk_size = initial_chunk_size
    max_retries = 5
    
    # Load model to check size
    model = create_moebius_dynamic()
    if os.path.exists(model_path):
        state = torch.load(model_path, map_location='cpu')
        model.load_state_dict(state)
    
    param_count = sum(p.numel() for p in model.parameters())
    logger.info(f"Model parameters: {param_count:,}")
    
    last_error = None
    
    for attempt in range(max_retries):
        logger.info(f"Attempt {attempt + 1} with chunk_size={chunk_size}")
        
        # Check estimated usage
        est_usage = estimate_memory_usage(chunk_size, param_count)
        if est_usage > (available_ram - RAM_TOLERANCE_GB):
            logger.warning(f"Estimated usage {est_usage:.2f}GB exceeds available {available_ram:.2f}GB. Reducing chunk size.")
            chunk_size = max(MIN_CHUNK_SIZE, chunk_size // 2)
            continue
        
        try:
            ensure_directory(output_dir)
            results = run_metrics_evaluation(
                model_path=model_path,
                dataset_path=dataset_path,
                annotations_path=annotations_path,
                output_dir=output_dir,
                chunk_size=chunk_size
            )
            results['chunk_size_used'] = chunk_size
            results['attempt'] = attempt + 1
            return results
            
        except RuntimeError as e:
            if "CUDA" in str(e) or "out of memory" in str(e).lower():
                last_error = e
                logger.error(f"OOM detected. Reducing chunk size from {chunk_size} to {chunk_size // 2}")
                chunk_size = max(MIN_CHUNK_SIZE, chunk_size // 2)
            else:
                raise e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise e
    
    logger.critical("Failed to run evaluation after reducing chunk size to minimum.")
    raise RuntimeError(f"Evaluation failed due to memory constraints. Last error: {last_error}")

def main():
    parser = argparse.ArgumentParser(description="Run Chunked Evaluation")
    parser.add_argument("--model", type=str, required=True, help="Path to model weights")
    parser.add_argument("--dataset", type=str, required=True, help="Path to processed dataset directory")
    parser.add_argument("--annotations", type=str, required=True, help="Path to annotations CSV")
    parser.add_argument("--output", type=str, required=True, help="Output directory for results")
    parser.add_argument("--initial-chunk", type=int, default=8, help="Initial chunk size")
    
    args = parser.parse_args()
    
    results = run_safe_evaluation(
        model_path=args.model,
        dataset_path=args.dataset,
        annotations_path=args.annotations,
        output_dir=args.output,
        initial_chunk_size=args.initial_chunk
    )
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
