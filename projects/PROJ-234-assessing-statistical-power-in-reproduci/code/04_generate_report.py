"""
T034: Generate the final audit report aggregating power audit results, extraction stats,
sensitivity delta, and MDES summary. Produces a histogram and a markdown report.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import matplotlib.pyplot as plt
import numpy as np

# Ensure we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging_config import setup_logging

# Configure logging
logger = setup_logging()

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Input files expected from previous tasks
POWER_AUDIT_RESULTS_FILE = DATA_PROCESSED / "power_audit_results.json"
EXTRACTION_STATS_FILE = DATA_PROCESSED / "extraction_stats.json"
SENSITIVITY_DELTA_FILE = DATA_PROCESSED / "sensitivity_delta_report.json"
MDES_SUMMARY_FILE = DATA_PROCESSED / "mdes_summary.json"

# Output files
OUTPUT_REPORT_MD = DATA_PROCESSED / "audit_report.md"
OUTPUT_POWER_HISTOGRAM = DATA_PROCESSED / "power_histogram.png"


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}. Returning empty dict.")
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return {}


def generate_power_histogram(power_values: List[float], output_path: Path) -> None:
    """
    Generate a histogram of observed power values and save it as a PNG.
    Bins=20, color=steelblue.
    """
    if not power_values:
        logger.warning("No power values provided for histogram. Creating empty plot.")
        plt.figure(figsize=(10, 6))
        plt.title("Observed Power Distribution (No Data)")
        plt.xlabel("Observed Power")
        plt.ylabel("Frequency")
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

    plt.figure(figsize=(10, 6))
    plt.hist(power_values, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
    plt.title("Distribution of Observed Statistical Power")
    plt.xlabel("Observed Power")
    plt.ylabel("Frequency")
    plt.xlim(0, 1.05)
    plt.axvline(x=0.8, color='red', linestyle='--', linewidth=2, label='Threshold (0.8)')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Power histogram saved to {output_path}")


def calculate_power_below_threshold(power_values: List[float]) -> float:
    """Calculate the fraction of studies with observed power < 0.8."""
    if not power_values:
        return 0.0
    below_count = sum(1 for p in power_values if p < 0.8)
    return below_count / len(power_values)


def assemble_report(
    power_results: Dict[str, Any],
    extraction_stats: Dict[str, Any],
    sensitivity_delta: Dict[str, Any],
    mdes_summary: Dict[str, Any],
    power_histogram_path: str
) -> str:
    """Assemble the markdown report content."""

    # Extract data for report
    total_studies = power_results.get("total_count", 0)
    power_values = power_results.get("power_values", [])
    power_below_frac = calculate_power_below_threshold(power_values)
    mdes_median = mdes_summary.get("median", "N/A")
    mdes_iqr = mdes_summary.get("iqr", "N/A")

    # Build sections
    lines = [
        "# Audit Report: Statistical Power in Reproducible Research",
        "",
        "## 1. Overview",
        f"This report analyzes the statistical power and sensitivity of {total_studies} public datasets",
        "retrieved from OpenML. It evaluates whether observed power meets the 0.8 threshold",
        "and provides the Minimum Detectable Effect Size (MDES) distribution.",
        "",
        "## 2. Dataset Ingestion Summary",
        f"- **Total Datasets Analyzed**: {total_studies}",
        "",
        "## 3. Extraction Statistics",
    ]

    if extraction_stats:
        success_rate = extraction_stats.get("success_rate", "N/A")
        failure_reasons = extraction_stats.get("failure_reasons", {})
        lines.append(f"- **Extraction Success Rate**: {success_rate}")
        lines.append("- **Failure Breakdown**:")
        for reason, count in failure_reasons.items():
            lines.append(f"  - {reason}: {count}")
    else:
        lines.append("- Extraction statistics not available.")

    lines.append("")
    lines.append("## 4. Observed Power Results")
    lines.append(f"- **Fraction of studies with Power < 0.8**: {power_below_frac:.2%}")
    lines.append("")
    lines.append("### Power Distribution Histogram")
    lines.append(f"![Power Histogram]({power_histogram_path})")
    lines.append("")
    lines.append("## 5. MDES Results")
    lines.append(f"- **Median MDES**: {mdes_median}")
    lines.append(f"- **IQR MDES**: {mdes_iqr}")
    lines.append("")
    lines.append("### MDES Distribution")
    # Reference the MDES histogram generated in T036
    mdes_hist_path = DATA_PROCESSED / "mdes_histogram.png"
    if mdes_hist_path.exists():
        lines.append(f"![MDES Histogram]({mdes_hist_path})")
    else:
        lines.append("*MDES histogram not found.*")
    lines.append("")
    lines.append("## 6. Sensitivity Delta (Optional)")
    if sensitivity_delta:
        lines.append(f"- **Full Text Success Rate**: {sensitivity_delta.get('full_text_rate', 'N/A')}")
        lines.append(f"- **Combined (Text+Abstract) Success Rate**: {sensitivity_delta.get('combined_rate', 'N/A')}")
        lines.append(f"- **Delta**: {sensitivity_delta.get('delta', 'N/A')}")
    else:
        lines.append("- Sensitivity delta report not available.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**Disclaimer:** Observed power is a monotone function of the p‑value and should not be used for post‑hoc validation (Hoenig & Heisey).")
    lines.append("")
    lines.append("The research question is to determine whether observed power is appropriate for post‑hoc validation. The method involves a theoretical analysis of the monotonic relationship between observed power and p‑values.")

    return "\n".join(lines)


def main():
    """Main entry point for T034."""
    logger.info("Starting report generation (T034)...")

    # Ensure output directory exists
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # Load input data
    power_results_data = load_json_file(POWER_AUDIT_RESULTS_FILE)
    extraction_stats_data = load_json_file(EXTRACTION_STATS_FILE)
    sensitivity_delta_data = load_json_file(SENSITIVITY_DELTA_FILE)
    mdes_summary_data = load_json_file(MDES_SUMMARY_FILE)

    # Extract power values for histogram
    # The power_audit_results.json structure from T033 is expected to be a list of records
    # or a dict containing a list. We handle both.
    records = []
    if isinstance(power_results_data, list):
        records = power_results_data
    elif isinstance(power_results_data, dict) and "results" in power_results_data:
        records = power_results_data["results"]
    
    power_values = [r.get("observed_power") for r in records if r.get("observed_power") is not None]
    
    # Generate Histogram
    generate_power_histogram(power_values, OUTPUT_POWER_HISTOGRAM)

    # Prepare data for report
    # Construct a summary dict for the report assembler
    power_summary = {
        "total_count": len(records),
        "power_values": power_values
    }

    # Assemble Report
    report_content = assemble_report(
        power_results=power_summary,
        extraction_stats=extraction_stats_data,
        sensitivity_delta=sensitivity_delta_data,
        mdes_summary=mdes_summary_data,
        power_histogram_path=OUTPUT_POWER_HISTOGRAM.name
    )

    # Write Report
    with open(OUTPUT_REPORT_MD, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"Audit report generated successfully at {OUTPUT_REPORT_MD}")
    logger.info(f"Power histogram generated at {OUTPUT_POWER_HISTOGRAM}")


if __name__ == "__main__":
    main()