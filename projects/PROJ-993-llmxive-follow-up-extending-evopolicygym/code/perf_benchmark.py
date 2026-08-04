"""
Benchmark script to measure inference performance under various conditions.

This script:
1. Loads a small CPU-quantized model
2. Runs inference with different batch sizes
3. Measures latency and throughput
4. Outputs results to data/perf_benchmark_results.json

Usage:
    python code/perf_benchmark.py
"""
import os
import sys
import json
import time
import logging
from typing import List, Dict, Any
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.utils.perf_optimizer import (
    load_model_with_mmap,
    enforce_timeout,
    adaptive_batch_size,
    PerformanceMonitor,
    record_metric,
    get_performance_report,
    get_optimization_config
)
from code.utils.logging import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use a small, publicly available model for benchmarking
TEST_MODEL_ID = "hf-internal-testing/tiny-random-LlamaForCausalLM"


def generate_test_prompts(num_prompts: int = 10) -> List[str]:
    """Generate simple test prompts for benchmarking."""
    return [
        f"Prompt {i}: The quick brown fox jumps over the lazy dog."
        for i in range(num_prompts)
    ]


def run_single_inference(model, tokenizer, prompt: str, max_new_tokens: int = 10) -> Dict[str, Any]:
    """Run inference on a single prompt and return metrics."""
    inputs = tokenizer(prompt, return_tensors="pt")
    
    with PerformanceMonitor(f"inference_{len(prompt)}") as monitor:
        try:
            with enforce_timeout(60):  # 60s timeout per prompt
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id
                )
                result = tokenizer.decode(outputs[0], skip_special_tokens=True)
                return {
                    "prompt_length": len(prompt),
                    "success": True,
                    "output": result[:50] + "..."  # Truncate for logging
                }
        except Exception as e:
            return {
                "prompt_length": len(prompt),
                "success": False,
                "error": str(e)
            }


@adaptive_batch_size
def run_batch_inference(model, tokenizer, prompts: List[str], max_new_tokens: int = 10):
    """Run inference on a batch of prompts."""
    results = []
    for prompt in prompts:
        result = run_single_inference(model, tokenizer, prompt, max_new_tokens)
        results.append(result)
    return results


def run_benchmark(num_prompts: int = 20, batch_sizes: List[int] = None) -> Dict[str, Any]:
    """
    Run full performance benchmark.
    
    Args:
        num_prompts: Number of test prompts to generate.
        batch_sizes: List of batch sizes to test.
        
    Returns:
        Dictionary of benchmark results.
    """
    if batch_sizes is None:
        batch_sizes = [1, 2, 4, 8]
        
    logger.info(f"Loading model: {TEST_MODEL_ID}")
    try:
        model, tokenizer = load_model_with_mmap(TEST_MODEL_ID)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return {"error": str(e), "success": False}
        
    prompts = generate_test_prompts(num_prompts)
    results = {
        "model": TEST_MODEL_ID,
        "num_prompts": num_prompts,
        "batch_tests": [],
        "config": get_optimization_config()
    }
    
    for batch_size in batch_sizes:
        if batch_size > len(prompts):
            continue
            
        logger.info(f"Testing batch size: {batch_size}")
        test_prompts = prompts[:batch_size]
        
        start_time = time.time()
        try:
            batch_results = run_batch_inference(model, tokenizer, test_prompts)
            elapsed = time.time() - start_time
            
            success_count = sum(1 for r in batch_results if r.get("success", False))
            results["batch_tests"].append({
                "batch_size": batch_size,
                "elapsed_seconds": elapsed,
                "throughput_prompts_per_sec": batch_size / elapsed if elapsed > 0 else 0,
                "success_count": success_count,
                "total_count": len(batch_results)
            })
            
            logger.info(f"Batch {batch_size}: {elapsed:.2f}s ({success_count}/{len(batch_results)} success)")
            
        except Exception as e:
            logger.error(f"Batch {batch_size} failed: {e}")
            results["batch_tests"].append({
                "batch_size": batch_size,
                "error": str(e),
                "success": False
            })
            
    # Record global metrics
    report = get_performance_report()
    results["summary"] = report["summary"]
    results["success"] = True
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Run performance benchmark")
    parser.add_argument("--num-prompts", type=int, default=20, help="Number of test prompts")
    parser.add_argument("--batch-sizes", type=str, default="1,2,4,8", help="Comma-separated batch sizes")
    parser.add_argument("--output", type=str, default="data/perf_benchmark_results.json", help="Output file path")
    
    args = parser.parse_args()
    
    batch_sizes = [int(x) for x in args.batch_sizes.split(",")]
    
    logger.info(f"Starting benchmark with {args.num_prompts} prompts")
    results = run_benchmark(args.num_prompts, batch_sizes)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    # Write results
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Benchmark results written to {args.output}")
    
    # Print summary
    if results.get("success"):
        for test in results["batch_tests"]:
            if "error" not in test:
                print(f"Batch {test['batch_size']}: {test['throughput_prompts_per_sec']:.2f} prompts/sec")
    else:
        print(f"Benchmark failed: {results.get('error', 'Unknown error')}")
        
    return 0 if results.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())