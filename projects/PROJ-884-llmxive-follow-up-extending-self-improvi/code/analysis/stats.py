"""
Statistical analysis module for llmXive.
Implements z-tests, power analysis, and machine-readable results writing.
"""
import math
import sys
import os
import json
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
import argparse
from pathlib import Path

from code.utils.logger import log

@dataclass
class ZTestResult:
    """Result of a two-proportion z-test."""
    p1: float
    p2: float
    n1: int
    n2: int
    z_score: float
    p_value: float
    confidence_interval_95: Tuple[float, float]
    is_significant: bool
    alpha: float = 0.05

@dataclass
class TOSTResult:
    """Result of a TOST (equivalence) test."""
    mean_diff: float
    lower_bound: float
    upper_bound: float
    equivalence_margin: float
    is_equivalent: bool
    p_value_lower: float
    p_value_upper: float

@dataclass
class PreRegistration:
    """Pre-registration configuration for statistical tests."""
    test_type: str  # 'equivalence', 'non-inferiority', 'superiority'
    alpha: float
    power_target: float
    effect_size_h0: float
    alternative: str  # 'two-sided', 'greater', 'less'
    timestamp: str = field(default_factory=lambda: "2024-01-01T00:00:00")
    notes: str = ""

def calculate_effect_size(p1: float, p2: float, n1: int, n2: int) -> float:
    """Calculate Cohen's h for two proportions."""
    if n1 == 0 or n2 == 0:
        return 0.0
    phi1 = 2 * math.asin(math.sqrt(p1))
    phi2 = 2 * math.asin(math.sqrt(p2))
    return abs(phi1 - phi2)

def calculate_power_z_test(p1: float, p2: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """
    Estimate statistical power for a two-proportion z-test.
    Uses the normal approximation.
    """
    if n1 == 0 or n2 == 0:
        return 0.0
    
    # Pooled proportion under H0
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    if p_pool == 0 or p_pool == 1:
        return 0.0
    
    # Standard error under H0
    se_null = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    
    # Standard error under H1
    se_alt = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    
    # Effect size
    diff = abs(p1 - p2)
    
    if se_null == 0:
        return 0.0
    
    # Z-score for critical value
    z_alpha = 1.96 if alpha == 0.05 else 2.576 # Approx for 0.01
    
    # Power calculation (approximation)
    z_power = (diff - z_alpha * se_null) / se_alt
    
    # CDF of standard normal for z_power
    # Using error function approximation for CDF
    power = 0.5 * (1 + math.erf(z_power / math.sqrt(2)))
    return max(0.0, min(1.0, power))

def two_proportion_z_test(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05) -> ZTestResult:
    """
    Perform a two-proportion z-test.
    H0: p1 = p2
    H1: p1 != p2
    """
    if n1 == 0 or n2 == 0:
        raise ValueError("Sample sizes must be greater than 0")
    
    p1 = x1 / n1
    p2 = x2 / n2
    
    # Pooled proportion
    p_pool = (x1 + x2) / (n1 + n2)
    
    # Standard error
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    
    if se == 0:
        # No variance, cannot compute z
        return ZTestResult(
            p1=p1, p2=p2, n1=n1, n2=n2,
            z_score=0.0, p_value=1.0,
            confidence_interval_95=(0.0, 0.0),
            is_significant=False, alpha=alpha
        )
    
    # Z-score
    z_score = (p1 - p2) / se
    
    # Two-tailed p-value
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2))))
    
    # Confidence interval for difference
    se_diff = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z_crit = 1.96 # 95% CI
    diff = p1 - p2
    ci_lower = diff - z_crit * se_diff
    ci_upper = diff + z_crit * se_diff
    
    is_significant = p_value < alpha
    
    return ZTestResult(
        p1=p1, p2=p2, n1=n1, n2=n2,
        z_score=z_score, p_value=p_value,
        confidence_interval_95=(ci_lower, ci_upper),
        is_significant=is_significant, alpha=alpha
    )

def tost_equivalence_test(
    x1: int, n1: int, x2: int, n2: int, 
    equivalence_margin: float, alpha: float = 0.05
) -> TOSTResult:
    """
    Perform TOST (Two One-Sided Tests) for equivalence.
    """
    p1 = x1 / n1
    p2 = x2 / n2
    diff = p1 - p2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    
    if se == 0:
        return TOSTResult(
            mean_diff=diff, lower_bound=0.0, upper_bound=0.0,
            equivalence_margin=equivalence_margin,
            is_equivalent=False, p_value_lower=1.0, p_value_upper=1.0
        )
    
    # T1: H0: diff <= -margin vs H1: diff > -margin
    z_lower = (diff - (-equivalence_margin)) / se
    p_value_lower = 1 - 0.5 * (1 + math.erf(z_lower / math.sqrt(2)))
    
    # T2: H0: diff >= margin vs H1: diff < margin
    z_upper = (diff - equivalence_margin) / se
    p_value_upper = 0.5 * (1 + math.erf(z_upper / math.sqrt(2)))
    
    is_equivalent = (p_value_lower < alpha) and (p_value_upper < alpha)
    
    # Confidence interval
    z_crit = 1.96
    ci_lower = diff - z_crit * se
    ci_upper = diff + z_crit * se
    
    return TOSTResult(
        mean_diff=diff, lower_bound=ci_lower, upper_bound=ci_upper,
        equivalence_margin=equivalence_margin,
        is_equivalent=is_equivalent,
        p_value_lower=p_value_lower, p_value_upper=p_value_upper
    )

def register_statistical_framework(
    test_type: str, alpha: float, power_target: float,
    effect_size_h0: float, alternative: str, notes: str = ""
) -> PreRegistration:
    """Register the statistical framework for pre-registration."""
    from datetime import datetime
    return PreRegistration(
        test_type=test_type,
        alpha=alpha,
        power_target=power_target,
        effect_size_h0=effect_size_h0,
        alternative=alternative,
        timestamp=datetime.now().isoformat(),
        notes=notes
    )

def load_experiment_logs(log_path: str) -> List[Dict[str, Any]]:
    """Load experiment logs from a JSONL or JSON file."""
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")
    
    logs = []
    if path.suffix == '.jsonl':
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
    else:
        with open(path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                logs = data
            elif isinstance(data, dict) and 'results' in data:
                logs = data['results']
            else:
                logs = [data]
    
    return logs

def count_successes(logs: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Count successes and total attempts from logs.
    Expects logs to have 'success' or 'is_success' boolean field.
    """
    successes = 0
    total = 0
    
    for entry in logs:
        # Handle various possible log formats
        if 'success' in entry:
            is_success = entry['success']
        elif 'is_success' in entry:
            is_success = entry['is_success']
        elif 'result' in entry and isinstance(entry['result'], dict):
            is_success = entry['result'].get('success', False)
        else:
            # If no success field, assume it's a failed attempt if present
            is_success = False
        
        total += 1
        if is_success:
            successes += 1
    
    return successes, total

def write_stats_results(
    symbolic_logs: List[Dict[str, Any]],
    neural_logs: List[Dict[str, Any]],
    output_path: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform statistical tests and write results to a machine-readable JSON file.
    """
    x1, n1 = count_successes(symbolic_logs)
    x2, n2 = count_successes(neural_logs)
    
    if n1 == 0 or n2 == 0:
        raise ValueError("One or both datasets have no samples.")
    
    # Perform z-test
    z_result = two_proportion_z_test(x1, n1, x2, n2, alpha)
    
    # Calculate power
    power = calculate_power_z_test(z_result.p1, z_result.p2, n1, n2, alpha)
    
    # Calculate effect size
    effect_size = calculate_effect_size(z_result.p1, z_result.p2, n1, n2)
    
    results = {
        "test_type": "two_proportion_z_test",
        "alpha": alpha,
        "symbolic": {
            "successes": x1,
            "total": n1,
            "rate": z_result.p1
        },
        "neural": {
            "successes": x2,
            "total": n2,
            "rate": z_result.p2
        },
        "test_statistics": {
            "z_score": z_result.z_score,
            "p_value": z_result.p_value,
            "confidence_interval_95": {
                "lower": z_result.confidence_interval_95[0],
                "upper": z_result.confidence_interval_95[1]
            }
        },
        "conclusion": {
            "is_significant": z_result.is_significant,
            "interpretation": "Reject H0" if z_result.is_significant else "Fail to reject H0"
        },
        "power_analysis": {
            "estimated_power": power,
            "effect_size_cohen_h": effect_size,
            "is_underpowered": power < 0.8
        },
        "metadata": {
            "symbolic_samples": n1,
            "neural_samples": n2,
            "generated_at": "2024-01-01T00:00:00" # Placeholder, real timestamp handled by caller if needed
        }
    }
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    """Main entry point for stats analysis."""
    parser = argparse.ArgumentParser(description="Statistical analysis for llmXive")
    parser.add_argument("--symbolic", type=str, required=True, help="Path to symbolic logs")
    parser.add_argument("--neural", type=str, required=True, help="Path to neural logs")
    parser.add_argument("--output", type=str, required=True, help="Output JSON path")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    
    args = parser.parse_args()
    
    try:
        symbolic_logs = load_experiment_logs(args.symbolic)
        neural_logs = load_experiment_logs(args.neural)
        
        results = write_stats_results(symbolic_logs, neural_logs, args.output, args.alpha)
        
        print(f"Results written to {args.output}")
        print(f"Symbolic rate: {results['symbolic']['rate']:.4f} ({results['symbolic']['successes']}/{results['symbolic']['total']})")
        print(f"Neural rate: {results['neural']['rate']:.4f} ({results['neural']['successes']}/{results['neural']['total']})")
        print(f"Z-score: {results['test_statistics']['z_score']:.4f}")
        print(f"P-value: {results['test_statistics']['p_value']:.4f}")
        print(f"Significant: {results['conclusion']['is_significant']}")
        print(f"Power: {results['power_analysis']['estimated_power']:.4f}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()