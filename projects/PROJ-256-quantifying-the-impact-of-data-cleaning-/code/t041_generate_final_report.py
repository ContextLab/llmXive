import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np
from config import get_config

logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Any:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def aggregate_artifacts(baseline_metrics: List, cleaned_metrics: List, comparison_report: Dict, fpr_metrics: List) -> Dict[str, Any]:
    """Aggregate all artifacts into a final report."""
    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_datasets": len(baseline_metrics),
            "cleaned_variants": len(cleaned_metrics),
            "comparison_metrics": {
                "p_value_shifts": comparison_report.get("p_value_shifts", []),
                "ci_width_changes": comparison_report.get("ci_width_changes", []),
                "inconsistency_rate": comparison_report.get("inconsistency_rate", 0)
            },
            "fpr_estimates": fpr_metrics
        },
        "artifacts": {
            "baseline_metrics": baseline_metrics,
            "cleaned_metrics": cleaned_metrics,
            "comparison_report": comparison_report,
            "fpr_metrics": fpr_metrics
        }
    }

def write_summary_text(report: Dict[str, Any], output_path: str) -> None:
    """Write a human-readable summary text file."""
    with open(output_path, 'w') as f:
        f.write("=== Research Pipeline Final Report ===\n\n")
        f.write(f"Generated: {report['generated_at']}\n\n")
        
        summary = report['summary']
        f.write(f"Total Datasets Analyzed: {summary['total_datasets']}\n")
        f.write(f"Cleaned Variants: {summary['cleaned_variants']}\n\n")
        
        f.write("Comparison Metrics:\n")
        cm = summary['comparison_metrics']
        f.write(f"  Inconsistency Rate: {cm['inconsistency_rate']:.3f}\n\n")
        
        f.write("FPR Estimates:\n")
        for fp in summary['fpr_estimates']:
            f.write(f"  {fp['dataset_name']}: {fp['fpr']:.3f}\n")

def main():
    """Generate final comprehensive report."""
    logger.info("Generating final report")
    
    config = get_config()
    baseline_file = config.get("BASELINE_OUTPUT_PATH", "data/processed/baseline_metrics.json")
    cleaned_file = config.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    comparison_file = config.get("COMPARISON_OUTPUT_PATH", "data/processed/comparison_report.json")
    fpr_file = config.get("NULL_FPR_PATH", "data/processed/null_fpr_metrics.json")
    output_dir = config.get("OUTPUT_PATH", "data/processed")
    
    # Load artifacts
    baseline_metrics = load_json_file(baseline_file) if os.path.exists(baseline_file) else []
    cleaned_metrics = load_json_file(cleaned_file) if os.path.exists(cleaned_file) else []
    comparison_report = load_json_file(comparison_file) if os.path.exists(comparison_file) else {}
    fpr_metrics = load_json_file(fpr_file) if os.path.exists(fpr_file) else []
    
    # Aggregate
    final_report = aggregate_artifacts(baseline_metrics, cleaned_metrics, comparison_report, fpr_metrics)
    
    # Write JSON report
    json_output = os.path.join(output_dir, "final_report.json")
    with open(json_output, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    # Write text summary
    text_output = os.path.join(output_dir, "final_report_summary.txt")
    write_summary_text(final_report, text_output)
    
    logger.info(f"Wrote final report to {json_output}")
    logger.info(f"Wrote summary to {text_output}")

if __name__ == "__main__":
    main()