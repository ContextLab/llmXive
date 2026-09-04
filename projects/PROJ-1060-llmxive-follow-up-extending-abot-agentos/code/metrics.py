import csv
import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import statistics

@dataclass
class MetricsEntry:
    """Represents a single metrics entry for logging."""
    timestamp: float
    experiment_id: str
    granularity: str
    expressiveness: str
    success: bool
    latency_ms: float
    memory_mb: float
    error_category: Optional[str] = None

class MetricsLogger:
    """Logs metrics to JSON and CSV formats, and supports aggregation."""

    def __init__(self, output_dir: str = "data/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.entries: List[MetricsEntry] = []

    def log_success(self, success: bool):
        """Log success status (contextualized by current run state)."""
        # This is a simplified helper; actual logging usually happens via add_entry
        pass

    def log_latency(self, latency_ms: float):
        """Log latency (contextualized by current run state)."""
        pass

    def log_memory(self, memory_mb: float):
        """Log memory usage (contextualized by current run state)."""
        pass

    def add_entry(self, entry: MetricsEntry):
        """Add a full metrics entry to the in-memory buffer."""
        self.entries.append(entry)

    def save_report(self, filename: str):
        """Save all collected entries to a CSV file."""
        filepath = self.output_dir / filename
        if not self.entries:
            # Write empty file with headers if no data
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(self.entries[0]).keys() if self.entries else [])
                writer.writeheader()
            return

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(self.entries[0]).keys())
            writer.writeheader()
            for entry in self.entries:
                writer.writerow(asdict(entry))

def run_mcnemar_test(success_symbolic: List[bool], success_neural: List[bool]) -> Tuple[float, float]:
    """
    Compute McNemar's test statistic and p-value for paired nominal data.
    Returns (statistic, p_value).
    """
    if len(success_symbolic) != len(success_neural):
        raise ValueError("Lists must be of equal length")

    n = len(success_symbolic)
    # Contingency table counts
    # a: Both Success
    # b: Symbolic Success, Neural Fail
    # c: Symbolic Fail, Neural Success
    # d: Both Fail
    b = 0
    c = 0
    for s, ne in zip(success_symbolic, success_neural):
        if s and not ne:
            b += 1
        elif not s and ne:
            c += 1

    if b + c == 0:
        return 0.0, 1.0

    # McNemar statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    # Or standard: (b - c)^2 / (b + c)
    # Using continuity correction for small samples usually preferred
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    
    # Approximate p-value using Chi-squared distribution with 1 df
    # Since we can't import scipy.stats easily without adding deps, 
    # we use a simple approximation or return the statistic.
    # However, statsmodels is in requirements. Let's assume we can use it if available,
    # but to keep it pure stdlib/dataclass based as per current imports, 
    # we will implement a basic Chi2 survival function approximation or rely on statsmodels if imported.
    # Given requirements.txt has statsmodels, let's try to import it.
    try:
        from scipy.stats import chi2
        p_value = chi2.sf(stat, 1)
    except ImportError:
        # Fallback simple approximation if scipy not available (unlikely given reqs)
        # For stat > 3.841, p < 0.05
        p_value = 1.0 if stat < 3.841 else 0.04 if stat < 5.0 else 0.01

    return float(stat), float(p_value)

def aggregate_sweep_results(sweep_data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Aggregate results from the parametric sweep (T016).
    Reads data/results/sweep_metrics.csv (or specified path),
    groups by granularity and expressiveness, and calculates
    average success rate, average latency, and average memory usage.
    
    Writes a summary report to the specified output_path.
    """
    input_file = Path(sweep_data_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Sweep results file not found: {sweep_data_path}")

    results: Dict[str, List[Dict[str, Any]]] = {}

    with open(input_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse row data
            granularity = row.get('granularity', 'unknown')
            expressiveness = row.get('expressiveness', 'unknown')
            success = row.get('success', 'False').lower() == 'true'
            latency = float(row.get('latency_ms', 0))
            memory = float(row.get('memory_mb', 0))

            key = (granularity, expressiveness)
            if key not in results:
                results[key] = []
            
            results[key].append({
                'success': success,
                'latency_ms': latency,
                'memory_mb': memory
            })

    summary = {
        'aggregated_metrics': [],
        'impact_analysis': {
            'granularity_impact': {},
            'expressiveness_impact': {}
        }
    }

    # Calculate aggregates
    for (gran, expr), data_list in results.items():
        total_runs = len(data_list)
        success_count = sum(1 for d in data_list if d['success'])
        success_rate = success_count / total_runs if total_runs > 0 else 0.0
        
        avg_latency = statistics.mean([d['latency_ms'] for d in data_list]) if data_list else 0.0
        avg_memory = statistics.mean([d['memory_mb'] for d in data_list]) if data_list else 0.0

        summary['aggregated_metrics'].append({
            'granularity': gran,
            'expressiveness': expr,
            'total_runs': total_runs,
            'success_rate': success_rate,
            'avg_latency_ms': avg_latency,
            'avg_memory_mb': avg_memory
        })

    # Analyze impact of granularity (holding expressiveness constant or averaging)
    # Simple approach: Compare coarse vs fine across all expressiveness
    gran_success_rates = {}
    gran_latencies = {}
    gran_memories = {}
    
    for metric in summary['aggregated_metrics']:
        g = metric['granularity']
        if g not in gran_success_rates:
            gran_success_rates[g] = []
            gran_latencies[g] = []
            gran_memories[g] = []
        gran_success_rates[g].append(metric['success_rate'])
        gran_latencies[g].append(metric['avg_latency_ms'])
        gran_memories[g].append(metric['avg_memory_mb'])

    for g, rates in gran_success_rates.items():
        summary['impact_analysis']['granularity_impact'][g] = {
            'avg_success_rate': statistics.mean(rates),
            'avg_latency_ms': statistics.mean(gran_latencies[g]),
            'avg_memory_mb': statistics.mean(gran_memories[g])
        }

    # Analyze impact of expressiveness
    expr_success_rates = {}
    expr_latencies = {}
    expr_memories = {}

    for metric in summary['aggregated_metrics']:
        e = metric['expressiveness']
        if e not in expr_success_rates:
            expr_success_rates[e] = []
            expr_latencies[e] = []
            expr_memories[e] = []
        expr_success_rates[e].append(metric['success_rate'])
        expr_latencies[e].append(metric['avg_latency_ms'])
        expr_memories[e].append(metric['avg_memory_mb'])

    for e, rates in expr_success_rates.items():
        summary['impact_analysis']['expressiveness_impact'][e] = {
            'avg_success_rate': statistics.mean(rates),
            'avg_latency_ms': statistics.mean(expr_latencies[e]),
            'avg_memory_mb': statistics.mean(expr_memories[e])
        }

    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    return summary

def main():
    """
    Entry point for T031: Aggregating sweep results.
    Expects sweep data at data/results/sweep_metrics.csv
    Outputs to data/results/sweep_aggregation.json
    """
    sweep_path = "data/results/sweep_metrics.csv"
    output_path = "data/results/sweep_aggregation.json"
    
    if not Path(sweep_path).exists():
        print(f"Error: Sweep data file {sweep_path} not found. Run T016 first.")
        return 1

    try:
        summary = aggregate_sweep_results(sweep_path, output_path)
        print(f"Sweep aggregation complete. Report saved to {output_path}")
        print(f"Granularity Impact: {summary['impact_analysis']['granularity_impact']}")
        print(f"Expressiveness Impact: {summary['impact_analysis']['expressiveness_impact']}")
        return 0
    except Exception as e:
        print(f"Error aggregating sweep results: {e}")
        return 1

if __name__ == "__main__":
    exit(main())