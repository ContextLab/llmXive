"""
Report Generation Module for Co-Evolving Policy Distillation.

This module generates the final analysis report by aggregating forgetting rates,
ANOVA results, and retention comparisons into a single JSON artifact.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Ensure src is in path for imports when run as script
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.forgetting_metrics import compute_retention_metrics, load_agent_results
from src.analysis.statistical_tests import (
    run_statistical_analysis,
    StatisticalReport,
    load_forgetting_data,
    load_retention_data
)
from src.utils.checksums import compute_file_sha256


@dataclass
class ReportGenerationError(Exception):
    """Custom exception for report generation failures."""
    pass


def load_precomputed_anova_results(analysis_result_path: Path) -> Dict[str, Any]:
    """
    Loads the ANOVA and Tukey results from the statistical analysis output.
    Assumes the statistical analysis module has already written this to disk.
    """
    if not analysis_result_path.exists():
        raise ReportGenerationError(f"Statistical analysis result not found at {analysis_result_path}")
    
    with open(analysis_result_path, 'r') as f:
        data = json.load(f)
    
    return data


def load_retention_comparison_results(retention_path: Path) -> Dict[str, Any]:
    """
    Loads the retention comparison results from the retention metrics output.
    """
    if not retention_path.exists():
        raise ReportGenerationError(f"Retention comparison result not found at {retention_path}")
    
    with open(retention_path, 'r') as f:
        data = json.load(f)
    
    return data


def generate_final_report(
    forgetting_data_path: Path,
    retention_data_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Orchestrates the loading of statistical results and generates the final report.
    
    Args:
        forgetting_data_path: Path to the forgetting metrics data (JSON).
        retention_data_path: Path to the retention comparison data (JSON).
        output_path: Path where the final report will be saved.
        
    Returns:
        The generated report dictionary.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load pre-computed statistical results
    # The statistical_tests.py module (T027, T032) should have produced these files
    # We assume the standard output paths from the pipeline logic
    anova_file = forgetting_data_path.parent / "statistical_analysis_results.json"
    retention_file = retention_data_path.parent / "retention_comparison_results.json"

    # If the specific files above don't exist, try to load from the provided paths directly
    # or standard locations if the task implies T032/T027 wrote to specific locations.
    # Based on T030/T031/T032 descriptions, they likely wrote to data/results/.
    
    # Attempt to load ANOVA results
    try:
        anova_results = load_precomputed_anova_results(anova_file)
    except ReportGenerationError:
        # Fallback: If T027 hasn't written to the expected location, try to run the analysis
        # or raise an error if the data is strictly required to be pre-existing.
        # For T033, we assume T027/T032 have run and produced the artifacts.
        # If the file is missing, we raise a clear error.
        raise ReportGenerationError(
            f"Required statistical analysis results not found at {anova_file}. "
            "Ensure T027 (statistical analysis) and T032 (retention comparison) have completed."
        )

    # Attempt to load Retention Comparison results
    try:
        retention_results = load_retention_comparison_results(retention_file)
    except ReportGenerationError:
        raise ReportGenerationError(
            f"Required retention comparison results not found at {retention_file}. "
            "Ensure T031 and T032 have completed."
        )

    # Construct the final report
    report = {
        "report_metadata": {
            "generated_by": "T033_ReportGenerator",
            "version": "1.0.0",
            "description": "Final analysis report containing forgetting rates, ANOVA results, and retention comparisons."
        },
        "forgetting_analysis": anova_results.get("forgetting_analysis", {}),
        "anova_results": anova_results.get("anova_results", {}),
        "tukey_results": anova_results.get("tukey_results", {}),
        "retention_comparison": retention_results.get("retention_comparison", {}),
        "descriptive_statistics": anova_results.get("descriptive_statistics", {}),
        "summary": {
            "total_runs_analyzed": anova_results.get("total_runs_analyzed", 0),
            "significant_forgetting_detected": anova_results.get("significant_forgetting_detected", False),
            "coevolving_better_than_mixed": retention_results.get("coevolving_better_than_mixed", False),
            "key_finding": ""
        }
    }

    # Generate a human-readable summary string
    p_value = anova_results.get("anova_results", {}).get("p_value", 1.0)
    if p_value < 0.05:
        report["summary"]["key_finding"] = (
            "Statistically significant difference in forgetting rates detected between conditions (p < 0.05). "
            f"Co-evolving condition shows better retention compared to Mixed-task: {retention_results.get('coevolving_better_than_mixed', False)}."
        )
    else:
        report["summary"]["key_finding"] = (
            "No statistically significant difference in forgetting rates detected between conditions (p >= 0.05)."
        )

    # Save the report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report


def main():
    """
    Entry point for the report generation script.
    Expects data to be present in data/results/ from previous tasks (T027, T030, T032).
    """
    base_dir = Path(__file__).parent.parent.parent
    data_results_dir = base_dir / "data" / "results"
    
    # Define expected input paths based on previous task outputs
    # T030 aggregates data -> data/results/aggregated_forgetting_data.json (hypothetical or direct usage)
    # T031/T032 produce retention data
    # T027 produces statistical analysis data
    
    # We assume the statistical_tests.py main() wrote to:
    statistical_analysis_path = data_results_dir / "statistical_analysis_results.json"
    retention_comparison_path = data_results_dir / "retention_comparison_results.json"
    
    # And forgetting data is available at:
    forgetting_data_path = data_results_dir / "forgetting_metrics_data.json"
    
    output_path = data_results_dir / "forgetting_analysis.json"

    if not data_results_dir.exists():
        print(f"Error: Data results directory not found at {data_results_dir}")
        sys.exit(1)

    try:
        print(f"Generating report: {output_path}")
        report = generate_final_report(
            forgetting_data_path=forgetting_data_path,
            retention_data_path=retention_comparison_path,
            output_path=output_path
        )
        
        # Compute checksum for the report
        checksum = compute_file_sha256(output_path)
        print(f"Report generated successfully. SHA-256: {checksum}")
        print(f"Summary: {report['summary']['key_finding']}")
        
        return 0
    except ReportGenerationError as e:
        print(f"Report generation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during report generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
