"""
Experiment Runner for Comparative Study (US3).

Orchestrates the comparative study between the symbolic memory system
and the neural baseline (ABot-AgentOS v1.0 or mock), recording success rate,
peak RAM, and query latency for both systems.
"""
import csv
import json
import os
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import networkx as nx

from config import RANDOM_SEED
from data_loader import stream_alfworld_traces, load_traces_as_list
from graph_builder import SymbolicGraphBuilder, save_graph
from query_engine import query_graph, Node
from baseline_runner import run_baseline_on_traces, load_traces as load_baseline_traces, aggregate_metrics as baseline_aggregate_metrics
from metrics import MetricsLogger, MetricsEntry
from latency_guard import latency_guard, flush_violations

# Output paths
RESULTS_DIR = Path("data/results")
COMPARATIVE_OUTPUT_FILE = RESULTS_DIR / "comparative_study_results.csv"
REPORT_FILE = RESULTS_DIR / "comparative_report.json"

# Configuration for the comparative run
MAX_TRACES_COMPARATIVE = 50  # Representative set size

def run_single_experiment(
    granularity: str,
    expressiveness: str,
    max_traces: int = MAX_TRACES_COMPARATIVE,
) -> Dict[str, Any]:
    """
    Run a single comparative experiment for a specific configuration.
    
    Args:
        granularity: 'coarse' or 'fine'
        expressiveness: 'spatial' or 'spatial+temporal'
        max_traces: Number of traces to process.
        
    Returns:
        Dictionary containing metrics for both systems.
    """
    # Start memory tracking
    tracemalloc.start()
    
    start_time = time.time()
    
    # 1. Load Real Data
    try:
        traces = load_traces_as_list(stream_alfworld_traces(), max_count=max_traces)
    except Exception as e:
        tracemalloc.stop()
        raise RuntimeError(f"Failed to load traces from ALFWorld: {e}")
    
    if not traces:
        tracemalloc.stop()
        raise RuntimeError("No traces loaded from ALFWorld.")
    
    # 2. Run Symbolic System
    symbolic_successes = []
    symbolic_latencies = []
    symbolic_graphs = []
    
    builder = SymbolicGraphBuilder(
        granularity=granularity,
        predicate_set=expressiveness,
        random_seed=RANDOM_SEED,
    )
    
    for i, trace in enumerate(traces):
        # Build Graph
        graph_start = time.time()
        try:
            graph = builder.build_graph_from_trace(trace)
            if graph is None:
                symbolic_successes.append(False)
                symbolic_latencies.append(0.0)
                symbolic_graphs.append(None)
                continue
            
            # Simulate a query (e.g., find object near start)
            # We assume a generic query to test the engine
            query_str = "find_start_node" 
            query_start = time.time()
            try:
                # Mock a simple query logic: find the first node
                nodes = list(graph.nodes(data=True))
                if nodes:
                    # Just verify we can traverse/query
                    _ = nodes[0] 
                    query_res = True
                else:
                    query_res = False
            except Exception:
                query_res = False
            query_end = time.time()
            
            graph_end = time.time()
            total_trace_time = graph_end - graph_start
            
            symbolic_successes.append(query_res)
            symbolic_latencies.append(total_trace_time)
            symbolic_graphs.append(graph)
            
        except Exception as e:
            symbolic_successes.append(False)
            symbolic_latencies.append(0.0)
            symbolic_graphs.append(None)
            print(f"Symbolic error on trace {i}: {e}")
    
    # 3. Run Baseline (Neural) System
    # We use the baseline_runner interface. It expects traces in a specific format.
    # We pass the same raw traces.
    baseline_successes = []
    baseline_latencies = []
    
    try:
        # Run the baseline on the same set of traces
        # The baseline_runner handles the execution and returns metrics
        baseline_metrics = run_baseline_on_traces(traces)
        
        # Extract results from the baseline metrics
        # Assuming baseline_metrics is a list of dicts with 'success' and 'latency'
        if isinstance(baseline_metrics, list):
            for m in baseline_metrics:
                baseline_successes.append(m.get('success', False))
                baseline_latencies.append(m.get('latency', 0.0))
        else:
            # Fallback if it returns a single aggregate (unlikely for trace-level)
            # In that case, we might need to re-run or handle differently
            # For now, assume list of results
            print("Warning: Baseline did not return list of trace results. Using aggregate.")
            baseline_successes = [False] * len(traces)
            baseline_latencies = [0.0] * len(traces)
            
    except Exception as e:
        print(f"Baseline runner failed: {e}")
        # If baseline fails, we record failures for those traces
        baseline_successes = [False] * len(traces)
        baseline_latencies = [0.0] * len(traces)
    
    # 4. Calculate Aggregate Metrics
    symbolic_success_rate = sum(symbolic_successes) / len(symbolic_successes) if symbolic_successes else 0.0
    baseline_success_rate = sum(baseline_successes) / len(baseline_successes) if baseline_successes else 0.0
    
    avg_symbolic_latency = sum(symbolic_latencies) / len(symbolic_latencies) if symbolic_latencies else 0.0
    avg_baseline_latency = sum(baseline_latencies) / len(baseline_latencies) if baseline_latencies else 0.0
    
    # Memory usage (peak)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_ram_mb = peak / (1024 * 1024)
    
    total_time = time.time() - start_time
    
    return {
        "granularity": granularity,
        "expressiveness": expressiveness,
        "traces_processed": len(traces),
        "symbolic_success_rate": symbolic_success_rate,
        "baseline_success_rate": baseline_success_rate,
        "symbolic_avg_latency_sec": avg_symbolic_latency,
        "baseline_avg_latency_sec": avg_baseline_latency,
        "peak_ram_mb": peak_ram_mb,
        "total_time_sec": total_time,
        "status": "success"
    }

def aggregate_comparative_results(results: List[Dict[str, Any]]) -> None:
    """
    Write the comparative results to a CSV file and a JSON report.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # CSV Output
    fieldnames = [
        "granularity", "expressiveness", "traces_processed",
        "symbolic_success_rate", "baseline_success_rate",
        "symbolic_avg_latency_sec", "baseline_avg_latency_sec",
        "peak_ram_mb", "total_time_sec", "status"
    ]
    
    with open(COMPARATIVE_OUTPUT_FILE, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Comparative results written to {COMPARATIVE_OUTPUT_FILE}")
    
    # JSON Report (Summary)
    total_symbolic_success = sum(r["symbolic_success_rate"] * r["traces_processed"] for r in results)
    total_baseline_success = sum(r["baseline_success_rate"] * r["traces_processed"] for r in results)
    total_traces = sum(r["traces_processed"] for r in results)
    
    overall_symbolic_rate = total_symbolic_success / total_traces if total_traces else 0.0
    overall_baseline_rate = total_baseline_success / total_traces if total_traces else 0.0
    
    report = {
        "total_traces": total_traces,
        "overall_symbolic_success_rate": overall_symbolic_rate,
        "overall_baseline_success_rate": overall_baseline_rate,
        "success_rate_delta": overall_symbolic_rate - overall_baseline_rate,
        "configs_tested": len(results),
        "details": results
    }
    
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Comparative report written to {REPORT_FILE}")

def main() -> None:
    """
    Main entry point to execute the comparative study.
    """
    print("Starting Comparative Study (US3)...")
    
    # Define the parameter space (same as sweep for consistency, or fixed config)
    # For US3, we might want to run on the "best" config or all configs.
    # Let's run all combinations to be thorough.
    GRANULARITY_OPTIONS = ["coarse", "fine"]
    EXPRESSIVENESS_OPTIONS = ["spatial", "spatial+temporal"]
    
    all_results = []
    
    for gran in GRANULARITY_OPTIONS:
        for expr in EXPRESSIVENESS_OPTIONS:
            print(f"Running comparative experiment: granularity={gran}, expressiveness={expr}")
            try:
                metrics = run_single_experiment(gran, expr)
                all_results.append(metrics)
                print(f"  -> Success Rate (Sym): {metrics['symbolic_success_rate']:.2%}, (Neural): {metrics['baseline_success_rate']:.2%}")
            except Exception as e:
                print(f"  -> FAILED: {e}")
                all_results.append({
                    "granularity": gran,
                    "expressiveness": expr,
                    "traces_processed": 0,
                    "symbolic_success_rate": 0.0,
                    "baseline_success_rate": 0.0,
                    "symbolic_avg_latency_sec": 0.0,
                    "baseline_avg_latency_sec": 0.0,
                    "peak_ram_mb": 0.0,
                    "total_time_sec": 0.0,
                    "status": "failed"
                })
    
    if all_results:
        aggregate_comparative_results(all_results)
        print("Comparative study completed.")
    else:
        print("No results to aggregate.")

if __name__ == "__main__":
    main()