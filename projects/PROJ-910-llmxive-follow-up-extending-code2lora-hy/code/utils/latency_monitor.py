import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from utils.logging import get_logger

logger = get_logger(__name__)

def ensure_results_dir() -> Path:
    """Ensure the results directory exists."""
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def measure_baseline_generation_latency() -> float:
    """
    Measure the time taken to load the baseline neural-encoder adapter.
    
    This function loads the baseline adapter using the baseline_loader module
    and measures the elapsed time for the loading process.
    
    Returns:
        float: Time taken in seconds.
    """
    try:
        from evaluation.baseline_loader import load_baseline_adapter
        
        logger.info("Starting baseline adapter generation latency measurement...")
        start_time = time.perf_counter()
        
        # Load the baseline adapter (this simulates the generation/loading process)
        adapter_model = load_baseline_adapter()
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        
        logger.info(f"Baseline adapter loaded successfully in {elapsed_time:.4f} seconds.")
        return elapsed_time
        
    except Exception as e:
        logger.error(f"Error measuring baseline generation latency: {e}")
        raise

def save_latency_comparison(baseline_latency: float, ast_latency: Optional[float] = None) -> Dict[str, Any]:
    """
    Save latency comparison results to a JSON file.
    
    Args:
        baseline_latency: Time taken for baseline adapter generation (seconds).
        ast_latency: Optional time taken for AST-based adapter generation (seconds).
        
    Returns:
        Dict containing the comparison results.
    """
    results_dir = ensure_results_dir()
    output_path = results_dir / "generation_latency_comparison.json"
    
    comparison_data = {
        "baseline_generation_latency_seconds": baseline_latency,
        "ast_generation_latency_seconds": ast_latency,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    if ast_latency is not None and baseline_latency > 0:
        comparison_data["latency_reduction_ratio"] = baseline_latency / ast_latency
        comparison_data["meets_10x_requirement"] = (baseline_latency / ast_latency) >= 10.0
    
    with open(output_path, 'w') as f:
        json.dump(comparison_data, f, indent=2)
    
    logger.info(f"Latency comparison saved to {output_path}")
    return comparison_data

def run_latency_analysis() -> Tuple[float, Optional[float]]:
    """
    Run the full latency analysis for both baseline and AST-based adapters.
    
    Returns:
        Tuple of (baseline_latency, ast_latency) in seconds.
    """
    # Measure baseline latency
    baseline_latency = measure_baseline_generation_latency()
    
    # Measure AST-based adapter latency (if needed for comparison)
    # This would require implementing the AST adapter generation timing
    # For now, we return None for ast_latency
    ast_latency = None
    
    return baseline_latency, ast_latency

def main():
    """Main entry point for the latency monitoring script."""
    try:
        logger.info("Running baseline generation latency measurement...")
        
        baseline_latency, ast_latency = run_latency_analysis()
        
        # Save the results
        comparison_data = save_latency_comparison(baseline_latency, ast_latency)
        
        logger.info("Latency analysis completed successfully.")
        logger.info(f"Baseline latency: {comparison_data['baseline_generation_latency_seconds']:.4f}s")
        if 'latency_reduction_ratio' in comparison_data:
            logger.info(f"Latency reduction ratio: {comparison_data['latency_reduction_ratio']:.2f}x")
        
        return comparison_data
        
    except Exception as e:
        logger.error(f"Latency analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
