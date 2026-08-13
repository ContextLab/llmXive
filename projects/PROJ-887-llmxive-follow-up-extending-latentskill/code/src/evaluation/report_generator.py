"""
Report Generator for LatentSkill Evaluation Pipeline.

This module aggregates results from statistical tests, sensitivity analyses,
and linearity checks to generate a comprehensive final report in JSON format.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns None if file does not exist or is invalid.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Dictionary containing JSON data, or None if loading failed.
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def aggregate_results(
    stats_report: Optional[Dict[str, Any]],
    sensitivity_report: Optional[Dict[str, Any]],
    linearity_report: Optional[Dict[str, Any]],
    reconstruction_report: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate results from various analysis reports into a single comprehensive report.

    Args:
        stats_report: Results from statistical comparisons (T028, T029a, T029b).
        sensitivity_report: Results from sensitivity analysis (T031b).
        linearity_report: Results from linearity check (T030).
        reconstruction_report: Results from reconstruction error analysis (T022d).

    Returns:
        Comprehensive dictionary containing all aggregated results.
    """
    report = {
        "summary": {
            "pipeline_version": "1.0.0",
            "task_id": "T032",
            "description": "Final Statistical Report for LatentSkill Evaluation"
        },
        "statistical_analysis": {},
        "sensitivity_analysis": {},
        "linearity_validation": {},
        "reconstruction_error": {},
        "conclusions": []
    }

    # Aggregate statistical analysis
    if stats_report:
        report["statistical_analysis"] = stats_report
        # Add conclusions based on statistical significance
        if "comparisons" in stats_report:
            significant_findings = [
                comp for comp in stats_report["comparisons"]
                if comp.get("significant", False)
            ]
            if significant_findings:
                report["conclusions"].append(
                    f"Found {len(significant_findings)} statistically significant "
                    "differences between strategies (BH-corrected)."
                )
            else:
                report["conclusions"].append(
                    "No statistically significant differences found between strategies "
                    "after Benjamini-Hochberg correction."
                )
    else:
        report["conclusions"].append(
            "Statistical analysis report not available. "
            "Ensure T028 and T029a/T029b completed successfully."
        )

    # Aggregate sensitivity analysis
    if sensitivity_report:
        report["sensitivity_analysis"] = sensitivity_report
        # Analyze sensitivity to k values
        if "results" in sensitivity_report:
            k_values = list(sensitivity_report["results"].keys())
            report["conclusions"].append(
                f"Sensitivity analysis performed for k values: {k_values}."
            )
            # Check for optimal k
            best_k = None
            best_score = -float('inf')
            for k, results in sensitivity_report["results"].items():
                score = results.get("mean_success_rate", 0)
                if score > best_score:
                    best_score = score
                    best_k = k
            if best_k is not None:
                report["conclusions"].append(
                    f"Optimal k value found: k={best_k} with mean success rate {best_score:.4f}."
                )
    else:
        report["conclusions"].append(
            "Sensitivity analysis report not available. "
            "Ensure T031b completed successfully."
        )

    # Aggregate linearity validation
    if linearity_report:
        report["linearity_validation"] = linearity_report
        correlation = linearity_report.get("pearson_correlation", None)
        if correlation is not None:
            if abs(correlation) > 0.7:
                report["conclusions"].append(
                    f"Strong linearity observed between text and weight spaces "
                    f"(r={correlation:.4f})."
                )
            elif abs(correlation) > 0.3:
                report["conclusions"].append(
                    f"Moderate linearity observed between text and weight spaces "
                    f"(r={correlation:.4f})."
                )
            else:
                report["conclusions"].append(
                    f"Weak linearity observed between text and weight spaces "
                    f"(r={correlation:.4f}). Linearity assumption may not hold."
                )
    else:
        report["conclusions"].append(
            "Linearity validation report not available. "
            "Ensure T030 completed successfully."
        )

    # Aggregate reconstruction error
    if reconstruction_report:
        report["reconstruction_error"] = reconstruction_report
        mean_error = reconstruction_report.get("mean_error", None)
        max_error = reconstruction_report.get("max_error", None)
        if mean_error is not None:
            report["conclusions"].append(
                f"Mean reconstruction error: {mean_error:.6f}, "
                f"Max reconstruction error: {max_error:.6f}."
            )
            # Flag high error
            if max_error > 0.1:
                report["conclusions"].append(
                    "WARNING: High maximum reconstruction error detected. "
                    "This may indicate non-linear interactions in the skill space."
                )
    else:
        report["conclusions"].append(
            "Reconstruction error report not available. "
            "Ensure T022d completed successfully."
        )

    # Add overall summary
    report["summary"]["total_conclusions"] = len(report["conclusions"])
    report["summary"]["reports_aggregated"] = sum([
        1 if stats_report else 0,
        1 if sensitivity_report else 0,
        1 if linearity_report else 0,
        1 if reconstruction_report else 0
    ])

    return report

def main() -> int:
    """
    Main entry point for generating the final statistical report.

    Loads all prerequisite reports and aggregates them into a comprehensive
    final report saved to data/results/stats_report.json.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        # Define paths
        base_path = Path(__file__).parent.parent.parent
        results_dir = base_path / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # Define input file paths
        stats_file = results_dir / "statistics_report.json"
        sensitivity_file = results_dir / "sensitivity.yaml"
        linearity_file = results_dir / "linearity_check.json"
        reconstruction_file = results_dir / "reconstruction_error.json"

        # Define output file path
        output_file = results_dir / "stats_report.json"

        logger.info("Starting final report generation (T032)...")

        # Load prerequisite reports
        logger.info(f"Loading statistical report from {stats_file}...")
        stats_report = load_json_safe(stats_file)

        logger.info(f"Loading sensitivity report from {sensitivity_file}...")
        # Handle YAML for sensitivity report
        if sensitivity_file.exists():
            try:
                import yaml
                with open(sensitivity_file, 'r', encoding='utf-8') as f:
                    sensitivity_report = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading sensitivity report: {e}")
                sensitivity_report = None
        else:
            sensitivity_report = None

        logger.info(f"Loading linearity report from {linearity_file}...")
        linearity_report = load_json_safe(linearity_file)

        logger.info(f"Loading reconstruction error report from {reconstruction_file}...")
        reconstruction_report = load_json_safe(reconstruction_file)

        # Aggregate results
        logger.info("Aggregating results...")
        final_report = aggregate_results(
            stats_report,
            sensitivity_report,
            linearity_report,
            reconstruction_report
        )

        # Save final report
        logger.info(f"Saving final report to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)

        logger.info(f"Final report successfully generated: {output_file}")
        logger.info(f"Total conclusions: {final_report['summary']['total_conclusions']}")

        # Print summary
        print("\n" + "="*60)
        print("FINAL REPORT SUMMARY")
        print("="*60)
        for i, conclusion in enumerate(final_report["conclusions"], 1):
            print(f"{i}. {conclusion}")
        print("="*60)

        return 0

    except Exception as e:
        logger.error(f"Failed to generate final report: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())