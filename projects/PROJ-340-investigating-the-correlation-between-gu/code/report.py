import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import get_config, load_config

def load_json_file(path: str) -> Dict:
    """Load a JSON file."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def load_correlation_results(path: str = "data/results/correlation_matrix.json") -> Dict:
    return load_json_file(path)

def load_diagnostics_report(path: str = "data/results/collinearity_report.json") -> Dict:
    return load_json_file(path)

def load_timing_evidence(path: str = "data/results/timing_evidence.json") -> Dict:
    return load_json_file(path)

def load_variable_metrics(path: str = "data/results/variable_load_metrics.json") -> Dict:
    return load_json_file(path)

def load_sensitivity_analysis(path: str = "data/results/sensitivity_analysis.json") -> List:
    return load_json_file(path)

def load_stability_metrics(path: str = "data/results/stability_metrics.json") -> Dict:
    return load_json_file(path)

def load_collinearity_report(path: str = "data/results/collinearity_report.json") -> Dict:
    return load_json_file(path)

def determine_data_source() -> str:
    """Determine if data is synthetic or real."""
    manifest_path = "data/metadata/synthetic_data_manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            data = json.load(f)
            if data.get('chain_of_custody_log') is None:
                return "Synthetic (Pipeline Validation)"
    return "Real"

def format_associational_warning() -> str:
    """Return associational framing warning."""
    return "Note: These results are associational. No causal claims are made."

def generate_report(output_path: str = "data/results/final_report.json") -> None:
    """Generate the final report."""
    source = determine_data_source()
    
    report = {
        "title": "Gut Microbiome and Sleep Architecture Correlation Study",
        "scope": "Pipeline Validation Study",
        "data_source": source,
        "disclaimer": "This study is a Pipeline Validation Study using synthetic data. No real-world biological correlations are established. Results demonstrate statistical engine correctness, not biological truth.",
        "timestamp": datetime.now().isoformat(),
        "methodology": {
            "framing": "Associational only",
            "correction": "Benjamini-Hochberg FDR"
        },
        "results_summary": load_correlation_results(),
        "diagnostics": load_collinearity_report(),
        "timing": load_timing_evidence(),
        "metrics": load_variable_metrics()
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"Report generated: {output_path}")

def main():
    """Entry point for report generation."""
    generate_report()

if __name__ == "__main__":
    main()
