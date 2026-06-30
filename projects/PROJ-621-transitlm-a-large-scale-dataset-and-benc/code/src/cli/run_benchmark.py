"""
End-to-end benchmark runner for map-free transit route generation.

Orchestrates:
1. Loading the held-out test set (O-D pairs).
2. Running LLM inference for N=100 samples.
3. Parsing LLM output into station sequences.
4. Validating sequences against the ground-truth GTFS graph.
5. Measuring and reporting total inference time and validation metrics.
"""
import argparse
import json
import logging
import time
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lib.config import set_seed, get_logger, init_project_config
from src.lib.memory_monitor import get_current_memory_usage_bytes, format_bytes
from src.lib.text_utils import parse_llm_route_output
from src.models.validation import validate_route_sequence
from src.models.inference import run_inference_batch
from src.contracts.models import GTFSGraph, load_graph_from_json

logger = get_logger(__name__)

def load_test_od_pairs(file_path: Path) -> List[Dict[str, str]]:
    """Load the held-out test set of O-D pairs."""
    if not file_path.exists():
        raise FileNotFoundError(f"Test O-D pairs file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Expecting a list of dicts with 'origin' and 'destination'
    return data

def run_benchmark(
    graph_path: Path,
    test_od_path: Path,
    output_path: Path,
    n_samples: int = 100,
    seed: int = 42,
    max_memory_gb: float = 7.0
) -> Dict[str, Any]:
    """
    Run the end-to-end benchmark.
    
    Args:
        graph_path: Path to the ground-truth GTFS graph JSON.
        test_od_path: Path to the JSON file containing O-D pairs.
        output_path: Path to write the benchmark results JSON.
        n_samples: Number of samples to process (default 100).
        seed: Random seed for reproducibility.
        max_memory_gb: Maximum allowed memory in GB.
        
    Returns:
        Dictionary containing benchmark metrics.
    """
    set_seed(seed)
    init_project_config(project_root)
    
    logger.info(f"Starting benchmark with N={n_samples} samples")
    logger.info(f"Loading graph from: {graph_path}")
    
    # Load ground-truth graph
    graph_data = load_graph_from_json(graph_path)
    graph = GTFSGraph(**graph_data)
    
    # Load test O-D pairs
    od_pairs = load_test_od_pairs(test_od_path)
    if len(od_pairs) < n_samples:
        logger.warning(f"Only {len(od_pairs)} O-D pairs available, using all.")
        n_samples = len(od_pairs)
    else:
        od_pairs = od_pairs[:n_samples]
    
    logger.info(f"Loaded {len(od_pairs)} O-D pairs for testing")
    
    # Prepare inputs for inference
    # Assuming the inference wrapper expects a list of prompts or O-D pairs
    # Based on T018, we assume run_inference_batch takes a list of O-D pairs
    # and returns a list of raw LLM outputs (strings).
    inputs = od_pairs
    
    results = []
    total_inference_time = 0.0
    valid_count = 0
    invalid_count = 0
    exact_match_count = 0
    
    logger.info("Starting inference and validation loop...")
    
    start_time = time.time()
    
    # Process in batches if possible, but for N=100 and strict memory,
    # we might process one by one or small batches.
    # run_inference_batch handles the batching internally if implemented correctly.
    # For this benchmark, we call it with the full slice.
    
    try:
        # T018 (inference.py) is expected to return raw text outputs
        raw_outputs = run_inference_batch(inputs, graph=graph)
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise
    
    inference_end_time = time.time()
    total_inference_time = inference_end_time - start_time
    
    logger.info(f"Inference completed in {total_inference_time:.2f}s")
    
    # Validate each output
    for i, (od_pair, raw_output) in enumerate(zip(od_pairs, raw_outputs)):
        # Parse LLM output
        try:
            sequence = parse_llm_route_output(raw_output)
        except Exception as e:
            logger.warning(f"Failed to parse output for O-D {i}: {e}")
            sequence = []
        
        # Validate against graph
        validation_result = validate_route_sequence(sequence, graph)
        
        result_entry = {
            "index": i,
            "origin": od_pair["origin"],
            "destination": od_pair["destination"],
            "raw_output": raw_output,
            "parsed_sequence": sequence,
            "is_valid": validation_result.is_valid,
            "exact_match": validation_result.exact_match_score == 1.0,
            "validation_details": {
                "has_infinite_loop": validation_result.has_infinite_loop,
                "has_hallucinated_station": validation_result.has_hallucinated_station,
                "is_connected": validation_result.is_connected
            }
        }
        results.append(result_entry)
        
        if validation_result.is_valid:
            valid_count += 1
            if validation_result.exact_match_score == 1.0:
                exact_match_count += 1
        else:
            invalid_count += 1
        
        if (i + 1) % 20 == 0:
            logger.info(f"Processed {i + 1}/{len(od_pairs)} samples")
    
    # Calculate metrics
    total_time = time.time() - start_time
    avg_time_per_sample = total_time / n_samples if n_samples > 0 else 0.0
    validity_rate = valid_count / n_samples if n_samples > 0 else 0.0
    exact_match_rate = exact_match_count / n_samples if n_samples > 0 else 0.0
    
    metrics = {
        "benchmark_config": {
            "n_samples": n_samples,
            "seed": seed,
            "max_memory_gb": max_memory_gb,
            "graph_file": str(graph_path),
            "test_file": str(test_od_path)
        },
        "timing": {
            "total_time_seconds": total_time,
            "inference_time_seconds": total_inference_time,
            "avg_time_per_sample_seconds": avg_time_per_sample
        },
        "counts": {
            "total": n_samples,
            "valid": valid_count,
            "invalid": invalid_count,
            "exact_match": exact_match_count
        },
        "rates": {
            "validity_rate": validity_rate,
            "exact_match_rate": exact_match_rate
        },
        "memory": {
            "peak_memory_gb": format_bytes(get_current_memory_usage_bytes())
        },
        "results": results
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Benchmark complete. Results written to: {output_path}")
    logger.info(f"Validity Rate: {validity_rate:.2%}, Exact Match Rate: {exact_match_rate:.2%}")
    logger.info(f"Total Time: {total_time:.2f}s ({avg_time_per_sample:.2f}s/sample)")
    
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Run end-to-end benchmark for map-free transit generation.")
    parser.add_argument("--graph", type=str, required=True, help="Path to ground-truth GTFS graph JSON.")
    parser.add_argument("--test-data", type=str, required=True, help="Path to test O-D pairs JSON.")
    parser.add_argument("--output", type=str, required=True, help="Path to output results JSON.")
    parser.add_argument("--n-samples", type=int, default=100, help="Number of samples to process.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--max-memory-gb", type=float, default=7.0, help="Max memory constraint in GB.")
    
    args = parser.parse_args()
    
    graph_path = Path(args.graph)
    test_od_path = Path(args.test_data)
    output_path = Path(args.output)
    
    try:
        run_benchmark(
            graph_path=graph_path,
            test_od_path=test_od_path,
            output_path=output_path,
            n_samples=args.n_samples,
            seed=args.seed,
            max_memory_gb=args.max_memory_gb
        )
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()