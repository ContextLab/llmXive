"""
Sensitivity Report Generator for User Story 3.

Generates a summary report in Markdown comparing 4mm vs 8mm temporal smoothing
kernel results, including effect size differences and replication rate variations.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_power_curve_results(input_path: Path) -> Dict[str, Any]:
    """
    Load power curve results from the aggregated JSON file.

    Args:
        input_path: Path to the power curves JSON file (aggregated or corrected).

    Returns:
        Dictionary containing power curve data organized by paradigm and kernel.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading power curve results from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def generate_sensitivity_summary(
    data: Dict[str, Any],
    kernel_a: float = 4.0,
    kernel_b: float = 8.0
) -> Dict[str, Any]:
    """
    Analyze power curve data to generate sensitivity summary statistics.

    Compares replication rates and effect sizes between two smoothing kernels.

    Args:
        data: Power curve data dictionary.
        kernel_a: First kernel size (default 4mm).
        kernel_b: Second kernel size (default 8mm).

    Returns:
        Dictionary containing sensitivity analysis results.
    """
    summary = {
        "comparison": {
            "kernel_a": kernel_a,
            "kernel_b": kernel_b,
            "paradigms": []
        },
        "overall_sensitivity": {
            "high_sensitivity_count": 0,
            "total_paradigms": 0
        }
    }

    paradigms = data.get("paradigms", [])

    for paradigm in paradigms:
        paradigm_name = paradigm.get("paradigm_name", "Unknown")
        kernel_results = paradigm.get("kernel_results", {})

        result_a = kernel_results.get(str(kernel_a))
        result_b = kernel_results.get(str(kernel_b))

        if not result_a or not result_b:
            logger.warning(f"Missing kernel data for {paradigm_name}: "
                         f"Has 4mm: {bool(result_a)}, Has 8mm: {bool(result_b)}")
            continue

        # Extract metrics
        rate_a = result_a.get("empirical_replication_rate", 0.0)
        rate_b = result_b.get("empirical_replication_rate", 0.0)
        effect_a = result_a.get("mean_effect_size", 0.0)
        effect_b = result_b.get("mean_effect_size", 0.0)

        # Calculate differences
        rate_diff = abs(rate_a - rate_b) * 100  # Percentage points
        effect_diff = abs(effect_a - effect_b)

        # Determine sensitivity flag (T033 logic: >10 percentage points)
        is_high_sensitivity = rate_diff > 10.0

        paradigm_summary = {
            "paradigm_name": paradigm_name,
            "kernel_a": {
                "size_mm": kernel_a,
                "replication_rate": rate_a,
                "effect_size": effect_a
            },
            "kernel_b": {
                "size_mm": kernel_b,
                "replication_rate": rate_b,
                "effect_size": effect_b
            },
            "differences": {
                "rate_diff_pp": round(rate_diff, 2),
                "effect_diff": round(effect_diff, 4)
            },
            "high_sensitivity": is_high_sensitivity
        }

        summary["comparison"]["paradigms"].append(paradigm_summary)

        if is_high_sensitivity:
            summary["overall_sensitivity"]["high_sensitivity_count"] += 1

        summary["overall_sensitivity"]["total_paradigms"] += 1

    return summary


def render_markdown_report(
    summary: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Render the sensitivity analysis summary to a Markdown report.

    Args:
        summary: Sensitivity analysis results dictionary.
        output_path: Path to write the Markdown report.
    """
    lines = []
    lines.append("# Preprocessing Sensitivity Analysis Report")
    lines.append("")
    lines.append(f"**Generated**: {summary.get('timestamp', 'N/A')}")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("This report compares the impact of different temporal smoothing kernels")
    lines.append("on statistical power and replication success in fMRI analysis.")
    lines.append(f"Comparison: **{summary['comparison']['kernel_a']}mm** vs **{summary['comparison']['kernel_b']}mm**")
    lines.append("")

    # Summary Statistics
    total = summary["overall_sensitivity"]["total_paradigms"]
    high_sens = summary["overall_sensitivity"]["high_sensitivity_count"]
    lines.append("### Summary Statistics")
    lines.append("")
    lines.append(f"- **Total Paradigms Analyzed**: {total}")
    lines.append(f"- **High Sensitivity Cases (>10pp rate diff)**: {high_sens}")
    if total > 0:
        pct = (high_sens / total) * 100
        lines.append(f"- **Percentage of High Sensitivity**: {pct:.1f}%")
    lines.append("")

    if high_sens > 0:
        lines.append("> **⚠️ Alert**: High sensitivity detected in some paradigms. ")
        lines.append("> This indicates that preprocessing choices significantly impact replication outcomes.")
        lines.append("")

    lines.append("## Detailed Results by Paradigm")
    lines.append("")

    for p_summary in summary["comparison"]["paradigms"]:
        pname = p_summary["paradigm_name"]
        lines.append(f"### {pname}")
        lines.append("")
        lines.append("| Metric | 4mm Kernel | 8mm Kernel | Difference |")
        lines.append("| :--- | :---: | :---: | :---: |")
        lines.append(f"| Replication Rate | {p_summary['kernel_a']['replication_rate']:.3f} | "
                   f"{p_summary['kernel_b']['replication_rate']:.3f} | "
                   f"{p_summary['differences']['rate_diff_pp']:.2f} pp |")
        lines.append(f"| Effect Size (Cohen's d) | {p_summary['kernel_a']['effect_size']:.4f} | "
                   f"{p_summary['kernel_b']['effect_size']:.4f} | "
                   f"{p_summary['differences']['effect_diff']:.4f} |")
        lines.append("")

        if p_summary["high_sensitivity"]:
            lines.append("> **⚠️ High Sensitivity**: Replication rate difference exceeds 10 percentage points.")
            lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append("- **Data Source**: Openly available fMRI datasets (OpenNeuro)")
    lines.append("- **Preprocessing**: Custom ROI extraction pipeline (fMRIPrep NOT used)")
    lines.append("- **Smoothing**: Temporal smoothing applied to ROI time-series")
    lines.append("- **Power Estimation**: Bootstrap resampling with split-half validation")
    lines.append("- **Significance Threshold**: Alpha = 0.05 (FDR corrected where applicable)")
    lines.append("")
    lines.append("## Conclusions")
    lines.append("")
    if high_sens > 0:
        lines.append("The analysis indicates that preprocessing smoothing parameters have a "
                   "significant impact on statistical power and replication success. "
                   "Researchers should carefully justify their choice of smoothing kernel "
                   "based on the specific cognitive paradigm and expected effect sizes.")
    else:
        lines.append("The analysis indicates that preprocessing smoothing parameters have "
                   "a relatively stable impact across the tested paradigms. "
                   "However, local variations may still exist for specific effect sizes.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by llmXive automated science pipeline*")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Sensitivity report written to {output_path}")


def main() -> int:
    """
    Main entry point for generating the sensitivity report.

    Expects power curve data in data/aggregated/corrected_power_curves.json
    and writes results to results/paper/sensitivity_report.md.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "aggregated" / "corrected_power_curves.json"
    output_path = project_root / "results" / "paper" / "sensitivity_report.md"

    # Allow CLI override
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    try:
        # Load data
        data = load_power_curve_results(input_path)

        # Generate summary
        summary = generate_sensitivity_summary(data)
        summary["timestamp"] = str(Path(__file__).stat().st_mtime)  # Placeholder for real time

        # Render report
        render_markdown_report(summary, output_path)

        logger.info("Sensitivity report generation completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
