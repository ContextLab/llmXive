import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import get_results_dir, get_config_summary

def load_metrics_data() -> Dict[str, Any]:
    """
    Load the aggregated metrics from data/results/metrics.json.
    Expects the file to exist as produced by T020 (main.py orchestrator).
    """
    results_dir = get_results_dir()
    metrics_path = results_dir / "metrics.json"
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}. "
                                "Ensure T020 (orchestrator) has run successfully.")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def calculate_time_reduction(metrics: Dict[str, Any]) -> Tuple[float, bool]:
    """
    Calculate the percentage reduction in inference time (Sparse vs Dense).
    Returns (reduction_percentage, pass_threshold).
    Threshold for SC-003 is 40% reduction.
    """
    dense_time = metrics.get("dense", {}).get("inference_time_seconds", 0)
    sparse_time = metrics.get("sparse", {}).get("inference_time_seconds", 0)
    
    if dense_time <= 0:
        # Avoid division by zero or invalid data
        return 0.0, False
    
    reduction = ((dense_time - sparse_time) / dense_time) * 100
    threshold = 40.0
    passed = reduction >= threshold
    
    return reduction, passed

def extract_anova_results(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract ANOVA results from the metrics data.
    Expected structure: metrics['anova']
    """
    return metrics.get("anova", {})

def extract_sensitivity_results(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract sensitivity analysis results from the metrics data.
    Expected structure: metrics['sensitivity']
    """
    return metrics.get("sensitivity", {})

def generate_report(metrics: Dict[str, Any]) -> str:
    """
    Generate the full markdown hypothesis verification report.
    Includes:
    - WorldScore vs. Sparse-Consistency comparison
    - ANOVA interaction effects
    - Sensitivity analysis stability
    - Inference time reduction status (Pass/Fail)
    """
    # Extract key metrics
    dense_metrics = metrics.get("dense", {})
    sparse_metrics = metrics.get("sparse", {})
    
    world_score = sparse_metrics.get("world_score", "N/A")
    sparse_consistency = sparse_metrics.get("sparse_consistency_score", "N/A")
    
    # Time reduction
    reduction_pct, time_passed = calculate_time_reduction(metrics)
    
    # ANOVA results
    anova_data = extract_anova_results(metrics)
    anova_interaction_p = anova_data.get("interaction_p_value", "N/A")
    anova_significant = "Yes" if (isinstance(anova_interaction_p, (int, float)) and anova_interaction_p < 0.05) else "No"
    
    # Sensitivity results
    sensitivity_data = extract_sensitivity_results(metrics)
    sensitivity_stable = "Stable" if sensitivity_data.get("stable", False) else "Unstable"
    
    # Build report
    report_lines = [
        "# Hypothesis Verification Report",
        "",
        f"**Generated**: {metrics.get('timestamp', 'N/A')}",
        f"**Config Summary**: {get_config_summary()}",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Inference Time Reduction**: {reduction_pct:.2f}% (Threshold: 40%) -> **{'PASS' if time_passed else 'FAIL'}**",
        "",
        "## 2. Metric Comparison",
        "",
        "| Metric | Sparse Method | Dense Baseline | Notes |",
        "|---|---|---|---|",
        f"| **WorldScore** | {world_score} | {dense_metrics.get('world_score', 'N/A')} | Topological fidelity |",
        f"| **Sparse-Consistency** | {sparse_consistency} | {dense_metrics.get('sparse_consistency_score', 'N/A')} | Reprojection error |",
        f"| **FID** | {sparse_metrics.get('fid', 'N/A')} | {dense_metrics.get('fid', 'N/A')} | Distribution similarity |",
        "",
        "## 3. Statistical Validation (ANOVA)",
        "",
        f"- **Interaction Effect (p-value)**: {anova_interaction_p}",
        f"- **Significant (p < 0.05)**: {anova_significant}",
        "",
        "## 4. Sensitivity Analysis",
        "",
        f"- **Stability Status**: {sensitivity_stable}",
        "",
        "## 5. Conclusion",
        "",
        f"The sparse method achieves a **{reduction_pct:.2f}%** reduction in inference time compared to the dense baseline.",
        f"This {'meets' if time_passed else 'does not meet'} the 40% threshold requirement (SC-003).",
        "",
        "### Final Verdict",
        "",
        f"**Hypothesis Status**: {'VERIFIED' if time_passed else 'NOT VERIFIED'}",
        ""
    ]
    
    return "\n".join(report_lines)

def write_report(report_content: str, output_path: Optional[Path] = None) -> Path:
    """
    Write the generated report to a markdown file.
    Default path: data/results/hypothesis_verification.md
    """
    if output_path is None:
        results_dir = get_results_dir()
        output_path = results_dir / "hypothesis_verification.md"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    return output_path

def main():
    """
    Main entry point for T021: Generate Hypothesis Verification Report.
    Reads metrics.json, computes time reduction, and writes hypothesis_verification.md.
    """
    try:
        print("Loading metrics data...")
        metrics = load_metrics_data()
        
        print("Generating report...")
        report_content = generate_report(metrics)
        
        print("Writing report to disk...")
        output_path = write_report(report_content)
        
        print(f"Report successfully written to: {output_path}")
        print("\n--- Report Preview ---")
        print(report_content)
        print("--- End Preview ---")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during report generation: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()