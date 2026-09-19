import json
import os
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure code directory is in path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def load_traces(input_path: str = "data/raw/traces.json") -> List[Dict[str, Any]]:
    """Load traces from file."""
    filepath = Path(input_path)
    if not filepath.exists():
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def run_baseline_on_traces(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run the neural baseline (ABot-AgentOS v1.0) on traces.
    Returns success/latency/memory metrics.
    """
    tracemalloc.start()
    start = time.time()
    
    # Simulate baseline execution (in real scenario, this would call the actual model)
    # For now, we simulate a deterministic outcome based on trace content
    success_count = 0
    for trace in traces:
        # Simple heuristic: if trace has objects and relations, consider it a "success"
        if trace.get("objects") and trace.get("relations"):
            success_count += 1
    
    elapsed = time.time() - start
    current, peak = tracemalloc.take_snapshot().get_traced_memory()
    tracemalloc.stop()
    
    memory_mb = peak / (1024 * 1024)
    
    return {
        "success": success_count > 0,
        "success_count": success_count,
        "total_count": len(traces),
        "latency_ms": elapsed * 1000,
        "memory_mb": memory_mb
    }

def aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate metrics from multiple runs."""
    if not results:
        return {"success_rate": 0.0, "avg_latency_ms": 0.0, "avg_memory_mb": 0.0}
    
    total_success = sum(r.get("success_count", 0) for r in results)
    total_count = sum(r.get("total_count", 0) for r in results)
    avg_latency = sum(r.get("latency_ms", 0) for r in results) / len(results)
    avg_memory = sum(r.get("memory_mb", 0) for r in results) / len(results)
    
    return {
        "success_rate": total_success / total_count if total_count > 0 else 0.0,
        "avg_latency_ms": avg_latency,
        "avg_memory_mb": avg_memory
    }

def save_metrics_report(metrics: Dict[str, float], output_path: str = "data/results/baseline_metrics.json"):
    """Save metrics report to JSON."""
    filepath = Path(output_path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """CLI entry point for baseline runner."""
    import argparse
    parser = argparse.ArgumentParser(description="Baseline Runner")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    args = parser.parse_args()
    
    if args.demo:
        traces = [{"id": "demo", "objects": ["cup"], "relations": []}]
        result = run_baseline_on_traces(traces)
        print(f"Baseline result: {result}")

if __name__ == "__main__":
    main()