"""
Report Generator for PROJ-015.

Generates the final report files (report_summary.txt, metrics_summary.csv)
with required citations to Constitution Principle VII and amended Spec FR-002.
"""
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

def _load_csv_safe(filepath: Path) -> Optional[pd.DataFrame]:
    """Safely load a CSV file, returning None if it doesn't exist."""
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return None
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        return None

def _generate_citations() -> str:
    """Generate the standard citation block for the report."""
    return (
        "---\n"
        "CITATIONS:\n"
        "This analysis adheres to Constitution Principle VII: 'Reproducibility and Transparency'.\n"
        "Statistical methodology follows Spec FR-002 (Amended): 'Repeated Measures ANOVA is the primary test for within-subject effects.'\n"
        "Normality checks (Shapiro-Wilk) are performed for audit purposes only; ANOVA robustness is relied upon per ratified amendment.\n"
        "Power analysis thresholds: Constitutional N >= 30.\n"
        "---\n"
    )

def generate_report_summary(
    metrics_summary_path: Path,
    power_report_path: Path,
    descriptive_stats_path: Path,
    output_path: Path
) -> None:
    """
    Assembles the final report_summary.txt by aggregating data from intermediate artifacts.
    
    Args:
        metrics_summary_path: Path to metrics_summary.csv (ANOVA results).
        power_report_path: Path to power_report.md.
        descriptive_stats_path: Path to descriptive_stats_explanation_engagement.csv.
        output_path: Path where report_summary.txt will be written.
    """
    logger.info(f"Generating report summary at {output_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    metrics_df = _load_csv_safe(metrics_summary_path)
    desc_df = _load_csv_safe(descriptive_stats_path)
    
    # Read power report if it exists
    power_content = ""
    if power_report_path.exists():
        with open(power_report_path, 'r') as f:
            power_content = f.read()
    else:
        logger.warning(f"Power report not found at {power_report_path}, skipping inclusion.")

    # Start building the report
    lines = []
    lines.append("# Final Usability Analysis Report")
    lines.append(f"Generated: {pd.Timestamp.now()}")
    lines.append("")
    
    lines.append("## 1. Executive Summary")
    lines.append("This report summarizes the statistical analysis of usability metrics comparing Traditional vs. Explainable interfaces.")
    lines.append("")

    lines.append("## 2. Statistical Methodology")
    lines.append("Per Spec FR-002 (Amended), Repeated Measures ANOVA was used for within-subject comparisons.")
    lines.append("Holm-Bonferroni correction was applied for multiple comparisons.")
    lines.append("")

    lines.append("## 3. ANOVA Results")
    if metrics_df is not None and not metrics_df.empty:
        lines.append("The following table summarizes the ANOVA results:")
        lines.append("")
        # Convert dataframe to markdown table
        lines.append(metrics_df.to_markdown(index=False))
        lines.append("")
    else:
        lines.append("*ANOVA results unavailable.*")
        lines.append("")

    lines.append("## 4. Power Analysis")
    lines.append(power_content if power_content else "*Power analysis report unavailable.*")
    lines.append("")

    lines.append("## 5. Descriptive Statistics (Explanation Engagement)")
    if desc_df is not None and not desc_df.empty:
        lines.append(desc_df.to_markdown(index=False))
        lines.append("")
    else:
        lines.append("*Descriptive statistics unavailable.*")
        lines.append("")

    lines.append(_generate_citations())

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Report summary written to {output_path}")

def main():
    """Main entry point for the report generator."""
    parser = argparse.ArgumentParser(description="Generate final analysis report.")
    parser.add_argument("--metrics", type=str, required=True, help="Path to metrics_summary.csv")
    parser.add_argument("--power", type=str, required=True, help="Path to power_report.md")
    parser.add_argument("--desc", type=str, required=True, help="Path to descriptive_stats_explanation_engagement.csv")
    parser.add_argument("--output", type=str, required=True, help="Path for report_summary.txt")
    
    args = parser.parse_args()

    # Resolve paths relative to project root if needed
    project_root = settings.project_root
    metrics_path = Path(args.metrics)
    power_path = Path(args.power)
    desc_path = Path(args.desc)
    output_path = Path(args.output)

    # If paths are relative and not absolute, assume they are relative to project root
    if not metrics_path.is_absolute():
        metrics_path = project_root / metrics_path
    if not power_path.is_absolute():
        power_path = project_root / power_path
    if not desc_path.is_absolute():
        desc_path = project_root / desc_path
    if not output_path.is_absolute():
        output_path = project_root / output_path

    generate_report_summary(metrics_path, power_path, desc_path, output_path)

if __name__ == "__main__":
    import argparse
    main()
