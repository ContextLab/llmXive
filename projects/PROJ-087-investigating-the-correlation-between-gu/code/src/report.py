"""
Report generation module for the Gut Microbiome and Sleep Quality study.

This module compiles the final research report, including:
- Loading correlation results and ingestion reports
- Compiling a summary table of correlations
- Generating a text-based report
- Saving the report to disk
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import load_config

# Configure logger
logger = logging.getLogger(__name__)


def load_correlation_results(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the correlation results from the processed CSV file.

    Args:
        config: Configuration dictionary containing file paths.

    Returns:
        DataFrame containing correlation results.

    Raises:
        FileNotFoundError: If the correlation results file does not exist.
        ValueError: If the file is empty or malformed.
    """
    file_path = Path(config['DATA_PROCESSED']) / 'correlation_results.csv'

    if not file_path.exists():
        raise FileNotFoundError(f"Correlation results file not found at: {file_path}")

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            logger.warning("Correlation results file is empty.")
            return df
        logger.info(f"Loaded {len(df)} correlation results from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading correlation results: {e}")
        raise


def load_ingestion_report(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load the ingestion report JSON file.

    Args:
        config: Configuration dictionary containing file paths.

    Returns:
        Dictionary containing ingestion statistics.

    Raises:
        FileNotFoundError: If the ingestion report file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    file_path = Path(config['DATA_PROCESSED']) / 'ingestion_report.json'

    if not file_path.exists():
        raise FileNotFoundError(f"Ingestion report file not found at: {file_path}")

    try:
        with open(file_path, 'r') as f:
            report = json.load(f)
        logger.info(f"Loaded ingestion report from {file_path}")
        return report
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in ingestion report: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading ingestion report: {e}")
        raise


def compile_summary_table(correlation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compile a summary table of correlations for the report.

    This function filters for meaningful correlations (q-value < 0.05 AND |r| > 0.3)
    and selects key columns for the summary table.

    Args:
        correlation_df: DataFrame containing all correlation results.

    Returns:
        DataFrame containing the summary table of meaningful correlations.
    """
    if correlation_df.empty:
        logger.warning("Correlation DataFrame is empty. Returning empty summary table.")
        return pd.DataFrame()

    # Filter for meaningful correlations
    summary = correlation_df[
        (correlation_df['is_meaningful'] == True) |
        (correlation_df['is_moderate'] == True)
    ].copy()

    # Select and order columns for the report
    columns_to_keep = [
        'variable_x', 'variable_y', 'correlation_coefficient',
        'p_value', 'q_value', 'is_moderate', 'is_meaningful'
    ]

    # Ensure all columns exist before selecting
    available_columns = [col for col in columns_to_keep if col in summary.columns]
    summary = summary[available_columns]

    # Sort by absolute correlation coefficient descending
    if 'correlation_coefficient' in summary.columns:
        summary = summary.sort_values(
            by='correlation_coefficient',
            key=abs,
            ascending=False
        )

    logger.info(f"Compiled summary table with {len(summary)} rows")
    return summary


def generate_report_text(
    summary_table: pd.DataFrame,
    ingestion_report: Dict[str, Any],
    config: Dict[str, Any]
) -> str:
    """
    Generate a text-based research report.

    Args:
        summary_table: DataFrame containing the summary of correlations.
        ingestion_report: Dictionary containing ingestion statistics.
        config: Configuration dictionary.

    Returns:
        Formatted string containing the research report.
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("GUT MICROBIOME COMPOSITION AND SLEEP QUALITY: FINAL REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Section 1: Data Ingestion Summary
    report_lines.append("1. DATA INGESTION SUMMARY")
    report_lines.append("-" * 40)
    total_samples = ingestion_report.get('total_initial_sample_count', 'N/A')
    excluded_samples = ingestion_report.get('excluded_count', 'N/A')
    exclusion_proportion = ingestion_report.get('exclusion_proportion', 'N/A')

    report_lines.append(f"   Total initial samples: {total_samples}")
    report_lines.append(f"   Excluded samples: {excluded_samples}")
    report_lines.append(f"   Exclusion proportion: {exclusion_proportion:.2%}" if isinstance(exclusion_proportion, (int, float)) else f"   Exclusion proportion: {exclusion_proportion}")
    report_lines.append("")

    # Section 2: Correlation Analysis Results
    report_lines.append("2. CORRELATION ANALYSIS RESULTS")
    report_lines.append("-" * 40)

    if summary_table.empty:
        report_lines.append("   No significant or moderate correlations were found.")
        report_lines.append("   All tested pairs failed to meet the criteria:")
        report_lines.append("   - |r| > 0.3 (moderate correlation)")
        report_lines.append("   - q-value < 0.05 (significant after FDR correction)")
    else:
        meaningful_count = summary_table['is_meaningful'].sum()
        moderate_count = summary_table['is_moderate'].sum()

        report_lines.append(f"   Total correlations analyzed: {len(summary_table)}")
        report_lines.append(f"   Meaningful correlations (q < 0.05 AND |r| > 0.3): {meaningful_count}")
        report_lines.append(f"   Moderate correlations (|r| > 0.3): {moderate_count}")
        report_lines.append("")

        report_lines.append("   Summary Table:")
        report_lines.append("   " + "-" * 70)
        report_lines.append(f"   {'Variable X':<25} {'Variable Y':<25} {'r':>8} {'q-value':>10}")
        report_lines.append("   " + "-" * 70)

        for _, row in summary_table.iterrows():
            var_x = str(row.get('variable_x', 'N/A'))[:25]
            var_y = str(row.get('variable_y', 'N/A'))[:25]
            r_val = f"{row.get('correlation_coefficient', 0):.4f}"
            q_val = f"{row.get('q_value', 0):.4f}"
            sig_marker = " *" if row.get('is_meaningful', False) else ""
            report_lines.append(f"   {var_x:<25} {var_y:<25} {r_val:>8} {q_val:>10}{sig_marker}")

        report_lines.append("   " + "-" * 70)
        report_lines.append("   * Indicates meaningful correlation (q < 0.05 AND |r| > 0.3)")

    report_lines.append("")
    report_lines.append("3. METHODOLOGY NOTES")
    report_lines.append("-" * 40)
    report_lines.append("   - Correlation method: Spearman rank correlation")
    report_lines.append("   - Multiple testing correction: Benjamini-Hochberg FDR")
    report_lines.append("   - Significance threshold: q-value < 0.05")
    report_lines.append("   - Moderate correlation threshold: |r| > 0.3")
    report_lines.append("   - Data filtering: Excluded samples with antibiotic use")
    report_lines.append("     in last 3 months and missing sleep metrics.")
    report_lines.append("")
    report_lines.append("4. GENERATED FILES")
    report_lines.append("-" * 40)
    report_lines.append(f"   - Correlation results: {config['DATA_PROCESSED']}/correlation_results.csv")
    report_lines.append(f"   - Ingestion report: {config['DATA_PROCESSED']}/ingestion_report.json")
    report_lines.append(f"   - Plot artifacts: {config['DATA_PROCESSED']}/plots/")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)


def save_report(report_text: str, config: Dict[str, Any]) -> Path:
    """
    Save the generated report to a text file.

    Args:
        report_text: The formatted report string.
        config: Configuration dictionary containing file paths.

    Returns:
        Path to the saved report file.
    """
    output_path = Path(config['DATA_PROCESSED']) / 'final_report.txt'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    logger.info(f"Report saved to: {output_path}")
    return output_path


def run_report_generation(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Main function to run the complete report generation pipeline.

    This function orchestrates:
    1. Loading configuration
    2. Loading correlation results
    3. Loading ingestion report
    4. Compiling summary table
    5. Generating report text
    6. Saving the report

    Args:
        config: Optional configuration dictionary. If None, loads from environment.

    Returns:
        Path to the generated report file.
    """
    if config is None:
        config = load_config()

    logger.info("Starting report generation pipeline...")

    # Load data
    correlation_df = load_correlation_results(config)
    ingestion_report = load_ingestion_report(config)

    # Compile summary
    summary_table = compile_summary_table(correlation_df)

    # Generate report
    report_text = generate_report_text(summary_table, ingestion_report, config)

    # Save report
    report_path = save_report(report_text, config)

    logger.info("Report generation pipeline completed successfully.")
    return str(report_path)


def main():
    """Entry point for running the report generation as a script."""
    import sys
    from src.logging_config import setup_logger

    # Setup logging
    logger = setup_logger("report", level="INFO")

    try:
        report_path = run_report_generation()
        print(f"Report successfully generated at: {report_path}")
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()