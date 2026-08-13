"""
Report Generation Script for llmXive Project.

This script generates a comprehensive Markdown report based on the analysis results.
It is invoked by the quickstart run-book to produce the final deliverable.

Usage:
    python code/viz/generate_report.py --input data/analysis/correlation_results.csv --output reports/summary.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Import from project modules
from code.logging_config import get_logger
from code.report.generate import (
    format_correlation_table,
    format_power_analysis,
    generate_limitations,
    generate_conclusion,
)

logger = get_logger(__name__)


def load_correlation_results(input_path: str) -> pd.DataFrame:
    """Load correlation results from CSV."""
    path = Path(input_path)
    if not path.exists():
        logger.log("error", message=f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    logger.log("info", message=f"Loaded {len(df)} correlation results from {input_path}")
    return df


def load_power_analysis(input_path: str) -> Optional[Dict[str, Any]]:
    """Load power analysis JSON if it exists."""
    path = Path(input_path)
    if not path.exists():
        logger.log("warning", message=f"Power analysis file not found: {input_path}. Skipping power analysis section.")
        return None
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        logger.log("info", message=f"Loaded power analysis from {input_path}")
        return data
    except Exception as e:
        logger.log("error", message=f"Failed to load power analysis: {e}")
        return None


def load_fdr_results(input_path: str) -> Optional[pd.DataFrame]:
    """Load FDR corrected results if available."""
    path = Path(input_path)
    if not path.exists():
        logger.log("warning", message=f"FDR results file not found: {input_path}. Using uncorrected results.")
        return None
    
    try:
        df = pd.read_csv(path)
        logger.log("info", message=f"Loaded FDR corrected results from {input_path}")
        return df
    except Exception as e:
        logger.log("error", message=f"Failed to load FDR results: {e}")
        return None


def generate_report(
    correlation_results: pd.DataFrame,
    power_analysis: Optional[Dict[str, Any]],
    fdr_results: Optional[pd.DataFrame],
    output_path: str,
) -> None:
    """Generate the final Markdown report."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Header
    report_lines = [
        "# Investigation of Brain Network Dynamics and Sensorimotor Performance",
        "",
        f"**Generated**: {timestamp}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "This report presents the findings from our investigation into the relationship between brain network dynamics and individual differences in sensorimotor performance. The analysis utilizes data from the Human Connectome Project (HCP) and applies graph-theoretical metrics to functional connectivity matrices derived from fMRI data.",
        "",
    ]
    
    # Methodology
    report_lines.extend([
        "## Methodology",
        "",
        "1. **Data Acquisition**: Functional MRI data was obtained from the Human Connectome Project (HCP) using ICA-FIX denoised data.",
        "2. **Parcellation**: The Schaefer high-resolution parcellation atlas (400 regions) was used to extract time-series.",
        "3. **Connectivity**: Pearson correlation matrices were computed for each subject.",
        "4. **Network Metrics**: Modularity, Participation Coefficient, Within-Module Degree, and Global Efficiency were calculated.",
        "5. **Statistical Analysis**: Spearman and Pearson correlations were performed with Framewise Displacement (FD) as a covariate.",
        "6. **Multiple Comparison Correction**: Benjamini-Hochberg False Discovery Rate (FDR) correction was applied.",
        "",
    ])
    
    # Results Section
    report_lines.extend([
        "## Results",
        "",
        "### Correlation Analysis",
        "",
    ])
    
    if correlation_results is not None and not correlation_results.empty:
        # Format correlation table
        table_md = format_correlation_table(correlation_results)
        report_lines.append(table_md)
        report_lines.append("")
        
        # Summary statistics
        significant = correlation_results[correlation_results['significant'] == True]
        report_lines.append(f"**Total tests performed**: {len(correlation_results)}")
        report_lines.append(f"**Significant correlations (p < 0.05)**: {len(significant)}")
        
        if fdr_results is not None and not fdr_results.empty:
            fdr_significant = fdr_results[fdr_results['significant'] == True]
            report_lines.append(f"**Significant after FDR correction (q < 0.05)**: {len(fdr_significant)}")
            report_lines.append("")
            report_lines.append("### FDR Corrected Results")
            report_lines.append("")
            fdr_md = format_correlation_table(fdr_results)
            report_lines.append(fdr_md)
            report_lines.append("")
    else:
        report_lines.append("*No correlation results available.*")
        report_lines.append("")
    
    # Power Analysis Section
    if power_analysis is not None:
        report_lines.extend([
            "## Power Analysis",
            "",
        ])
        power_md = format_power_analysis(power_analysis)
        report_lines.append(power_md)
        report_lines.append("")
    else:
        report_lines.extend([
            "## Power Analysis",
            "",
            "*Power analysis results were not available.*",
            "",
        ])
    
    # Limitations
    report_lines.extend([
        "## Limitations",
        "",
    ])
    limitations_md = generate_limitations()
    report_lines.append(limitations_md)
    report_lines.append("")
    
    # Conclusion
    report_lines.extend([
        "## Conclusion",
        "",
    ])
    conclusion_md = generate_conclusion(correlation_results)
    report_lines.append(conclusion_md)
    report_lines.append("")
    
    # Footer
    report_lines.extend([
        "---",
        "",
        f"*Report generated by llmXive automated science pipeline.*",
    ])
    
    # Write to file
    report_content = "\n".join(report_lines)
    with open(output_file, 'w') as f:
        f.write(report_content)
    
    logger.log("info", message=f"Report successfully generated: {output_path}")


def main() -> None:
    """Main entry point for the report generation script."""
    parser = argparse.ArgumentParser(
        description="Generate research report from analysis results."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the correlation results CSV file (e.g., data/analysis/correlation_results.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output Markdown report file (e.g., reports/summary.md)",
    )
    parser.add_argument(
        "--power-input",
        type=str,
        default="data/analysis/power_analysis.json",
        help="Path to the power analysis JSON file (default: data/analysis/power_analysis.json)",
    )
    parser.add_argument(
        "--fdr-input",
        type=str,
        default="data/analysis/fdr_corrected_results.csv",
        help="Path to the FDR corrected results CSV file (default: data/analysis/fdr_corrected_results.csv)",
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        correlation_results = load_correlation_results(args.input)
        power_analysis = load_power_analysis(args.power_input)
        fdr_results = load_fdr_results(args.fdr_input)
        
        # Generate report
        generate_report(correlation_results, power_analysis, fdr_results, args.output)
        
        logger.log("info", message="Report generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.log("error", message=str(e))
        sys.exit(1)
    except Exception as e:
        logger.log("error", message=f"Report generation failed: {e}")
        raise


if __name__ == "__main__":
    main()