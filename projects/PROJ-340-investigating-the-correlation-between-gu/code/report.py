"""
Report Generation Module.
Generates the final markdown report with associational framing.
"""
import json
import os
from pathlib import Path
from datetime import datetime

def load_json_file(path: str) -> dict:
    with open(path, 'r') as f:
        return json.load(f)

def generate_report():
    """Generate the final markdown report."""
    # Load results
    corr_data = load_json_file("data/results/correlation_matrix.json")
    sens_data = load_json_file("data/results/sensitivity_analysis.json")
    power_data = load_json_file("data/results/power_analysis.json")
    
    report_lines = [
        "# Gut Microbiome and Sleep Architecture Analysis Report",
        "",
        "## Disclaimer",
        "",
        "**These results represent an associational relationship.** No causal claims are made.",
        "",
        "## Correlation Results",
        "",
        "| Predictor | Outcome | Correlation | P-Value | Significant |",
        "|---|---|---|---|---|"
    ]
    
    for row in corr_data:
        sig = "Yes" if row.get('significant', False) else "No"
        report_lines.append(
            f"| {row['predictor']} | {row['outcome']} | {row['correlation']:.3f} | {row['p_value']:.4f} | {sig} |"
        )
    
    report_lines.extend([
        "",
        "## Sensitivity Analysis",
        "",
        f"Stability Status: {sens_data['stability_status']}",
        ""
    ])
    
    report_lines.extend([
        "## Power Analysis",
        "",
        f"Minimum sample size required: {power_data['min_sample_size']}",
        ""
    ])
    
    report_content = "\n".join(report_lines)
    
    output_path = "data/results/final_report.md"
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    print(f"Report generated: {output_path}")

def main():
    generate_report()

if __name__ == "__main__":
    main()