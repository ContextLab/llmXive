"""
Baseline Runner for ABot-AgentOS v1.0 (or mock fallback).

Executes the neural baseline on provided task traces and returns
success/latency metrics.

Dependencies:
- Uses `mock_baseline` if real ABot-AgentOS is unavailable (as per T027a).
- Writes metrics to `data/results/baseline_metrics.json`.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.config import RANDOM_SEED, MAX_TRACES
from code.metrics import MetricsLogger, MetricsEntry
from code.mock_baseline import run_baseline_simulation, generate_mock_traces

BASELINE_OUTPUT_DIR = PROJECT_ROOT / "data" / "results"
BASELINE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_traces(trace_source: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load task traces.
    
    If trace_source is provided, attempts to load from that path.
    Otherwise, generates mock traces using the baseline simulation generator
    (since T027a established the mock baseline as the fallback).
    """
    if trace_source and Path(trace_source).exists():
        with open(trace_source, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data[:MAX_TRACES]
            elif isinstance(data, dict) and "traces" in data:
                return data["traces"][:MAX_TRACES]
            else:
                raise ValueError("Trace file must contain a list of traces or a 'traces' key.")
    else:
        # Fallback to generating mock traces if no source is provided or file missing
        # This aligns with T027a's directive to use mock if real acquisition fails.
        print("No trace source provided or file missing. Generating mock traces for baseline run.")
        return generate_mock_traces(n=MAX_TRACES)

def run_baseline_on_traces(traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute the baseline (mock) on a list of traces.
    
    Returns a list of results containing:
    - trace_id
    - success (bool)
    - latency (float)
    - memory_usage (float, approximated)
    """
    results = []
    
    for i, trace in enumerate(traces):
        start_time = time.perf_counter()
        
        # Run the mock baseline simulation
        # This function is defined in code/mock_baseline.py as per API surface
        baseline_result = run_baseline_simulation(trace, seed=RANDOM_SEED + i)
        
        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000  # ms
        
        results.append({
            "trace_id": trace.get("id", f"trace_{i}"),
            "success": baseline_result.success,
            "latency_ms": latency,
            "memory_usage_mb": baseline_result.memory_mb,
            "details": baseline_result.details
        })
    
    return results

def aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results into summary statistics.
    """
    if not results:
        return {
            "total_traces": 0,
            "success_rate": 0.0,
            "avg_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "avg_memory_mb": 0.0
        }
    
    successes = [r["success"] for r in results]
    latencies = [r["latency_ms"] for r in results]
    memories = [r["memory_usage_mb"] for r in results]
    
    return {
        "total_traces": len(results),
        "success_rate": sum(successes) / len(successes),
        "avg_latency_ms": sum(latencies) / len(latencies),
        "max_latency_ms": max(latencies),
        "min_latency_ms": min(latencies),
        "avg_memory_mb": sum(memories) / len(memories),
        "max_memory_mb": max(memories)
    }

def save_metrics_report(results: List[Dict[str, Any]], summary: Dict[str, Any], output_path: str):
    """
    Save the full results and summary to a JSON file.
    """
    report = {
        "summary": summary,
        "individual_results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Baseline metrics saved to {output_path}")

def main():
    """
    Main entry point for the baseline runner.
    """
    print("Starting Baseline Runner (T027)...")
    
    # Initialize metrics logger if needed, though we are writing directly to JSON for this task
    # We can also log to the MetricsLogger if we want to integrate with the existing system
    logger = MetricsLogger(output_dir=BASELINE_OUTPUT_DIR)
    
    # Load traces
    traces = load_traces()
    print(f"Loaded {len(traces)} traces.")
    
    if not traces:
        print("No traces to process. Exiting.")
        return
    
    # Run baseline
    print("Running baseline simulation...")
    results = run_baseline_on_traces(traces)
    
    # Aggregate
    summary = aggregate_metrics(results)
    
    # Log to MetricsLogger as well (optional but good practice)
    for r in results:
        logger.log_success(r["success"])
        logger.log_latency(r["latency_ms"])
        logger.log_memory(r["memory_usage_mb"])
    
    # Save report
    output_path = str(BASELINE_OUTPUT_DIR / "baseline_metrics.json")
    save_metrics_report(results, summary, output_path)
    
    # Save the metrics report from the logger as well
    logger.save_report(str(BASELINE_OUTPUT_DIR / "baseline_metrics_log.json"))
    
    print("Baseline Runner completed successfully.")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    main()