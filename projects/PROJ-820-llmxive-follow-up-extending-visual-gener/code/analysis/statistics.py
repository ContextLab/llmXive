"""
Statistical analysis module for evaluating geometric consistency and significance.
"""
import json
import os
import sys
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats

class StudyInvalidError(Exception):
    """Raised when the study data is invalid for statistical analysis."""
    pass

def calculate_effect_size(p1: float, p2: float) -> float:
    """
    Calculate Cohen's h effect size for two proportions.
    
    Args:
        p1: Proportion 1.
        p2: Proportion 2.
        
    Returns:
        Cohen's h value.
    """
    # Avoid log(0)
    eps = 1e-7
    p1 = np.clip(p1, eps, 1 - eps)
    p2 = np.clip(p2, eps, 1 - eps)
    
    phi1 = 2 * np.arcsin(np.sqrt(p1))
    phi2 = 2 * np.arcsin(np.sqrt(p2))
    
    return abs(phi1 - phi2)

def power_analysis_two_proportions(effect_size: float, alpha: float = 0.05, 
                                   power_target: float = 0.8, n_per_group: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform power analysis for two-proportion tests.
    
    Args:
        effect_size: Expected effect size (Cohen's h).
        alpha: Significance level.
        power_target: Target statistical power.
        n_per_group: Optional fixed sample size to check power for.
        
    Returns:
        Dictionary with power analysis results.
    """
    if n_per_group:
        # Calculate power for given n
        # Using normal approximation for power
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power_target)
        
        # Power formula rearrangement or direct calculation
        # For simplicity, we use statsmodels logic conceptually or scipy approximation
        # Here we calculate required n if not provided, or power if provided
        pass
    
    # Standard calculation for required sample size per group
    # n = 2 * ( (z_alpha/2 + z_beta) / effect_size )^2
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power_target)
    
    if effect_size <= 0:
        raise ValueError("Effect size must be positive for sample size calculation.")
        
    n_required = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    n_required = int(np.ceil(n_required))
    
    return {
        "effect_size": effect_size,
        "alpha": alpha,
        "target_power": power_target,
        "required_n_per_group": n_required,
        "total_required_samples": n_required * 2
    }

def two_proportion_z_test(x1: int, n1: int, x2: int, n2: int) -> Tuple[float, float]:
    """
    Perform a two-proportion z-test.
    
    Args:
        x1: Number of successes in group 1.
        n1: Total trials in group 1.
        x2: Number of successes in group 2.
        n2: Total trials in group 2.
        
    Returns:
        Tuple of (z_statistic, p_value).
    """
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    
    if se == 0:
        return 0.0, 1.0
        
    z = (p1 - p2) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    return z, p_value

def fisher_exact_test(x1: int, n1: int, x2: int, n2: int) -> Tuple[float, float]:
    """
    Perform Fisher's Exact Test.
    
    Args:
        x1: Successes in group 1.
        n1: Total in group 1.
        x2: Successes in group 2.
        n2: Total in group 2.
        
    Returns:
        Tuple of (odds_ratio, p_value).
    """
    # Contingency table:
    # [[x1, n1-x1], [x2, n2-x2]]
    table = [[x1, n1 - x1], [x2, n2 - x2]]
    oddsratio, p_value = stats.fisher_exact(table)
    return oddsratio, p_value

def select_statistical_test(x1: int, n1: int, x2: int, n2: int) -> str:
    """
    Select the appropriate statistical test based on cell counts.
    
    Args:
        x1, n1, x2, n2: Counts for the two groups.
        
    Returns:
        'z_test' or 'fisher'.
    """
    # Check expected cell counts (rule of thumb: if any < 5, use Fisher)
    # Approximation: min(x1, n1-x1, x2, n2-x2)
    min_count = min(x1, n1 - x1, x2, n2 - x2)
    
    if min_count < 5:
        return "fisher"
    return "z_test"

def load_evaluation_results(results_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all evaluation result JSONs from a directory.
    
    Args:
        results_dir: Directory containing result JSONs.
        
    Returns:
        List of result dictionaries.
    """
    results = []
    if not results_dir.exists():
        return results
        
    for json_file in results_dir.glob("*.json"):
        if json_file.name == "contradiction_log.json":
            continue
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                results.append(data)
        except json.JSONDecodeError:
            continue
    return results

def aggregate_violation_rates(results: List[Dict[str, Any]], group_label: str = "group") -> Dict[str, int]:
    """
    Aggregate violation counts by group.
    
    Args:
        results: List of evaluation results.
        group_label: Key for the group identifier.
        
    Returns:
        Dict mapping group -> {"total": int, "violations": int}.
    """
    aggregates = {}
    
    for res in results:
        # Assuming structure: { "group": "Baseline", "violation_count": 1, "total_objects": 5 }
        # Or flat violation flags. We adapt to common structure.
        grp = res.get(group_label, "Unknown")
        if grp not in aggregates:
            aggregates[grp] = {"total": 0, "violations": 0}
        
        # Heuristic for counting violations
        if "violation_count" in res:
            aggregates[grp]["violations"] += res["violation_count"]
            aggregates[grp]["total"] += res.get("total_objects", 1)
        elif "is_violation" in res:
            aggregates[grp]["total"] += 1
            if res["is_violation"]:
                aggregates[grp]["violations"] += 1
                
    return aggregates

def calculate_contradiction_rate(constraints_dir: Path) -> float:
    """Helper to calculate contradiction rate (reused from analyzer concept)."""
    # Implementation simplified for this module context
    log_path = constraints_dir / "contradiction_log.json"
    if not log_path.exists():
        return 0.0
    try:
        with open(log_path) as f:
            data = json.load(f)
        count = len(data)
        # Total scenes estimation
        total = len(list(constraints_dir.glob("*.json"))) - 1 # minus log
        if total == 0: return 0.0
        return (count / (total + count)) * 100
    except:
        return 0.0

def verify_contradiction_rate(rate: float, threshold: float = 5.0) -> bool:
    return rate <= threshold

def run_power_analysis_and_report(effect_size: float = 0.2, alpha: float = 0.05, 
                                  power_target: float = 0.8, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run power analysis and save report.
    
    Args:
        effect_size: Expected effect size.
        alpha: Alpha level.
        power_target: Target power.
        output_path: Path to save the report.
        
    Returns:
        Report dictionary.
    """
    report = power_analysis_two_proportions(effect_size, alpha, power_target)
    
    if report["required_n_per_group"] > 10000: # Arbitrary safety check
         report["status"] = "WARNING: Required sample size is very large."
    else:
         report["status"] = "OK"
         
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
            
    return report

def run_statistical_comparison(results: List[Dict[str, Any]], group1: str, group2: str) -> Dict[str, Any]:
    """
    Run the appropriate statistical test between two groups.
    """
    agg = aggregate_violation_rates(results)
    
    if group1 not in agg or group2 not in agg:
        raise ValueError(f"Groups {group1} or {group2} not found in results.")
        
    d1 = agg[group1]
    d2 = agg[group2]
    
    test_type = select_statistical_test(d1["violations"], d1["total"], d2["violations"], d2["total"])
    
    result = {
        "test_type": test_type,
        "group1": group1,
        "group2": group2,
        "group1_counts": {"violations": d1["violations"], "total": d1["total"]},
        "group2_counts": {"violations": d2["violations"], "total": d2["total"]}
    }
    
    if test_type == "z_test":
        z, p = two_proportion_z_test(d1["violations"], d1["total"], d2["violations"], d2["total"])
        result["z_statistic"] = z
        result["p_value"] = p
    else:
        or_val, p = fisher_exact_test(d1["violations"], d1["total"], d2["violations"], d2["total"])
        result["odds_ratio"] = or_val
        result["p_value"] = p
        
    return result

def generate_final_analysis_csv(results: List[Dict[str, Any]], output_path: Path):
    """
    Generate the final analysis CSV with aggregated stats.
    """
    import csv
    
    agg = aggregate_violation_rates(results)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Group", "Total Scenes", "Violations", "Prompt Adherence Rate"])
        
        for group, data in agg.items():
            total = data["total"]
            violations = data["violations"]
            rate = 1.0 - (violations / total) if total > 0 else 1.0
            writer.writerow([group, total, violations, f"{rate:.4f}"])

def main():
    """Main entry point for statistics analysis."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    results_dir = base_dir / "data" / "derived" / "evaluation_results"
    output_csv = base_dir / "data" / "processed" / "final_analysis.csv"
    power_report = base_dir / "data" / "derived" / "evaluation_results" / "power_analysis_report.json"
    
    print(f"Loading evaluation results from: {results_dir}")
    results = load_evaluation_results(results_dir)
    
    if not results:
        print("No evaluation results found.")
        sys.exit(0)
        
    # Run Power Analysis
    print("Running Power Analysis...")
    run_power_analysis_and_report(output_path=power_report)
    print(f"Power analysis report saved to {power_report}")
    
    # Run Comparison (Baseline vs Experimental)
    try:
        print("Running Statistical Comparison (Baseline vs Experimental)...")
        comparison = run_statistical_comparison(results, "Baseline", "Experimental")
        print(f"Result: {comparison}")
        
        # Generate CSV
        print(f"Generating final analysis CSV at {output_csv}")
        generate_final_analysis_csv(results, output_csv)
        
    except ValueError as e:
        print(f"Comparison failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
