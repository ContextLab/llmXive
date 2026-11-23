"""07_generate_report.py

Report generation script for the primary analysis.

This script combines LMM summary, post-hoc results, exclusion logs,
and sensitivity analysis into a comprehensive markdown report.
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_results_dir, get_processed_data_dir
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

def get_lmm_summary_path() -> Path:
    return get_results_dir() / "lmm_summary.csv"

def get_posthoc_path() -> Path:
    return get_results_dir() / "posthoc_tukey.csv"

def get_excluded_participants_path() -> Path:
    return get_processed_data_dir() / "excluded_participants.csv"

def get_sensitivity_metrics_path() -> Path:
    return get_processed_data_dir() / "sensitivity_metrics.csv"

def get_power_analysis_path() -> Path:
    return get_processed_data_dir() / "power_analysis_results.json"

def load_csv(path: Path) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return []

    results = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_report() -> None:
    """Generate the final analysis report."""
    report_path = get_results_dir() / "report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Load all necessary data
    lmm_summary = load_csv(get_lmm_summary_path())
    posthoc_results = load_csv(get_posthoc_path())
    excluded_participants = load_csv(get_excluded_participants_path())
    sensitivity_metrics = load_csv(get_sensitivity_metrics_path())
    power_analysis = load_json(get_power_analysis_path())

    with open(report_path, "w", encoding="utf-8") as f:
        # Title and Introduction
        f.write("# Primary Analysis Report: Text Message Tone and Emotional Support\n\n")
        f.write("## Overview\n\n")
        f.write("This report presents the results of the primary analysis examining ")
        f.write("the impact of text message tone on perceived emotional support. ")
        f.write("The analysis uses Linear Mixed Models (LMM) with random intercepts ")
        f.write("for participants and stimuli.\n\n")

        # Power Analysis Section
        f.write("## Power Analysis\n\n")
        if power_analysis:
            f.write(f"- **Estimated Power**: {power_analysis.get('estimated_power', 'N/A')}\n")
            f.write(f"- **Target Sample Size**: {power_analysis.get('target_N', 'N/A')}\n")
            f.write(f"- **Method**: {power_analysis.get('method', 'N/A')}\n\n")
        else:
            f.write("Power analysis results not available.\n\n")

        # Data Cleaning Summary
        f.write("## Data Cleaning Summary\n\n")
        f.write(f"- **Excluded Participants**: {len(excluded_participants)}\n")
        if excluded_participants:
            f.write("### Excluded Participant IDs\n\n")
            for participant in excluded_participants:
                f.write(f"- {participant.get('participant_id', 'Unknown')}\n")
        f.write("\n")

        # LMM Results
        f.write("## Linear Mixed Model Results\n\n")
        f.write("### Fixed Effects\n\n")
        f.write("| Fixed Effect | Estimate | Std Error | Z Value | P Value |\n")
        f.write("|--------------|----------|-----------|---------|---------|\n")
        for row in lmm_summary:
            f.write(f"| {row.get('fixed_effect', '')} | ")
            f.write(f"{row.get('estimate', '')} | ")
            f.write(f"{row.get('stderr', '')} | ")
            f.write(f"{row.get('z_value', '')} | ")
            f.write(f"{row.get('p_value', '')} |\n")
        f.write("\n")

        # Post-hoc Results
        f.write("## Post-hoc Analysis (Tukey HSD)\n\n")
        if posthoc_results:
            f.write("| Comparison | Estimate | Std Error | P Value | Significant |\n")
            f.write("|------------|----------|-----------|---------|-------------|\n")
            for row in posthoc_results:
                f.write(f"| {row.get('comparison', '')} | ")
                f.write(f"{row.get('estimate', '')} | ")
                f.write(f"{row.get('stderr', '')} | ")
                f.write(f"{row.get('p_value', '')} | ")
                f.write(f"{row.get('significant', '')} |\n")
        else:
            f.write("No significant interaction effect detected; post-hoc tests not performed.\n")
        f.write("\n")

        # Sensitivity Analysis
        f.write("## Sensitivity Analysis\n\n")
        if sensitivity_metrics:
            f.write("### Stability Across Weighting Schemes\n\n")
            f.write("| Scheme | Beta Interaction | P Value | Significant | Stability Score |\n")
            f.write("|--------|------------------|---------|-------------|-----------------|\n")
            for row in sensitivity_metrics:
                f.write(f"| {row.get('scheme', '')} | ")
                f.write(f"{row.get('beta_interaction', '')} | ")
                f.write(f"{row.get('p_value', '')} | ")
                f.write(f"{row.get('significant', '')} | ")
                f.write(f"{row.get('stability_score', '')} |\n")

            # Interpretation
            significant_count = sum(1 for row in sensitivity_metrics if row.get("significant") == "True")
            f.write("\n### Conclusion\n\n")
            if significant_count == len(sensitivity_metrics):
                f.write("The interaction effect is **robust** across all weighting schemes.\n")
            elif significant_count > 0:
                f.write("The interaction effect is **partially robust**, significant in some schemes.\n")
            else:
                f.write("The interaction effect is **not robust** across weighting schemes.\n")
        else:
            f.write("Sensitivity analysis results not available.\n")
        f.write("\n")

        # Methodological Limitations
        f.write("## Methodological Limitations\n\n")
        f.write("This analysis uses the **Wald-Z approximation** for p-value calculation ")
        f.write("via statsmodels, as the Satterthwaite approximation is not available ")
        f.write("in the Python-only stack. This choice is documented in ")
        f.write("`data/results/methodological_limitations.md`.\n\n")

        # Reproducibility
        f.write("## Reproducibility\n\n")
        f.write("All analysis scripts are deterministic when run with the same ")
        f.write("random seed. Checksums for all output files are recorded in ")
        f.write("`data/checksums.json`.\n")

    logger.info(f"Report generated at {report_path}")

def main() -> int:
    """Main entry point."""
    try:
        logger.info("Starting report generation.")
        generate_report()
        logger.info("Report generation complete.")
        return 0
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())