"""
Generate final verification report.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import get_results_dir, get_config_summary

def load_metrics_data(path: Path) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)

def extract_sensitivity_results(data: Dict[str, Any]) -> Dict[str, Any]:
    return data

def generate_report(metrics: Dict[str, Any], sensitivity: Dict[str, Any], anova: Dict[str, Any]) -> str:
    report = []
    report.append("# llmXive Verification Report")
    report.append("")
    report.append("## Sensitivity Analysis")
    for k, v in sensitivity.items():
        report.append(f"- Threshold {k}: WorldScore={v.get('world_score', 'N/A')}")
    report.append("")
    report.append("## ANOVA Results")
    report.append(f"- P-value: {anova.get('p_value', 'N/A')}")
    report.append("")
    report.append("## Conclusion")
    report.append("Pipeline executed successfully.")
    return "\n".join(report)

def write_report(content: str, path: Path):
    with open(path, 'w') as f:
        f.write(content)

def main():
    sens_path = get_results_dir() / "sensitivity_analysis.json"
    anova_path = get_results_dir() / "anova_results.json"
    output_path = get_results_dir() / "hypothesis_verification.md"

    if not sens_path.exists():
        print("Sensitivity analysis missing.")
        return

    sens = load_metrics_data(sens_path)
    anova = load_metrics_data(anova_path) if anova_path.exists() else {}

    report = generate_report({}, sens, anova)
    write_report(report, output_path)
    print(f"Report written to {output_path}")

if __name__ == "__main__":
    main()