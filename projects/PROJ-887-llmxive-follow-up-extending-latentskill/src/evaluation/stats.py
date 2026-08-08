"""
Statistical analysis module for llmXive evaluation pipeline.

Implements:
- Benjamini-Hochberg (BH) correction for multiple comparisons (FR-006)
- Aggregation of p-values from primary strategies and sensitivity sweeps
"""
import json
import math
from typing import Dict, List, Any, Tuple
import numpy as np

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg procedure to control False Discovery Rate (FDR).
    
    Args:
        p_values: List of raw p-values from statistical tests.
        alpha: Significance level (default 0.05).
        
    Returns:
        Tuple of:
        - adjusted_q_values: BH-adjusted q-values (FDR-corrected p-values).
        - significant: Boolean list indicating if each test is significant after correction.
        
    Raises:
        ValueError: If p_values is empty or contains non-finite values.
    """
    if not p_values:
        raise ValueError("p_values list cannot be empty")
    
    if not all(np.isfinite(p) and 0 <= p <= 1 for p in p_values):
        raise ValueError("All p-values must be finite and in range [0, 1]")
    
    m = len(p_values)
    # Sort p-values with their original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate BH adjusted q-values
    # q_i = p_i * m / i (where i is rank, 1-based)
    # Ensure monotonicity by taking cumulative min from the end
    ranks = np.arange(1, m + 1)
    q_values = sorted_p * m / ranks
    
    # Enforce monotonicity: q_i <= q_{i+1}
    # Iterate backwards to ensure q_i = min(q_i, q_{i+1})
    for i in range(m - 2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i + 1])
    
    # Cap at 1.0
    q_values = np.clip(q_values, 0, 1.0)
    
    # Map back to original order
    final_q_values = np.zeros(m)
    final_q_values[sorted_indices] = q_values
    
    # Determine significance
    significant = [q < alpha for q in final_q_values]
    
    return final_q_values.tolist(), significant

def aggregate_stats_report(
    base_p_values: Dict[str, float],
    sensitivity_p_values: Dict[str, Dict[str, float]],
    output_path: str
) -> Dict[str, Any]:
    """
    Aggregate p-values from primary strategy comparisons and sensitivity sweeps,
    apply BH correction, and write the final report.
    
    Args:
        base_p_values: Dict mapping comparison name (e.g., "strategy_A_vs_baseline") to p-value.
        sensitivity_p_values: Dict mapping sensitivity parameter (e.g., "k=1") to 
                             another Dict of comparison names to p-values.
        output_path: Path to write the final JSON report.
    
    Returns:
        The complete report dictionary.
    """
    # Flatten all comparisons for BH correction
    all_comparisons = []
    all_p_values = []
    
    # Add base strategy comparisons
    for name, p_val in base_p_values.items():
        all_comparisons.append({"type": "base", "name": name, "p_value": p_val})
        all_p_values.append(p_val)
    
    # Add sensitivity sweep comparisons
    for k_param, comparisons in sensitivity_p_values.items():
        for name, p_val in comparisons.items():
            all_comparisons.append({
                "type": "sensitivity",
                "k": k_param,
                "name": name,
                "p_value": p_val
            })
            all_p_values.append(p_val)
    
    if not all_p_values:
        raise ValueError("No p-values provided for BH correction.")
    
    # Apply BH correction
    adjusted_q_values, significant_flags = benjamini_hochberg(all_p_values)
    
    # Attach results back to comparisons
    for i, comp in enumerate(all_comparisons):
        comp["q_value"] = adjusted_q_values[i]
        comp["significant"] = significant_flags[i]
    
    # Construct final report
    report = {
        "method": "Benjamini-Hochberg",
        "alpha": 0.05,
        "total_comparisons": len(all_comparisons),
        "significant_count": sum(significant_flags),
        "comparisons": all_comparisons,
        "summary": {
            "base_strategies": {
                k: {"p": v, "significant": next(c["significant"] for c in all_comparisons if c["name"] == k and c["type"] == "base")}
                for k, v in base_p_values.items()
            },
            "sensitivity_analysis": {
                k_param: {
                    name: {"p": p, "significant": next(c["significant"] for c in all_comparisons if c["name"] == name and c["type"] == "sensitivity" and c["k"] == k_param)}
                    for name, p in comps.items()
                }
                for k_param, comps in sensitivity_p_values.items()
            }
        }
    }
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return report

# Example usage / entry point for testing if run directly
if __name__ == "__main__":
    # Mock data for demonstration of the logic
    mock_base = {
        "unweighted_vs_baseline": 0.012,
        "weighted_vs_baseline": 0.004,
        "single_vs_baseline": 0.089
    }
    mock_sensitivity = {
        "k=1": {"unweighted_vs_baseline": 0.015, "weighted_vs_baseline": 0.005},
        "k=3": {"unweighted_vs_baseline": 0.011, "weighted_vs_baseline": 0.003},
        "k=5": {"unweighted_vs_baseline": 0.014, "weighted_vs_baseline": 0.006}
    }
    
    result = aggregate_stats_report(
        mock_base,
        mock_sensitivity,
        "data/results/stats_report.json"
    )
    print(f"Report generated with {result['total_comparisons']} comparisons.")
    print(f"Significant findings: {result['significant_count']}")