"""
Metrics collection, aggregation, and statistical analysis.
"""
import csv
import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import math

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

@dataclass
class MetricsEntry:
    """Single metric entry for logging."""
    timestamp: str
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsLogger:
    """Logger for success, latency, and memory metrics."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.entries: List[MetricsEntry] = []
    
    def log_success(self, success: bool, tags: Dict[str, str] = None):
        """Log a success/failure event."""
        entry = MetricsEntry(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metric_name="success",
            value=1.0 if success else 0.0,
            tags=tags or {}
        )
        self.entries.append(entry)
    
    def log_latency(self, latency_ms: float, tags: Dict[str, str] = None):
        """Log latency in milliseconds."""
        entry = MetricsEntry(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metric_name="latency_ms",
            value=latency_ms,
            tags=tags or {}
        )
        self.entries.append(entry)
    
    def log_memory(self, memory_mb: float, tags: Dict[str, str] = None):
        """Log memory usage in MB."""
        entry = MetricsEntry(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metric_name="memory_mb",
            value=memory_mb,
            tags=tags or {}
        )
        self.entries.append(entry)
    
    def save_report(self, filename: str):
        """Save all entries to a JSON report."""
        report_path = self.output_dir / filename
        with open(report_path, "w") as f:
            json.dump([asdict(e) for e in self.entries], f, indent=2)

def run_mcnemar_test(success_symbolic: List[bool], success_neural: List[bool]) -> Tuple[float, float]:
    """
    Compute McNemar's test statistic and p-value for paired binary data.
    
    Args:
        success_symbolic: List of booleans for symbolic system success
        success_neural: List of booleans for neural baseline success
    
    Returns:
        (p_value, statistic) tuple
    """
    if len(success_symbolic) != len(success_neural):
        raise ValueError("Input lists must have the same length")
    
    n = len(success_symbolic)
    if n == 0:
        return 1.0, 0.0
    
    # Build contingency table
    # a: both succeed
    # b: symbolic succeeds, neural fails
    # c: symbolic fails, neural succeeds
    # d: both fail
    a = b = c = d = 0
    
    for s, ne in zip(success_symbolic, success_neural):
        if s and ne:
            a += 1
        elif s and not ne:
            b += 1
        elif not s and ne:
            c += 1
        else:
            d += 1
    
    # McNemar's statistic (with continuity correction)
    # chi2 = (|b - c| - 1)^2 / (b + c)
    if b + c == 0:
        return 1.0, 0.0
    
    statistic = ((abs(b - c) - 1) ** 2) / (b + c)
    
    # Calculate p-value using chi-square distribution with 1 degree of freedom
    # Approximation: p = 1 - CDF(chi2)
    # Using standard approximation for chi-square CDF
    p_value = 1.0 - chi2_cdf(statistic, 1)
    
    return max(0.0, min(1.0, p_value)), statistic

def chi2_cdf(x, df):
    """
    Approximate chi-square cumulative distribution function.
    Uses the regularized incomplete gamma function approximation.
    """
    if x <= 0:
        return 0.0
    if df <= 0:
        return 0.0
    
    # For df=1, chi2_cdf(x) = erf(sqrt(x/2))
    if df == 1:
        return math.erf(math.sqrt(x / 2))
    
    # General approximation using series expansion
    k = df / 2.0
    x_half = x / 2.0
    
    # Regularized incomplete gamma function P(k, x)
    # Using series expansion for small x
    if x_half < k + 1:
        sum_val = 1.0 / k
        term = 1.0 / k
        for n in range(1, 200):
            term *= x_half / (k + n)
            sum_val += term
            if abs(term) < 1e-10:
                break
        return sum_val * math.exp(-x_half + k * math.log(x_half) - math.lgamma(k))
    else:
        # Use continued fraction for large x
        return 1.0 - continued_fraction_gamma(k, x_half)

def continued_fraction_gamma(a, x):
    """Continued fraction approximation for Q(a, x) = 1 - P(a, x)."""
    if x <= 0:
        return 1.0
    
    # Lentz's algorithm for continued fraction
    f = 1.0 + (1.0 - a) / x
    c = f
    d = 0.0
    for i in range(1, 200):
        m = (i + 1) / 2
        if i % 2 == 1:
            a_i = -m * (m + a - 1) / (2 * m + 1)
        else:
            a_i = m / (2 * m + 1)
        
        d = 1.0 + a_i * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + a_i / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = c * d
        f *= delta
        if abs(delta - 1.0) < 1e-10:
            break
    
    return f * math.exp(-x + a * math.log(x) - math.lgamma(a))

def aggregate_sweep_results(sweep_file: Path) -> Dict[str, Any]:
    """Aggregate results from sweep_metrics.csv."""
    if not sweep_file.exists():
        return {}
    
    results = []
    with open(sweep_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "granularity": row["granularity"],
                "expressiveness": row["expressiveness"],
                "success_rate": float(row["success_rate"]),
                "latency_ms": float(row["latency_ms"]),
                "memory_mb": float(row["memory_mb"]),
                "trace_count": int(row["trace_count"])
            })
    
    return {
        "total_runs": len(results),
        "results": results
    }

def calculate_deltas(comparative_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate performance deltas between symbolic and neural systems.
    
    Args:
        comparative_results: List of experiment results with symbolic/neural metrics
    
    Returns:
        Dictionary with success_rate_delta and memory_reduction_pct
    """
    if not comparative_results:
        return {
            "success_rate_delta": 0.0,
            "memory_reduction_pct": 0.0
        }
    
    symbolic_successes = [r["symbolic_success"] for r in comparative_results]
    neural_successes = [r["neural_success"] for r in comparative_results]
    symbolic_memory = [r["symbolic_memory_mb"] for r in comparative_results]
    neural_memory = [r["neural_memory_mb"] for r in comparative_results]
    
    # Calculate success rates
    symbolic_rate = sum(symbolic_successes) / len(symbolic_successes)
    neural_rate = sum(neural_successes) / len(neural_successes)
    
    # Calculate memory averages
    symbolic_mem_avg = sum(symbolic_memory) / len(symbolic_memory)
    neural_mem_avg = sum(neural_memory) / len(neural_memory)
    
    # Calculate deltas
    success_rate_delta = symbolic_rate - neural_rate
    
    if neural_mem_avg > 0:
        memory_reduction_pct = (1 - symbolic_mem_avg / neural_mem_avg) * 100
    else:
        memory_reduction_pct = 0.0
    
    return {
        "success_rate_delta": success_rate_delta,
        "memory_reduction_pct": memory_reduction_pct
    }

def save_metrics_report(report_data: Dict[str, Any], output_path: Path):
    """Save metrics report to JSON file."""
    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=2)

def main():
    """Main entry point for metrics module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Metrics Analysis Tool")
    parser.add_argument("--mode", type=str, default="calculate_deltas",
                        choices=["calculate_deltas", "aggregate_sweep"])
    parser.add_argument("--input", type=str, help="Input file path")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    if args.mode == "calculate_deltas":
        # This would require comparative results input
        print("Use experiment_runner.py for comparative analysis")
    elif args.mode == "aggregate_sweep":
        if not args.input:
            print("Error: --input required for aggregate_sweep mode")
            return 1
        
        results = aggregate_sweep_results(Path(args.input))
        print(json.dumps(results, indent=2))
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
