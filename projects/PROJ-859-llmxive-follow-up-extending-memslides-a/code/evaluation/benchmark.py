"""
Benchmarking Module for Agent Comparison.

Runs both Baseline and Compressed agents on a held-out test set
and generates a comparative report.
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import get_config
from utils.loaders import TraceLoader
from agents.baseline import BaselineAgent
from agents.compressed import CompressedAgent

class BenchmarkRunner:
    """Manages the execution of the agent comparison benchmark."""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.baseline_agent = BaselineAgent(self.config)
        self.compressed_agent = CompressedAgent(self.config)
        self.loader = TraceLoader(self.config)

    def load_test_set(self) -> List[Dict[str, Any]]:
        """Loads the held-out test set from data/raw/."""
        traces = []
        raw_dir = self.config.data_raw_path
        
        if not raw_dir.exists():
            raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
        
        session_files = list(raw_dir.glob("session_*.json"))
        if not session_files:
            raise ValueError(f"No session files found in {raw_dir}")
        
        for file_path in session_files:
            try:
                trace = self.loader.load_trace(file_path)
                if trace and "final_state" in trace:
                    traces.append(trace)
            except Exception as e:
                # Log warning but continue processing other traces
                print(f"Warning: Failed to load {file_path}: {e}")
                continue
        
        if not traces:
            raise ValueError("No valid traces loaded from the test set.")
        
        return traces

    def calculate_edit_accuracy(self, predicted: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
        """Calculates Edit Accuracy (exact match fraction)."""
        if not ground_truth:
            return 0.0 if not predicted else 0.0
        if not predicted:
            return 0.0
        
        # Exact match for structured objects
        if predicted == ground_truth:
            return 1.0
        
        # Fallback: key overlap ratio for partial credit if exact match fails
        p_keys = set(predicted.keys())
        g_keys = set(ground_truth.keys())
        if not p_keys or not g_keys:
            return 0.0
        
        matching = len(p_keys.intersection(g_keys))
        return matching / len(g_keys)

    def run_benchmark(self) -> Dict[str, Any]:
        """
        Executes the benchmark and returns the full result dictionary.
        Measures Edit Accuracy and Retrieval Latency for both agents.
        """
        test_set = self.load_test_set()
        
        results = []
        baseline_latencies = []
        compressed_latencies = []
        baseline_accuracies = []
        compressed_accuracies = []

        for trace in test_set:
            session_id = trace.get("session_id", "unknown")
            gt_state = trace.get("final_state", {})
            
            if not gt_state:
                print(f"Warning: Skipping {session_id} due to missing final_state.")
                continue

            # Baseline Agent
            t0 = time.perf_counter()
            try:
                pred_base, _ = self.baseline_agent.process_trace(trace)
                lat_base = time.perf_counter() - t0
                acc_base = self.calculate_edit_accuracy(pred_base, gt_state)
            except Exception as e:
                print(f"Error running baseline on {session_id}: {e}")
                lat_base = -1.0
                acc_base = 0.0
                pred_base = {}
            
            baseline_latencies.append(lat_base)
            baseline_accuracies.append(acc_base)
            
            # Compressed Agent
            t1 = time.perf_counter()
            try:
                pred_comp, _ = self.compressed_agent.process_trace(trace)
                lat_comp = time.perf_counter() - t1
                acc_comp = self.calculate_edit_accuracy(pred_comp, gt_state)
            except Exception as e:
                print(f"Error running compressed on {session_id}: {e}")
                lat_comp = -1.0
                acc_comp = 0.0
                pred_comp = {}
            
            compressed_latencies.append(lat_comp)
            compressed_accuracies.append(acc_comp)
            
            results.append({
                "session_id": session_id,
                "baseline": {"accuracy": acc_base, "latency": lat_base},
                "compressed": {"accuracy": acc_comp, "latency": lat_comp}
            })

        # Aggregate Statistics
        def safe_avg(vals):
            valid = [v for v in vals if v >= 0]
            return sum(valid) / len(valid) if valid else 0.0

        return {
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "num_traces": len(test_set),
                "baseline_agent": self.baseline_agent.name,
                "compressed_agent": self.compressed_agent.name
            },
            "aggregates": {
                "baseline": {
                    "edit_accuracy": safe_avg(baseline_accuracies),
                    "avg_retrieval_latency": safe_avg(baseline_latencies)
                },
                "compressed": {
                    "edit_accuracy": safe_avg(compressed_accuracies),
                    "avg_retrieval_latency": safe_avg(compressed_latencies)
                }
            },
            "per_trace_results": results
        }

    def save_report(self, report: Dict[str, Any], output_path: Optional[Path] = None):
        """Saves the benchmark report to JSON."""
        if output_path is None:
            output_path = self.config.data_processed_path / "benchmark_results.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

def main():
    """Entry point for running the full benchmark."""
    config = get_config()
    runner = BenchmarkRunner(config)
    
    print("Running benchmark...")
    try:
        report = runner.run_benchmark()
    except (FileNotFoundError, ValueError) as e:
        print(f"Benchmark failed: {e}")
        return
    
    print(f"Benchmark complete. Processed {report['metadata']['num_traces']} traces.")
    print(f"Baseline Accuracy: {report['aggregates']['baseline']['edit_accuracy']:.4f}")
    print(f"Compressed Accuracy: {report['aggregates']['compressed']['edit_accuracy']:.4f}")
    print(f"Baseline Avg Latency: {report['aggregates']['baseline']['avg_retrieval_latency']:.6f}s")
    print(f"Compressed Avg Latency: {report['aggregates']['compressed']['avg_retrieval_latency']:.6f}s")
    
    runner.save_report(report)
    print(f"Report saved to {config.data_processed_path / 'benchmark_results.json'}")

if __name__ == "__main__":
    main()