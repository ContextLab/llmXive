import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import get_config, load_config

def load_correlation_results(path: str = "data/results/correlation_matrix.json") -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def load_diagnostics_report(path: str = "data/results/collinearity_report.json") -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def load_timing_evidence(path: str = "data/results/timing_evidence.json") -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def load_variable_metrics(path: str = "data/results/variable_load_metrics.json") -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def load_sensitivity_analysis(path: str = "data/results/sensitivity_analysis.json") -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def load_stability_metrics(path: str = "data/results/stability_metrics.json") -> Dict:
    if Path(path).exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def load_collinearity_report(path: str = "data/results/collinearity_report.json") -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def determine_data_source() -> str:
    """Determines if data is synthetic or real based on manifest."""
    manifest_path = Path("data/metadata/synthetic_data_manifest.json")
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        return manifest.get("data_type", "unknown")
    return "unknown"

def format_associational_warning() -> str:
    """Returns a warning string for associational framing."""
    return "NOTE: All results are associational. No causal claims are made."

def enforce_associational_framing(text: str) -> str:
    """
    Scans generated text for causal language ('causes', 'leads to', 'effect')
    and replaces with 'associational with', 'correlates with', 'relationship'.
    Addresses FR-004.
    """
    if not text:
        return text

    # Define patterns for causal language to replace
    # Using case-insensitive regex to catch variations
    replacements = [
        (r'\bcauses?\b', 'is associational with'),
        (r'\bleads to\b', 'correlates with'),
        (r'\beffect\b', 'relationship'),
        (r'\binfluences\b', 'is associational with'),
        (r'\bimpacts\b', 'is associational with'),
        (r'\bdrives\b', 'is associational with'),
        (r'\bresults in\b', 'is associational with'),
        (r'\btriggers\b', 'is associational with'),
    ]

    result = text
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result

def generate_report():
    """Generates the final report with enforced associational framing."""
    # Load all artifacts
    correlation = load_correlation_results()
    diagnostics = load_collinearity_report()
    timing = load_timing_evidence()
    variables = load_variable_metrics()
    sensitivity = load_sensitivity_analysis()
    source = determine_data_source()
    
    # Check for synthetic only state
    is_synthetic = source == "synthetic"
    
    # Build raw report content
    raw_report = {
        "title": "Gut Microbiome and Sleep Architecture Correlation Study",
        "date": datetime.now().isoformat(),
        "data_source": source,
        "disclaimer": "This study is a Pipeline Validation Study using synthetic data. No real-world biological correlations are established. Results demonstrate statistical engine correctness, not biological truth." if is_synthetic else "",
        "variable_load_metrics": variables,
        "timing_evidence": timing,
        "correlation_results_summary": {
            "total_pairs": len(correlation.get("correlations", [])),
            "significant_pairs": sum(1 for c in correlation.get("correlations", []) if c.get("p_value_adjusted", 1.0) <= 0.05)
        },
        "collinearity_diagnostics": diagnostics,
        "sensitivity_analysis": sensitivity,
        "warnings": [format_associational_warning()]
    }
    
    # Convert report to string for framing enforcement
    # We enforce framing on the textual representation of the report
    # to catch any causal language that might have been introduced
    # in descriptions or summaries.
    report_text = json.dumps(raw_report, indent=2)
    framed_text = enforce_associational_framing(report_text)
    
    # Parse back to dict to ensure valid JSON structure
    try:
        framed_report = json.loads(framed_text)
    except json.JSONDecodeError:
        # Fallback: use original if framing breaks JSON (should not happen)
        framed_report = raw_report
    
    output_path = Path("data/results/final_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(framed_report, f, indent=2)
    
    print(f"Report generated: {output_path}")

def main():
    generate_report()

if __name__ == "__main__":
    main()