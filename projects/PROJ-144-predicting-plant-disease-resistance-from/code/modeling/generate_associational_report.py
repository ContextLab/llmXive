import os
import json
import sys
from pathlib import Path
from datetime import datetime
from utils.constants import RESULTS_DIR, DATA_PROCESSED_DIR

def load_json_file(file_path: Path) -> dict:
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def generate_associational_report(metrics: dict, shap: dict) -> str:
    report = []
    report.append("# Associational Analysis Report")
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("\n## Important Note")
    report.append("All findings in this report are framed as **ASSOCIATIONAL**.")
    report.append("No causal inferences are made from these results.")
    report.append("\n## Metrics Summary")
    report.append(json.dumps(metrics, indent=2))
    report.append("\n## SHAP Analysis Summary")
    report.append(json.dumps(shap, indent=2))
    report.append("\n## Conclusion")
    report.append("The observed associations between metabolite profiles and disease resistance")
    report.append("warrant further investigation but do not imply causation.")
    return "\n".join(report)

def main():
    # Load results
    metrics_path = RESULTS_DIR / "metrics.json"
    shap_path = RESULTS_DIR / "shap_analysis.json"
    
    metrics = load_json_file(metrics_path)
    shap = load_json_file(shap_path)
    
    report_content = generate_associational_report(metrics, shap)
    
    report_path = RESULTS_DIR / "associational_report.md"
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    print(f"Associational report saved to {report_path}")

if __name__ == "__main__":
    main()
