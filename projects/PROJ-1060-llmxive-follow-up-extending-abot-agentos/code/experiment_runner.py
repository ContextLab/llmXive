import csv
import json
import os
import time
import tracemalloc
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Ensure code directory is in path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data_loader import load_traces_as_list
from graph_builder import build_graph_from_traces, save_graph
from query_engine import query_graph
from baseline_runner import run_baseline_on_traces, aggregate_metrics
from metrics import MetricsLogger, calculate_deltas, run_mcnemar_test
from error_analysis import ErrorAnalyzer
from latency_guard import latency_guard, LatencyExceededError, flush_violations
from config import RANDOM_SEED, MAX_TRACES

@dataclass
class ExperimentResult:
    task_id: str
    symbolic_success: bool
    neural_success: bool
    symbolic_latency_ms: float
    neural_latency_ms: float
    symbolic_memory_mb: float
    neural_memory_mb: float

def run_single_experiment(
    trace: Dict[str, Any],
    task_id: str,
    analyzer: ErrorAnalyzer
) -> ExperimentResult:
    """
    Run a single task trace through both symbolic and neural systems.
    Records success, latency, and memory.
    """
    # --- Symbolic System ---
    tracemalloc.start()
    start_time = time.perf_counter()
    symbolic_success = False
    try:
        # Build graph
        graph = build_graph_from_traces([trace])
        # Query graph (simple query for demonstration of comparative study)
        # Using a generic query relevant to the task
        query_str = trace.get('instruction', 'navigate')
        # We assume query_graph returns a path or context; success if no exception and result exists
        result = query_graph(graph, query_str)
        symbolic_success = result is not None and len(result) > 0
    except Exception as e:
        # Categorize error
        error_type = 'OTHER'
        if "VLM" in str(e) or "token" in str(e).lower():
            error_type = 'VLM_MISMATCH'
        elif "traversal" in str(e).lower() or "graph" in str(e).lower():
            error_type = 'GRAPH_TRAVERSAL_FAIL'
        
        analyzer.record_failure(
            trace_id=task_id,
            error_type=error_type,
            description=str(e),
            raw_trace=trace
        )
        symbolic_success = False
    finally:
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        symbolic_latency_ms = (end_time - start_time) * 1000
        symbolic_memory_mb = peak / (1024 * 1024)

    # --- Neural Baseline ---
    tracemalloc.start()
    start_time = time.perf_counter()
    neural_success = False
    try:
        # Run baseline
        baseline_result = run_baseline_on_traces([trace])
        neural_success = baseline_result.get('success', False)
    except Exception as e:
        neural_success = False
    finally:
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        neural_latency_ms = (end_time - start_time) * 1000
        neural_memory_mb = peak / (1024 * 1024)

    return ExperimentResult(
        task_id=task_id,
        symbolic_success=symbolic_success,
        neural_success=neural_success,
        symbolic_latency_ms=symbolic_latency_ms,
        neural_latency_ms=neural_latency_ms,
        symbolic_memory_mb=symbolic_memory_mb,
        neural_memory_mb=neural_memory_mb
    )

def aggregate_comparative_results(results: List[ExperimentResult]) -> Dict[str, Any]:
    """Aggregate results from multiple experiments."""
    total = len(results)
    if total == 0:
        return {}

    symbolic_successes = [r.symbolic_success for r in results]
    neural_successes = [r.neural_success for r in results]

    symbolic_rate = sum(symbolic_successes) / total
    neural_rate = sum(neural_successes) / total

    avg_symbolic_latency = sum(r.symbolic_latency_ms for r in results) / total
    avg_neural_latency = sum(r.neural_latency_ms for r in results) / total

    avg_symbolic_memory = sum(r.symbolic_memory_mb for r in results) / total
    avg_neural_memory = sum(r.neural_memory_mb for r in results) / total

    # Run McNemar test
    p_value, statistic = run_mcnemar_test(symbolic_successes, neural_successes)

    # Calculate deltas
    deltas = calculate_deltas(
        {"success_rate": symbolic_rate, "memory_mb": avg_symbolic_memory, "latency_ms": avg_symbolic_latency},
        {"success_rate": neural_rate, "memory_mb": avg_neural_memory, "latency_ms": avg_neural_latency}
    )

    return {
        "total_tasks": total,
        "symbolic_success_rate": symbolic_rate,
        "neural_success_rate": neural_rate,
        "symbolic_avg_latency_ms": avg_symbolic_latency,
        "neural_avg_latency_ms": avg_neural_latency,
        "symbolic_avg_memory_mb": avg_symbolic_memory,
        "neural_avg_memory_mb": avg_neural_memory,
        "mcnemar_p_value": p_value,
        "mcnemar_statistic": statistic,
        "deltas": deltas,
        "raw_results": [
            {
                "task_id": r.task_id,
                "symbolic_success": r.symbolic_success,
                "neural_success": r.neural_success,
                "symbolic_latency_ms": r.symbolic_latency_ms,
                "neural_latency_ms": r.neural_latency_ms,
                "symbolic_memory_mb": r.symbolic_memory_mb,
                "neural_memory_mb": r.neural_memory_mb
            }
            for r in results
        ]
    }

def run_sweep(sample_size: int = 50):
    """
    Run the comparative study on a sample of traces.
    """
    print(f"Starting comparative study with sample size: {sample_size}")
    
    # Load real traces
    try:
        traces = load_traces_as_list(split="train", max_traces=sample_size)
    except Exception as e:
        print(f"Failed to load traces: {e}")
        raise RuntimeError("Baseline acquisition failed: No reproducible artifact found.")

    analyzer = ErrorAnalyzer()
    results: List[ExperimentResult] = []

    for i, trace in enumerate(traces):
        task_id = trace.get('id', f'task_{i}')
        print(f"Processing {task_id} ({i+1}/{len(traces)})")
        
        # Flush latency violations for each batch if needed, or accumulate
        # We accumulate for the whole run to check global thresholds
        try:
            res = run_single_experiment(trace, task_id, analyzer)
            results.append(res)
        except LatencyExceededError as e:
            print(f"Latency exceeded for {task_id}: {e}")
            # Continue with other tasks but log the violation
            # We still record the result up to the point of failure or mark as failed
            # For simplicity, we mark as failed and continue
            results.append(ExperimentResult(
                task_id=task_id,
                symbolic_success=False,
                neural_success=False,
                symbolic_latency_ms=0,
                neural_latency_ms=0,
                symbolic_memory_mb=0,
                neural_memory_mb=0
            ))

    # Aggregate results
    report = aggregate_comparative_results(results)
    
    # Save error analysis log (T030a)
    analyzer.save_log("data/results/error_analysis_log.json")
    print("Saved error analysis log.")

    # Save deltas (T032a)
    deltas_path = Path("data/results/deltas.json")
    deltas_path.parent.mkdir(parents=True, exist_ok=True)
    with open(deltas_path, 'w') as f:
        json.dump(report.get('deltas', {}), f, indent=2)
    print("Saved deltas.")

    # Save full report (T032)
    full_report_path = Path("data/results/final_report.json")
    with open(full_report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate Markdown report
    generate_markdown_report(report)
    print("Comparative study complete.")
    return report

def generate_markdown_report(report: Dict[str, Any]):
    """Generate the final markdown report."""
    md_path = Path("data/results/final_report.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(md_path, 'w') as f:
        f.write("# Comparative Analysis Report\n\n")
        f.write(f"**Total Tasks:** {report.get('total_tasks', 0)}\n\n")
        
        f.write("## Performance Metrics\n")
        f.write(f"- **Symbolic Success Rate:** {report.get('symbolic_success_rate', 0):.2%}\n")
        f.write(f"- **Neural Success Rate:** {report.get('neural_success_rate', 0):.2%}\n")
        f.write(f"- **Symbolic Avg Latency:** {report.get('symbolic_avg_latency_ms', 0):.2f} ms\n")
        f.write(f"- **Neural Avg Latency:** {report.get('neural_avg_latency_ms', 0):.2f} ms\n")
        f.write(f"- **Symbolic Avg Memory:** {report.get('symbolic_avg_memory_mb', 0):.2f} MB\n")
        f.write(f"- **Neural Avg Memory:** {report.get('neural_avg_memory_mb', 0):.2f} MB\n\n")
        
        f.write("## Statistical Analysis (McNemar's Test)\n")
        f.write(f"- **p-value:** {report.get('mcnemar_p_value', 0):.4f}\n")
        f.write(f"- **Statistic:** {report.get('mcnemar_statistic', 0):.4f}\n\n")
        
        f.write("## Deltas\n")
        deltas = report.get('deltas', {})
        f.write(f"- **Success Rate Delta:** {deltas.get('success_rate_delta', 0):.4f}\n")
        f.write(f"- **Memory Reduction:** {deltas.get('memory_reduction_pct', 0):.2f}%\n\n")
        
        f.write("## Target Evaluation\n")
        # Check targets: <= 5% error rate difference (if applicable), >= 80% success rate
        success_rate = report.get('symbolic_success_rate', 0)
        target_met = success_rate >= 0.80
        f.write(f"- **Target Success Rate (>= 80%):** {'Met' if target_met else 'Not Met'} ({success_rate:.2%})\n")
        
        # P-value target (e.g., < 0.05 for significance)
        p_val = report.get('mcnemar_p_value', 1.0)
        sig_met = p_val < 0.05
        f.write(f"- **Significance (p < 0.05):** {'Met' if sig_met else 'Not Met'} (p={p_val:.4f})\n")

def main():
    parser = argparse.ArgumentParser(description="Run comparative experiment.")
    parser.add_argument("--mode", type=str, default="full", help="Run mode: full, baseline-only")
    parser.add_argument("--sample-size", type=int, default=50, help="Number of traces to sample")
    args = parser.parse_args()

    if args.mode == "baseline-only":
        print("Baseline-only mode not fully implemented in this task; running full comparative.")
    
    # Initialize latency violations file
    flush_violations()
    
    # Run the sweep
    run_sweep(sample_size=args.sample_size)

if __name__ == "__main__":
    main()