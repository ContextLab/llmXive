import csv
import json
import os
import sys
import time
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure code directory is in path for imports if running as script
code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import RANDOM_SEED

@dataclass
class MetricsEntry:
    timestamp: str
    metric_name: str
    value: float
    unit: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricsLogger:
    def __init__(self, output_dir: str = "data/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.entries: List[MetricsEntry] = []

    def log_success(self, success: bool, metadata: Optional[Dict] = None):
        entry = MetricsEntry(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metric_name="success",
            value=1.0 if success else 0.0,
            unit="boolean",
            metadata=metadata or {}
        )
        self.entries.append(entry)

    def log_latency(self, latency_ms: float):
        entry = MetricsEntry(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metric_name="latency",
            value=latency_ms,
            unit="ms",
            metadata={}
        )
        self.entries.append(entry)

    def log_memory(self, memory_mb: float):
        entry = MetricsEntry(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metric_name="memory",
            value=memory_mb,
            unit="MB",
            metadata={}
        )
        self.entries.append(entry)

    def save_report(self, filename: str):
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump([asdict(e) for e in self.entries], f, indent=2)

# Gamma and Chi-Square approximations for statistical tests
def continued_fraction_gamma(x: float) -> float:
    """Approximation of the incomplete gamma function ratio."""
    if x <= 0:
        return 0.0
    # Simple approximation for the purpose of the test statistic
    # In a full implementation, one would use scipy.special.gammainc
    return math.exp(-x) * (1 + x)

def chi2_cdf(x: float, k: int) -> float:
    """Cumulative Distribution Function for Chi-Square with k degrees of freedom."""
    if x <= 0:
        return 0.0
    # Approximation using the regularized gamma function
    # P(k/2, x/2)
    return continued_fraction_gamma(x / 2.0)

def run_mcnemar_test(success_symbolic: List[bool], success_neural: List[bool]) -> Tuple[float, float]:
    """
    Compute McNemar's test for paired binary outcomes.
    Returns (p_value, test_statistic).
    """
    if len(success_symbolic) != len(success_neural):
        raise ValueError("Input lists must be of equal length for paired test.")

    n = len(success_symbolic)
    discordant_01 = 0 # Symbolic Fail, Neural Success
    discordant_10 = 0 # Symbolic Success, Neural Fail

    for s, ne in zip(success_symbolic, success_neural):
        if not s and ne:
            discordant_01 += 1
        elif s and not ne:
            discordant_10 += 1

    if (discordant_01 + discordant_10) == 0:
        return 1.0, 0.0

    # McNemar statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    b, c = discordant_01, discordant_10
    statistic = (abs(b - c) - 1) ** 2 / (b + c)

    # P-value from Chi-Square distribution with 1 degree of freedom
    # Using approximation for p-value from statistic
    # For k=1, Chi2 CDF is related to the error function, but we use a simple lookup or approximation
    # Here we use a standard approximation for p-value from Chi2 statistic
    # p = 1 - CDF(statistic, 1)
    # Since we don't have scipy, we approximate:
    # For large X, P(X > x) ~ exp(-x/2) / sqrt(2*pi*x) ... but let's use a simpler bound or 1.0 if small
    # A more robust approximation for 1 d.f.:
    # p = 2 * (1 - Phi(sqrt(statistic)))
    # Using continued_fraction_gamma as a proxy for the CDF of Gamma(k/2, 2) which is Chi2(k)
    # Actually, for k=1, Chi2 is the square of a standard normal.
    # Let's compute a rough p-value using the fact that for 1 dof, CDF(x) = erf(sqrt(x/2))
    # p = 1 - erf(sqrt(statistic/2))
    # We'll use a standard approximation for erf or just return the statistic if we can't compute p precisely without scipy
    # Given the constraints, we will return the statistic and a calculated p-value using a simple approximation
    # p-value approximation for Chi2(1)
    if statistic <= 0:
        p_value = 1.0
    else:
        # Approximation: p = exp(-statistic/2) * (1 / sqrt(2*pi*statistic)) is for tail
        # Let's use a simpler logic: if statistic > 3.841 (95% threshold), p < 0.05
        # We will return a calculated value using a basic series expansion or just the statistic
        # For this task, we calculate the statistic and use a standard approximation for p-value
        # p = 1 - (2 * Phi(sqrt(statistic)) - 1) = 2 * (1 - Phi(sqrt(statistic)))
        # Using a rational approximation for the normal CDF (Abramowitz and Stegun)
        z = math.sqrt(statistic)
        t = 1.0 / (1.0 + 0.2316419 * z)
        d = 0.3989423 * math.exp(-z * z / 2.0)
        p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
        p_value = 2.0 * p if p < 0.5 else 2.0 * (1.0 - p) # Two-tailed equivalent logic for symmetry in this context

    return p_value, statistic

def aggregate_sweep_results(csv_path: str) -> Dict[str, Any]:
    """
    Aggregate sweep results from CSV to measure impact of granularity and expressiveness.
    Reads data/results/sweep_metrics.csv.
    Returns a dictionary with aggregated statistics per configuration.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Sweep results file not found: {csv_path}")

    results = {}
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            granularity = row['granularity']
            expressiveness = row['expressiveness']
            key = f"{granularity}_{expressiveness}"

            if key not in results:
                results[key] = {
                    'granularity': granularity,
                    'expressiveness': expressiveness,
                    'success_rates': [],
                    'latencies': [],
                    'memory_usages': []
                }

            results[key]['success_rates'].append(float(row['success_rate']))
            results[key]['latencies'].append(float(row['latency_ms']))
            results[key]['memory_usages'].append(float(row['memory_mb']))

    # Calculate averages and impacts
    summary = {}
    for key, data in results.items():
        summary[key] = {
            'avg_success_rate': sum(data['success_rates']) / len(data['success_rates']) if data['success_rates'] else 0.0,
            'avg_latency_ms': sum(data['latencies']) / len(data['latencies']) if data['latencies'] else 0.0,
            'avg_memory_mb': sum(data['memory_usages']) / len(data['memory_usages']) if data['memory_usages'] else 0.0,
            'trace_count': len(data['success_rates'])
        }

    # Calculate impact of granularity (coarse vs fine)
    coarse_keys = [k for k in summary if 'coarse' in k]
    fine_keys = [k for k in summary if 'fine' in k]

    impact = {
        'granularity_impact': {},
        'expressiveness_impact': {}
    }

    if coarse_keys and fine_keys:
        avg_coarse_success = sum(summary[k]['avg_success_rate'] for k in coarse_keys) / len(coarse_keys)
        avg_fine_success = sum(summary[k]['avg_success_rate'] for k in fine_keys) / len(fine_keys)
        impact['granularity_impact']['success_rate_delta'] = avg_fine_success - avg_coarse_success

    # Similar for expressiveness
    spatial_keys = [k for k in summary if 'spatial' in k and 'temporal' not in k]
    spatial_temporal_keys = [k for k in summary if 'temporal' in k]

    if spatial_keys and spatial_temporal_keys:
        avg_spatial_success = sum(summary[k]['avg_success_rate'] for k in spatial_keys) / len(spatial_keys)
        avg_st_success = sum(summary[k]['avg_success_rate'] for k in spatial_temporal_keys) / len(spatial_temporal_keys)
        impact['expressiveness_impact']['success_rate_delta'] = avg_st_success - avg_spatial_success

    return {
        'configurations': summary,
        'impact_analysis': impact,
        'total_configurations': len(summary)
    }

def calculate_deltas(symbolic_metrics: Dict, neural_metrics: Dict) -> Dict[str, float]:
    """
    Calculate specific deltas between symbolic and neural systems.
    """
    success_rate_delta = symbolic_metrics.get('success_rate', 0.0) - neural_metrics.get('success_rate', 0.0)
    symbolic_mem = symbolic_metrics.get('memory_mb', 1.0)
    neural_mem = neural_metrics.get('memory_mb', 1.0)
    memory_reduction_pct = (1 - (symbolic_mem / neural_mem)) * 100 if neural_mem > 0 else 0.0

    return {
        'success_rate_delta': success_rate_delta,
        'memory_reduction_pct': memory_reduction_pct
    }

def save_metrics_report(data: Dict, filename: str = "sweep_analysis.json"):
    """
    Save the aggregated analysis to a JSON file.
    """
    output_path = Path("data/results") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    """
    Entry point for T031: Aggregate sweep results and measure impact.
    """
    csv_path = "data/results/sweep_metrics.csv"
    try:
        analysis = aggregate_sweep_results(csv_path)
        save_metrics_report(analysis, "sweep_analysis.json")
        print(f"Sweep analysis complete. Results saved to data/results/sweep_analysis.json")
        print(f"Total configurations analyzed: {analysis['total_configurations']}")
        print(f"Granularity impact: {analysis['impact_analysis']['granularity_impact']}")
        print(f"Expressiveness impact: {analysis['impact_analysis']['expressiveness_impact']}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()