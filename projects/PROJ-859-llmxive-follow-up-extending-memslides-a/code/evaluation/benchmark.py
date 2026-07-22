"""
Benchmark runner to compare BaselineAgent and CompressedAgent on the held-out test set.
Implements FR-004: Run both agents on the held-out test set.
"""

import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Project imports based on API surface
from config import get_config
from utils.loaders import TraceLoader
from agents.baseline import BaselineAgent
from agents.compressed import CompressedAgent


class BenchmarkRunner:
    """
    Orchestrates the benchmarking of Baseline and Compressed agents.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.held_out_dir = Path(config['paths']['held_out'])
        self.output_dir = Path(config['paths']['processed'])
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize agents
        self.baseline_agent = BaselineAgent(config)
        self.compressed_agent = CompressedAgent(config)

        # Results storage
        self.results: List[Dict[str, Any]] = []

    def load_held_out_traces(self) -> List[Dict[str, Any]]:
        """
        Loads all traces from the held-out directory.
        Raises FileNotFoundError if the directory is empty or missing.
        """
        loader = TraceLoader()
        traces = []
        
        if not self.held_out_dir.exists():
            raise FileNotFoundError(f"Held-out directory not found: {self.held_out_dir}")

        json_files = list(self.held_out_dir.glob("*.json"))
        if not json_files:
            raise ValueError(f"No JSON trace files found in {self.held_out_dir}")

        for file_path in json_files:
            try:
                trace = loader.load_trace(file_path)
                traces.append(trace)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}", file=sys.stderr)
        
        return traces

    def run_single_trace(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs a single trace against both agents and records metrics.
        """
        trace_id = trace.get('trace_id', str(trace.get('id', 'unknown')))
        ground_truth = trace.get('final_state')

        if not ground_truth:
            raise ValueError(f"Trace {trace_id} missing 'final_state' ground truth.")

        # --- Baseline Agent ---
        start_time = time.perf_counter()
        try:
            baseline_result = self.baseline_agent.process(trace)
        except Exception as e:
            baseline_result = {'final_state': None, 'error': str(e)}
        baseline_latency = time.perf_counter() - start_time

        # --- Compressed Agent ---
        start_time = time.perf_counter()
        try:
            compressed_result = self.compressed_agent.process(trace)
        except Exception as e:
            compressed_result = {'final_state': None, 'error': str(e)}
        compressed_latency = time.perf_counter() - start_time

        # Calculate Edit Accuracy (Exact Match for this benchmark scope)
        # Note: FR-005 specifies Edit Accuracy. For this implementation, 
        # we assume exact structural match for simplicity unless a diff lib is requested.
        # A more complex edit distance could be implemented if ground_truth and result are complex objects.
        baseline_acc = 1.0 if baseline_result.get('final_state') == ground_truth else 0.0
        compressed_acc = 1.0 if compressed_result.get('final_state') == ground_truth else 0.0

        return {
            "trace_id": trace_id,
            "baseline_accuracy": baseline_acc,
            "baseline_latency_ms": baseline_latency * 1000,
            "compressed_accuracy": compressed_acc,
            "compressed_latency_ms": compressed_latency * 1000,
            "baseline_error": baseline_result.get('error'),
            "compressed_error": compressed_result.get('error')
        }

    def run_benchmark(self) -> List[Dict[str, Any]]:
        """
        Runs the benchmark on all held-out traces.
        """
        print(f"Starting benchmark on held-out set: {self.held_out_dir}")
        traces = self.load_held_out_traces()
        print(f"Loaded {len(traces)} traces.")

        for i, trace in enumerate(traces):
            trace_id = trace.get('trace_id', 'unknown')
            print(f"Processing [{i+1}/{len(traces)}]: {trace_id}")
            try:
                result = self.run_single_trace(trace)
                self.results.append(result)
            except Exception as e:
                print(f"Error processing {trace_id}: {e}", file=sys.stderr)
                # Log failure but continue with next trace
                self.results.append({
                    "trace_id": trace_id,
                    "baseline_accuracy": 0.0,
                    "baseline_latency_ms": 0.0,
                    "compressed_accuracy": 0.0,
                    "compressed_latency_ms": 0.0,
                    "baseline_error": str(e),
                    "compressed_error": str(e)
                })

        return self.results

    def save_results(self):
        """
        Saves the benchmark results to a JSON file.
        """
        if not self.results:
            raise RuntimeError("No results to save. Run benchmark first.")

        output_path = self.output_dir / "benchmark_results.json"
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Benchmark results saved to: {output_path}")
        return output_path


def main():
    """
    Entry point for the benchmark script.
    """
    config = get_config()
    
    # Dependency check: Ensure global rules exist (T026b output)
    global_rules_path = Path(config['paths']['processed']) / "rules" / "global_rules.json"
    if not global_rules_path.exists():
        raise FileNotFoundError(
            f"Global rules file not found at {global_rules_path}. "
            "Please ensure T026b (Rule Induction/Aggregation) has completed successfully."
        )

    # Dependency check: Ensure held-out data exists (T012 output)
    held_out_path = Path(config['paths']['held_out'])
    if not held_out_path.exists() or not list(held_out_path.glob("*.json")):
        raise FileNotFoundError(
            f"Held-out data not found at {held_out_path}. "
            "Please ensure T012 (Synthetic Trace Generation) has completed successfully."
        )

    runner = BenchmarkRunner(config)
    runner.run_benchmark()
    runner.save_results()

    # Print summary
    if runner.results:
        total = len(runner.results)
        baseline_accs = [r['baseline_accuracy'] for r in runner.results if r.get('baseline_error') is None]
        compressed_accs = [r['compressed_accuracy'] for r in runner.results if r.get('compressed_error') is None]
        
        avg_baseline = sum(baseline_accs) / len(baseline_accs) if baseline_accs else 0.0
        avg_compressed = sum(compressed_accs) / len(compressed_accs) if compressed_accs else 0.0
        
        print(f"\n--- Benchmark Summary ---")
        print(f"Total Traces: {total}")
        print(f"Baseline Avg Accuracy: {avg_baseline:.4f}")
        print(f"Compressed Avg Accuracy: {avg_compressed:.4f}")
        print(f"Accuracy Delta (Baseline - Compressed): {avg_baseline - avg_compressed:.4f}")


if __name__ == "__main__":
    main()