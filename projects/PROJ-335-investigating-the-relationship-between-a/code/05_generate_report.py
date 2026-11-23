"""
T035: Generate final report summarizing findings, limitations, and associational nature.

This script reads the results from previous analysis steps (threshold results,
correlation analysis, reliability metrics) and generates a comprehensive Markdown
report at data/results/analysis_report.md.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_config import setup_logging, get_logger
from utils.validation import load_and_validate_csv

# Setup logging
logger = setup_logging(
    log_name="generate_report",
    log_file_path=Path("data/results/generate_report.log"),
    console_level=logging.INFO
)

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {file_path}: {e}")
        return None

def load_csv_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a CSV file into a dictionary representation."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        df = load_and_validate_csv(file_path, required_columns=None)
        if df is None or df.empty:
            logger.warning(f"Empty or invalid CSV file: {file_path}")
            return None
        # Convert to a simple dict representation for the report
        return {
            "columns": list(df.columns),
            "row_count": len(df),
            "sample_data": df.head(5).to_dict('records')
        }
    except Exception as e:
        logger.error(f"Failed to load CSV file {file_path}: {e}")
        return None

def format_correlation_results(results: Dict[str, Any]) -> str:
    """Format correlation analysis results for the report."""
    if not results:
        return "No correlation results available."

    lines = []
    lines.append("### Correlation Analysis Results")
    lines.append("")
    
    if "partial_correlations" in results:
        lines.append("#### Partial Correlations")
        lines.append("")
        lines.append("| Variable 1 | Variable 2 | Correlation (r) | p-value | FDR-corrected |")
        lines.append("|------------|------------|-----------------|---------|---------------|")
        for corr in results["partial_correlations"]:
            fdr_status = "Yes" if corr.get("fdr_corrected", False) else "No"
            lines.append(f"| {corr.get('var1', 'N/A')} | {corr.get('var2', 'N/A')} | {corr.get('r', 'N/A'):.3f} | {corr.get('p_value', 'N/A'):.4f} | {fdr_status} |")
        lines.append("")
    
    if "los_results" in results:
        lines.append("#### Leave-One-Subject-Out Cross-Validation")
        lines.append("")
        los = results["los_results"]
        lines.append(f"- **Mean Correlation**: {los.get('mean_r', 'N/A'):.3f}")
        lines.append(f"- **Std Deviation**: {los.get('std_r', 'N/A'):.3f}")
        lines.append(f"- **Range**: [{los.get('min_r', 'N/A'):.3f}, {los.get('max_r', 'N/A'):.3f}]")
        lines.append("")
    
    if "split_half" in results:
        lines.append("#### Split-Half Reliability")
        lines.append("")
        sh = results["split_half"]
        lines.append(f"- **Reliability Coefficient**: {sh.get('reliability', 'N/A'):.3f}")
        lines.append(f"- **Status**: {sh.get('status', 'N/A')}")
        lines.append("")

    return "\n".join(lines)

def generate_report(
    threshold_results_path: Path,
    correlation_results_path: Path,
    alpha_power_path: Path,
    plv_path: Path,
    output_path: Path
) -> None:
    """Generate the final analysis report."""
    logger.info(f"Starting report generation. Output: {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    threshold_results = load_json_safe(threshold_results_path)
    correlation_results = load_json_safe(correlation_results_path)
    alpha_power_data = load_csv_safe(alpha_power_path)
    plv_data = load_csv_safe(plv_path)
    
    # Build report content
    report_lines = []
    
    # Title and Introduction
    report_lines.append("# Analysis Report: Alpha Oscillations and Working Memory Capacity")
    report_lines.append("")
    report_lines.append("**Date**: " + Path(__file__).parent.parent.joinpath("data/results").stat().st_mtime if False else "Generated automatically by T035")
    report_lines.append("")
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This report summarizes the findings from the analysis of the relationship between alpha oscillations and working memory capacity using the OpenNeuro ds000248 dataset.")
    report_lines.append("")
    report_lines.append("### Key Findings")
    report_lines.append("")
    
    if threshold_results:
        status = threshold_results.get("threshold_status", "UNKNOWN")
        r_val = threshold_results.get("r_value", "N/A")
        rel_status = threshold_results.get("reliability_status", "UNKNOWN")
        rel_coeff = threshold_results.get("reliability_coeff", "N/A")
        
        report_lines.append(f"- **Primary Correlation Status**: {status}")
        report_lines.append(f"- **Correlation Coefficient (r)**: {r_val}")
        report_lines.append(f"- **Reliability Status**: {rel_status}")
        report_lines.append(f"- **Reliability Coefficient**: {rel_coeff}")
    else:
        report_lines.append("- *No threshold results available*")
    
    report_lines.append("")
    
    # Methodology
    report_lines.append("## Methodology")
    report_lines.append("")
    report_lines.append("### Data Source")
    report_lines.append("")
    report_lines.append("- **Dataset**: OpenNeuro ds000248 (Visual Working Memory Task)")
    report_lines.append("- **Preprocessing**: Bandpass filtering (1-40 Hz), ICA artifact removal, average mastoid re-referencing")
    report_lines.append("- **Epoching**: Aligned to task events during delay periods")
    report_lines.append("")
    
    report_lines.append("### Metrics Extracted")
    report_lines.append("")
    report_lines.append("1. **Alpha Power**: Computed from frontal (F3, F4, Fz) and parietal (P3, P4, Pz) electrodes")
    report_lines.append("2. **Phase-Locking Value (PLV)**: Calculated between frontal-parietal electrode pairs using Hilbert transform")
    report_lines.append("3. **Working Memory Capacity**: k-scores and d' derived from behavioral performance")
    report_lines.append("")
    
    report_lines.append("### Statistical Analysis")
    report_lines.append("")
    report_lines.append("- **Partial Correlation**: To control for confounding variables")
    report_lines.append("- **FDR Correction**: Benjamini-Hochberg procedure for multiple comparisons")
    report_lines.append("- **LOSO Cross-Validation**: Leave-one-subject-out validation")
    report_lines.append("- **Split-Half Reliability**: Internal consistency check")
    report_lines.append("")
    
    # Results
    report_lines.append("## Results")
    report_lines.append("")
    
    if correlation_results:
        report_lines.append(format_correlation_results(correlation_results))
    else:
        report_lines.append("### Correlation Analysis")
        report_lines.append("")
        report_lines.append("No correlation results available.")
        report_lines.append("")
    
    # Data Overview
    report_lines.append("### Data Overview")
    report_lines.append("")
    
    if alpha_power_data:
        report_lines.append("#### Alpha Power Metrics")
        report_lines.append("")
        report_lines.append(f"- **Total Records**: {alpha_power_data['row_count']}")
        report_lines.append(f"- **Columns**: {', '.join(alpha_power_data['columns'])}")
        report_lines.append("")
    else:
        report_lines.append("#### Alpha Power Metrics")
        report_lines.append("")
        report_lines.append("- *No data available*")
        report_lines.append("")
    
    if plv_data:
        report_lines.append("#### PLV Metrics")
        report_lines.append("")
        report_lines.append(f"- **Total Records**: {plv_data['row_count']}")
        report_lines.append(f"- **Columns**: {', '.join(plv_data['columns'])}")
        report_lines.append("")
    else:
        report_lines.append("#### PLV Metrics")
        report_lines.append("")
        report_lines.append("- *No data available*")
        report_lines.append("")
    
    # Limitations
    report_lines.append("## Limitations")
    report_lines.append("")
    report_lines.append("1. **Sample Size**: The analysis is constrained by the available participant count in the ds000248 dataset. Power analysis was conducted to assess adequacy.")
    report_lines.append("")
    report_lines.append("2. **Associational Nature**: This study identifies correlations between alpha oscillations and working memory capacity but does not establish causality. Experimental manipulation would be required to infer causal relationships.")
    report_lines.append("")
    report_lines.append("3. **Generalizability**: Results are specific to the visual working memory task paradigm used in ds000248. Different task demands or modalities may yield different patterns.")
    report_lines.append("")
    report_lines.append("4. **EEG Spatial Resolution**: EEG provides limited spatial resolution compared to intracranial recordings. Source localization was not performed in this analysis.")
    report_lines.append("")
    report_lines.append("5. **Artifact Removal**: While ICA was used to remove artifacts, some residual noise may remain, potentially affecting metric accuracy.")
    report_lines.append("")
    
    # Conclusions
    report_lines.append("## Conclusions")
    report_lines.append("")
    report_lines.append("This analysis provides an evidence-based assessment of the relationship between alpha-band oscillations and working memory capacity. The findings should be interpreted within the context of the limitations described above.")
    report_lines.append("")
    
    if threshold_results:
        if threshold_results.get("threshold_status") == "PASS":
            report_lines.append("The correlation between alpha oscillations and working memory capacity met the predefined threshold (|r| ≥ 0.3), suggesting a meaningful relationship.")
        else:
            report_lines.append("The correlation between alpha oscillations and working memory capacity did not meet the predefined threshold (|r| ≥ 0.3), indicating a weaker or non-significant relationship in this dataset.")
    else:
        report_lines.append("Threshold analysis could not be completed due to missing results.")
    
    report_lines.append("")
    report_lines.append("## References")
    report_lines.append("")
    report_lines.append("- OpenNeuro Dataset ds000248: Visual Working Memory Task")
    report_lines.append("- MNE-Python for EEG preprocessing and analysis")
    report_lines.append("- Benjamini-Hochberg procedure for FDR correction")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*Report generated automatically by the llmXive pipeline (Task T035)*")
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    
    logger.info(f"Report successfully generated: {output_path}")

def main():
    """Main entry point for report generation."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    data_results_dir = project_root / "data" / "results"
    data_metrics_dir = project_root / "data" / "metrics"
    
    threshold_results_path = data_results_dir / "threshold_results.json"
    correlation_results_path = data_results_dir / "correlation_results.json"
    alpha_power_path = data_metrics_dir / "alpha_power.csv"
    plv_path = data_metrics_dir / "plv.csv"
    output_path = data_results_dir / "analysis_report.md"
    
    try:
        generate_report(
            threshold_results_path=threshold_results_path,
            correlation_results_path=correlation_results_path,
            alpha_power_path=alpha_power_path,
            plv_path=plv_path,
            output_path=output_path
        )
        print(f"Report generated successfully: {output_path}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()