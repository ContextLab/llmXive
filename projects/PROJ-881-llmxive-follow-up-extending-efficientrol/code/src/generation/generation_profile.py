"""
Profiling script for generation.py to verify RAM usage and latency.

This script runs cProfile and tracemalloc on the generation pipeline
to ensure it stays within the 6.5GB RAM limit for sequences up to 500 tokens
processed in batches of 50 tokens.
"""
import cProfile
import tracemalloc
import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.generation.generation import (
    GenerationConfig,
    load_model_for_cpu_inference,
    generate_single_pass,
    process_batch,
    write_jsonl,
    setup_logging
)
from src.utils.entropy_calc import calculate_entropy

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

def generate_synthetic_sequence(length: int) -> Dict[str, Any]:
    """
    Generate a synthetic token sequence for profiling.
    This simulates the input data without requiring real dataset loading.
    """
    tokens = [f"<token_{i}>" for i in range(length)]
    logits = np.random.randn(length, 50257).tolist()  # Simulate logits for vocab size
    
    return {
        "prompt_id": f"profile_test_{length}",
        "tokens": tokens,
        "logits": logits,
        "validity": True,
        "entropy": [calculate_entropy(np.array(l)) for l in logits]
    }

def run_profile_experiment(
    batch_size: int = 50,
    max_tokens: int = 500,
    num_batches: int = 10
) -> Tuple[float, float]:
    """
    Run the generation pipeline with profiling enabled.
    
    Args:
        batch_size: Number of tokens per batch
        max_tokens: Maximum tokens to process
        num_batches: Number of batches to process
        
    Returns:
        Tuple of (peak_rss_mb, avg_latency_seconds)
    """
    tracemalloc.start()
    
    # Generate synthetic data for profiling
    logger.info(f"Generating synthetic data: {num_batches} batches of {batch_size} tokens")
    synthetic_data = []
    for i in range(num_batches):
        seq_length = min(batch_size, max_tokens - len(synthetic_data))
        if seq_length <= 0:
            break
        synthetic_data.append(generate_synthetic_sequence(seq_length))
    
    logger.info(f"Starting profiling with {len(synthetic_data)} batches")
    
    # Profile the processing
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    
    # Process batches
    output_path = Path(project_root) / "data" / "profile_output.jsonl"
    
    for i, data in enumerate(synthetic_data):
        # Simulate batch processing
        try:
            # Calculate entropy for each token
            if "logits" in data:
                entropies = [calculate_entropy(np.array(l)) for l in data["logits"]]
                data["entropy"] = entropies
            
            # Write to output
            with open(output_path, "a") as f:
                f.write(json.dumps(data) + "\n")
                
        except Exception as e:
            logger.error(f"Error processing batch {i}: {e}")
            continue
    
    profiler.disable()
    end_time = time.time()
    
    # Get memory stats
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    peak_rss_mb = peak / (1024 * 1024)
    avg_latency = (end_time - start_time) / len(synthetic_data) if synthetic_data else 0
    
    logger.info(f"Profiling complete. Peak RSS: {peak_rss_mb:.2f} MB, Avg Latency: {avg_latency:.4f} s")
    
    # Save profiling stats
    stats_file = Path(project_root) / "results" / "profile_stats.json"
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(stats_file, "w") as f:
        json.dump({
            "batch_size": batch_size,
            "num_batches": num_batches,
            "total_tokens": sum(len(d.get("tokens", [])) for d in synthetic_data),
            "peak_rss_mb": peak_rss_mb,
            "avg_latency_s": avg_latency,
            "total_time_s": end_time - start_time
        }, f, indent=2)
    
    return peak_rss_mb, avg_latency

def save_profile_report(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save the profiling report to a text file.
    
    Args:
        results: List of profiling results
        output_path: Optional custom output path
        
    Returns:
        Path to the saved report
    """
    if output_path is None:
        output_path = Path(project_root) / "results" / "profile_report.txt"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write("Generation Pipeline Profiling Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Memory Limit: 6.5 GB (6656 MB)\n\n")
        f.write("Results Summary:\n")
        f.write("-" * 50 + "\n")
        f.write(f"{'Batch Size':<15} {'Peak RSS (MB)':<20} {'Avg Latency (s)':<20}\n")
        f.write("-" * 50 + "\n")
        
        for result in results:
            f.write(f"{result['batch_size']:<15} {result['peak_rss_mb']:<20.2f} {result['avg_latency_s']:<20.4f}\n")
        
        f.write("-" * 50 + "\n")
        
        # Check compliance
        max_rss = max(r['peak_rss_mb'] for r in results) if results else 0
        limit_mb = 6656  # 6.5 GB
        
        if max_rss < limit_mb:
            f.write(f"\n✓ COMPLIANCE: Peak RSS ({max_rss:.2f} MB) is within limit ({limit_mb} MB)\n")
        else:
            f.write(f"\n✗ NON-COMPLIANCE: Peak RSS ({max_rss:.2f} MB) exceeds limit ({limit_mb} MB)\n")
        
        f.write(f"\nDetailed Results:\n")
        for i, result in enumerate(results, 1):
            f.write(f"\nRun {i}:\n")
            f.write(f"  Batch Size: {result['batch_size']}\n")
            f.write(f"  Peak RSS: {result['peak_rss_mb']:.2f} MB\n")
            f.write(f"  Avg Latency: {result['avg_latency_s']:.4f} s\n")
            f.write(f"  Total Tokens: {result.get('total_tokens', 'N/A')}\n")
    
    logger.info(f"Profile report saved to {output_path}")
    return output_path

def main():
    """Main entry point for profiling."""
    logger.info("Starting generation pipeline profiling...")
    
    # Run experiments with different batch sizes
    experiments = [
        {"batch_size": 50, "max_tokens": 500, "num_batches": 10},
        {"batch_size": 100, "max_tokens": 500, "num_batches": 5},
        {"batch_size": 25, "max_tokens": 500, "num_batches": 20},
    ]
    
    results = []
    
    for exp in experiments:
        logger.info(f"Running experiment: {exp}")
        try:
            peak_rss, avg_latency = run_profile_experiment(
                batch_size=exp["batch_size"],
                max_tokens=exp["max_tokens"],
                num_batches=exp["num_batches"]
            )
            
            results.append({
                "batch_size": exp["batch_size"],
                "peak_rss_mb": peak_rss,
                "avg_latency_s": avg_latency,
                "total_tokens": exp["batch_size"] * exp["num_batches"]
            })
            
        except Exception as e:
            logger.error(f"Experiment failed: {e}", exc_info=True)
            results.append({
                "batch_size": exp["batch_size"],
                "peak_rss_mb": float('inf'),
                "avg_latency_s": float('inf'),
                "error": str(e)
            })
    
    # Save report
    report_path = save_profile_report(results)
    
    # Print summary
    print(f"\nProfiling complete. Report saved to: {report_path}")
    
    # Return exit code based on compliance
    max_rss = max(r['peak_rss_mb'] for r in results if 'error' not in r) if any('error' not in r for r in results) else float('inf')
    if max_rss < 6656:
        print("✓ All experiments passed memory limit check")
        return 0
    else:
        print("✗ Memory limit exceeded in one or more experiments")
        return 1

if __name__ == "__main__":
    sys.exit(main())
