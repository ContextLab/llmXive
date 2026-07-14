"""Report generation module for assembling Markdown/PDF reports."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from code.logging_config import get_logger

logger = get_logger(__name__)

# Ensure templates directory exists
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

def load_template(template_name: str = "report_template.md") -> str:
    """Load the report template from disk or create a fallback if missing."""
    template_path = TEMPLATES_DIR / template_name
    
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Fallback template if file is missing (should not happen if T033 ran correctly)
    fallback = """# Brain Network Dynamics and Sensorimotor Performance Report

**Generated:** {{date}}
**Project:** Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

## Executive Summary

This report presents the findings from the analysis of brain network dynamics and their association with sensorimotor performance metrics.

## Data Overview

- **Subjects Analyzed:** {{subjects_analyzed}}
- **Data Source:** HCP (Human Connectome Project) / ADHD-200
- **Atlas:** Schaefer 400 Parcellation

## Correlation Results

{{correlation_table}}

## Power Analysis

{{power_analysis}}

## Visualizations

{{plots}}

## Limitations

{{limitations}}

## Conclusion

{{conclusion}}

---
*Generated automatically by the llmXive automated science pipeline.*"""
    return fallback

def format_correlation_table(correlation_results: Optional[pd.DataFrame]) -> str:
    """Format correlation results as a Markdown table."""
    if correlation_results is None or correlation_results.empty:
        return "*No correlation results available.*"
    
    # Ensure necessary columns exist
    required_cols = ["metric_name", "r", "p", "q", "significant"]
    available_cols = [c for c in required_cols if c in correlation_results.columns]
    
    df_display = correlation_results[available_cols].copy()
    df_display["significant"] = df_display["significant"].apply(lambda x: "Yes" if x else "No")
    
    # Round numeric columns
    for col in ["r", "p", "q"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].round(4)
    
    return df_display.to_markdown(index=False)

def format_power_analysis(power_results: Optional[Dict[str, Any]]) -> str:
    """Format power analysis results."""
    if not power_results:
        return "*No power analysis results available.*"
    
    lines = []
    lines.append(f"- **Sample Size (N):** {power_results.get('n', 'N/A')}")
    lines.append(f"- **Power Level:** {power_results.get('power', '80%')}")
    lines.append(f"- **Significance Level (α):** {power_results.get('alpha', '0.05')}")
    lines.append(f"- **Detectable Effect Size (r):** {power_results.get('detectable_r', 'N/A'):.4f}" if isinstance(power_results.get('detectable_r'), (int, float)) else f"- **Detectable Effect Size (r):** {power_results.get('detectable_r', 'N/A')}")
    lines.append(f"- **Confidence Interval:** {power_results.get('ci', 'N/A')}")
    
    return "\n".join(lines)

def format_plots(plot_files: List[str]) -> str:
    """Format plot file references as Markdown image links."""
    if not plot_files:
        return "*No plots generated.*"
    
    lines = []
    for plot_file in plot_files:
        plot_path = Path(plot_file)
        if plot_path.exists():
            # Use relative path for report
            rel_path = plot_path.relative_to(Path(__file__).parent.parent.parent)
            lines.append(f"![{plot_path.stem}]({rel_path})")
        else:
            lines.append(f"*Plot file not found: {plot_file}*")
    
    return "\n\n".join(lines)

def generate_limitations() -> str:
    """Generate the limitations section with required text."""
    return (
        "### Limitations\n\n"
        "1. **Causality:** This study identifies correlational evidence, not causal relationships.\n"
        "2. **Measurement Proxy:** Motor Task Performance is a proxy for proprioceptive accuracy.\n"
        "3. **Sample Size:** The effective sample size after exclusions may limit statistical power for smaller effect sizes.\n"
        "4. **Generalizability:** Results are specific to the HCP/ADHD-200 population and may not generalize to other cohorts.\n"
        "5. **Motion Artifacts:** Despite rigorous motion correction, residual artifacts may influence connectivity estimates."
    )

def generate_conclusion(
    correlation_results: Optional[pd.DataFrame],
    power_results: Optional[Dict[str, Any]]
) -> str:
    """Generate the conclusion section with conditional phrasing based on results."""
    has_significant = False
    significant_count = 0
    total_count = 0
    
    if correlation_results is not None and not correlation_results.empty:
        if "significant" in correlation_results.columns:
            significant_count = int(correlation_results["significant"].sum())
            total_count = len(correlation_results)
            has_significant = significant_count > 0
    
    conclusion_parts = [
        "## Conclusion\n\n"
        "This study investigated the relationship between brain network dynamics and individual differences in sensorimotor performance.\n\n"
    ]
    
    if has_significant:
        conclusion_parts.append(
            f"Significant correlations were found in {significant_count} out of {total_count} tested metrics. "
            "These findings provide **correlational evidence** for an **associational relationship** "
            "between specific network metrics (e.g., Participation Coefficient, Within-Module Degree) and motor performance scores.\n\n"
        )
    else:
        conclusion_parts.append(
            f"No significant correlations survived FDR correction across the {total_count} tested metrics. "
            "While this suggests a lack of strong **associational relationship** in this dataset, "
            "it does not rule out the possibility of weaker effects or effects in specific sub-populations.\n\n"
        )
    
    if power_results and isinstance(power_results.get('detectable_r'), (int, float)):
        r_val = power_results['detectable_r']
        conclusion_parts.append(
            f"Based on the achieved sample size, the study had 80% power to detect effect sizes of |r| >= {r_val:.3f}. "
            "Effects smaller than this threshold may have been missed.\n\n"
        )
    
    conclusion_parts.append(
        "Future work should replicate these findings in independent cohorts and explore the causal mechanisms "
        "underlying the observed **associational relationship** between brain network topology and sensorimotor function."
    )
    
    return "".join(conclusion_parts)

def generate_report(
    correlation_results: Optional[pd.DataFrame] = None,
    power_results: Optional[Dict[str, Any]] = None,
    plot_files: Optional[List[str]] = None,
    output_path: Optional[Path] = None
) -> Path:
    """Assemble the full report and write to disk."""
    logger.log("generate_report", status="starting")
    
    # Load template
    template_content = load_template("report_template.md")
    
    # Prepare data
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Count subjects if available
    subjects_analyzed = "N/A"
    if correlation_results is not None and "subject_id" in correlation_results.columns:
        subjects_analyzed = len(correlation_results["subject_id"].unique())
    elif correlation_results is not None:
        subjects_analyzed = len(correlation_results)
    
    # Format sections
    corr_table_md = format_correlation_table(correlation_results)
    power_md = format_power_analysis(power_results)
    plots_md = format_plots(plot_files or [])
    limitations_md = generate_limitations()
    conclusion_md = generate_conclusion(correlation_results, power_results)
    
    # Substitute placeholders
    report_content = template_content
    report_content = report_content.replace("{{date}}", date_str)
    report_content = report_content.replace("{{subjects_analyzed}}", str(subjects_analyzed))
    report_content = report_content.replace("{{correlation_table}}", corr_table_md)
    report_content = report_content.replace("{{power_analysis}}", power_md)
    report_content = report_content.replace("{{plots}}", plots_md)
    report_content = report_content.replace("{{limitations}}", limitations_md)
    report_content = report_content.replace("{{conclusion}}", conclusion_md)
    
    # Determine output path
    if output_path is None:
        output_dir = Path(__file__).parent.parent.parent / "data" / "analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "final_report.md"
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.log("generate_report", status="completed", output=str(output_path))
    return output_path

def main() -> None:
    """Entry point for report generation."""
    logger.log("main", step="report_generation")
    
    # Load data from previous steps if available
    data_dir = Path(__file__).parent.parent.parent / "data" / "analysis"
    
    correlation_df = None
    corr_file = data_dir / "correlation_results.csv"
    if corr_file.exists():
        try:
            correlation_df = pd.read_csv(corr_file)
            logger.log("load_correlations", path=str(corr_file), rows=len(correlation_df))
        except Exception as e:
            logger.log("load_correlations_error", error=str(e))
    
    power_results = None
    power_file = data_dir / "power_analysis_results.json"
    if power_file.exists():
        try:
            import json
            with open(power_file, "r") as f:
                power_results = json.load(f)
            logger.log("load_power", path=str(power_file))
        except Exception as e:
            logger.log("load_power_error", error=str(e))
    
    # Collect plot files
    plot_files = []
    figures_dir = Path(__file__).parent.parent.parent / "figures"
    if figures_dir.exists():
        for ext in ["*.png", "*.pdf"]:
            plot_files.extend([str(p) for p in figures_dir.glob(ext)])
    
    # Generate report
    output_path = generate_report(
        correlation_results=correlation_df,
        power_results=power_results,
        plot_files=plot_files
    )
    
    print(f"Report generated successfully: {output_path}")
    logger.log("main", status="finished", output=str(output_path))

if __name__ == "__main__":
    main()