"""
Latency monitoring utilities for adapter generation.

This module measures the time taken to generate adapters using the AST-based
hypernetwork approach and compares it against the baseline neural-encoder
generation time (Code2LoRA).

It addresses SC-001 by quantifying the latency reduction achieved by the
static AST-based method.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from utils.logging import get_logger
from evaluation.baseline_loader import load_baseline_adapter, get_baseline_adapter_path

# Ensure results directory exists
RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)


def measure_generation_latency(
    generate_func: callable,
    *args,
    **kwargs
) -> Tuple[float, Any]:
    """
    Measure the execution time of a generation function.

    Args:
        generate_func: The function to measure (e.g., train_mlp_projection).
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        A tuple containing (elapsed_time_seconds, return_value).
    """
    logger.info("Starting latency measurement for generation function...")
    start_time = time.perf_counter()
    try:
        result = generate_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Generation function failed during measurement: {e}")
        raise
    finally:
        end_time = time.perf_counter()

    elapsed = end_time - start_time
    logger.info(f"Generation completed in {elapsed:.4f} seconds.")
    return elapsed, result


def measure_baseline_generation_latency() -> float:
    """
    Measure the generation latency of the baseline Code2LoRA neural encoder.

    This simulates the baseline generation process by loading the baseline
    adapter configuration and performing a mock generation step (or timing
    the loading process if generation is pre-computed). For the purpose of
    this metric, we time the `load_baseline_adapter` process as a proxy
    for the "generation" overhead in a real-time scenario, or we time a
    dummy training step if the baseline involves training.

    Since the baseline adapter is pre-trained in this context, we measure
    the time to load and instantiate it, which represents the inference-time
    cost of the baseline encoder compared to the AST generation time.
    Note: If the baseline requires training, this function would need to
    wrap the training loop. Here we assume the baseline is loaded.

    Returns:
        Elapsed time in seconds.
    """
    logger.info("Measuring baseline generation (loading) latency...")
    baseline_path = get_baseline_adapter_path()
    
    if not baseline_path.exists():
        logger.warning(f"Baseline adapter not found at {baseline_path}. "
                       "Skipping baseline latency measurement.")
        return 0.0

    start_time = time.perf_counter()
    try:
        # Load the baseline adapter
        load_baseline_adapter()
    except Exception as e:
        logger.error(f"Failed to load baseline adapter: {e}")
        return 0.0
    finally:
        end_time = time.perf_counter()

    elapsed = end_time - start_time
    logger.info(f"Baseline load completed in {elapsed:.4f} seconds.")
    return elapsed


def save_latency_comparison(
    ast_latency: float,
    baseline_latency: float,
    output_path: Optional[Path] = None
) -> Path:
    """
    Save the latency comparison report to a JSON file.

    Args:
        ast_latency: Time taken for AST-based generation.
        baseline_latency: Time taken for baseline generation.
        output_path: Optional custom output path. Defaults to data/results/generation_latency_comparison.json.

    Returns:
        The path to the saved JSON file.
    """
    if output_path is None:
        output_path = RESULTS_DIR / "generation_latency_comparison.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "ast_generation_latency_seconds": ast_latency,
        "baseline_generation_latency_seconds": baseline_latency,
        "latency_reduction_ratio": baseline_latency / ast_latency if ast_latency > 0 else float('inf'),
        "meets_sc001_requirement": baseline_latency >= (10 * ast_latency) if ast_latency > 0 else False,
        "notes": "SC-001 requires AST generation to be at least 10x faster than baseline."
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Latency comparison report saved to {output_path}")
    return output_path


def run_latency_analysis(
    ast_generate_func: callable,
    *ast_args,
    **ast_kwargs
) -> Dict[str, Any]:
    """
    Run a full latency analysis comparing AST-based generation to baseline.

    This function measures the AST generation time, measures the baseline
    generation time, and saves the comparison report.

    Args:
        ast_generate_func: The AST-based generation function (e.g., from adapter_generator).
        *ast_args: Arguments for the AST generation function.
        **ast_kwargs: Keyword arguments for the AST generation function.

    Returns:
        A dictionary containing the analysis results.
    """
    logger.info("Starting full latency analysis...")

    # 1. Measure AST generation latency
    ast_latency, _ = measure_generation_latency(ast_generate_func, *ast_args, **ast_kwargs)

    # 2. Measure baseline generation latency
    baseline_latency = measure_baseline_generation_latency()

    # 3. Save report
    report_path = save_latency_comparison(ast_latency, baseline_latency)

    return {
        "ast_latency": ast_latency,
        "baseline_latency": baseline_latency,
        "report_path": str(report_path)
    }


def main():
    """
    Main entry point for running latency analysis as a standalone script.
    This is intended to be called from the main pipeline or for testing.
    """
    logger.info("Running latency monitor main...")
    # This would typically be called by the adapter_generator or main.py
    # with the specific generation function.
    # For now, we log that it's ready to be integrated.
    print("Latency monitor module loaded. Call run_latency_analysis() with a generation function.")


if __name__ == "__main__":
    main()
