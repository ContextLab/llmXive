"""
Report generation module for the network structure superconducting qubit coupling study.

This module aggregates results from correlation analysis, robustness checks, and power analysis
to generate a comprehensive Markdown report documenting the findings.
"""

import os
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORT_PATH = DOCS_DIR / "report.md"

# Ensure docs directory exists
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def load_correlation_results() -> Optional[pd.DataFrame]:
    """
    Load correlation results from the processed CSV file.

    Returns:
        DataFrame with correlation results or None if file not found.
    """
    file_path = DATA_PROCESSED_DIR / "correlation_results.csv"
    if not file_path.exists():
        logger.error(f"Correlation results file not found: {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} correlation results from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading correlation results: {e}")
        return None


def load_robustness_lodo() -> Optional[pd.DataFrame]:
    """
    Load Leave-One-Device-Out (LODO) robustness check results.

    Note: If the robustness results are stored in a separate file, adjust the path accordingly.
    For now, we assume the LODO results might be embedded in the correlation results or a separate file.
    If not available, return None.
    """
    # Attempt to load LODO results if they exist in a separate file
    file_path = DATA_PROCESSED_DIR / "robustness_lodo.csv"
    if file_path.exists():
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded LODO robustness results: {len(df)} rows")
            return df
        except Exception as e:
            logger.warning(f"Could not load LODO results from {file_path}: {e}")
    
    # If no separate file, check if LODO info is in correlation results
    corr_df = load_correlation_results()
    if corr_df is not None and 'is_lodo_stable' in corr_df.columns:
        logger.info("LODO stability info found in correlation results")
        return corr_df[['metric_a', 'metric_b', 'is_lodo_stable']]
    
    logger.warning("No LODO robustness results found.")
    return None


def load_power_analysis() -> Optional[pd.DataFrame]:
    """
    Load power analysis results.

    Note: Similar to LODO, power analysis results might be in a separate file or embedded.
    """
    file_path = DATA_PROCESSED_DIR / "power_analysis.csv"
    if file_path.exists():
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded power analysis results: {len(df)} rows")
            return df
        except Exception as e:
            logger.warning(f"Could not load power analysis from {file_path}: {e}")
    
    logger.warning("No power analysis results found.")
    return None


def generate_methodology_section() -> str:
    """
    Generate the Methodology section of the report.

    This section describes the data sources, processing steps, and statistical methods used.
    """
    return """
## Methodology

This study explores the role of network structure in superconducting qubit coupling by analyzing calibration data from IBM Quantum backends. The methodology follows a cross-sectional approach, ensuring that topology and performance metrics are extracted from the same calibration snapshot (simultaneous data).

### Data Sources
- **IBM Quantum Backends**: Calibration properties were fetched for all publicly accessible backends.
- **Data Freshness**: Only data ≤ 30 days old was included to ensure relevance.

### Processing Steps
1. **Topology Extraction**: Coupling maps were extracted and converted to undirected graphs.
2. **Graph Metrics**: Topological descriptors (e.g., average shortest-path length, clustering coefficient, spectral gap) were computed.
3. **Performance Metrics**: Key performance indicators (T1, T2, CX error, readout error) were aggregated per device.
4. **Correlation Analysis**: Spearman rank-correlation tests were performed between graph metrics and performance indicators.
5. **Multiple Testing Correction**: Benjamini-Hochberg FDR correction was applied to control false discovery rate.

### Statistical Methods
- **Spearman Correlation**: Used to assess monotonic relationships between non-normally distributed variables.
- **Benjamini-Hochberg FDR**: Adjusted p-values to account for multiple hypothesis testing.
- **Leave-One-Device-Out (LODO)**: Robustness check to verify stability of significant correlations.

*Note: Historical time window logic is disabled per Plan.md Spec Gap and FR-003 resolution. Topology and performance metrics are extracted from the same calibration snapshot.*
"""


def generate_correlation_results_section(df: pd.DataFrame) -> str:
    """
    Generate the Correlation Results section of the report.

    Args:
        df: DataFrame containing correlation results.

    Returns:
        Markdown string summarizing the correlation results.
    """
    if df is None or df.empty:
        return "## Correlation Results\n\nNo correlation results available."

    significant = df[df['is_significant'] == True]
    excluded = df[df['is_excluded'] == True]

    section = "## Correlation Results\n\n"
    section += f"Total correlations tested: {len(df)}\n"
    section += f"Significant correlations (adj p < 0.05): {len(significant)}\n"
    section += f"Excluded correlations: {len(excluded)}\n\n"

    if not significant.empty:
        section += "### Significant Correlations\n\n"
        section += "| Metric A | Metric B | Spearman's ρ | p-value | Adj p-value |\n"
        section += "|----------|----------|--------------|---------|-------------|\n"
        for _, row in significant.iterrows():
            section += f"| {row['metric_a']} | {row['metric_b']} | {row['spearman_rho']:.3f} | {row['p_value']:.4f} | {row['adj_p_value']:.4f} |\n"
        section += "\n"
    else:
        section += "No significant correlations were found after FDR correction.\n\n"

    if not excluded.empty:
        section += "### Excluded Correlations\n\n"
        section += "The following correlations were excluded due to insufficient data or other criteria:\n\n"
        section += "| Metric A | Metric B | Reason |\n"
        section += "|----------|----------|--------|\n"
        for _, row in excluded.iterrows():
            reason = row.get('exclusion_reason', 'Unknown')
            section += f"| {row['metric_a']} | {row['metric_b']} | {reason} |\n"
        section += "\n"
    else:
        section += "No correlations were excluded.\n\n"

    return section


def generate_robustness_section(lodo_df: Optional[pd.DataFrame]) -> str:
    """
    Generate the Robustness Checks section of the report.

    Args:
        lodo_df: DataFrame containing LODO robustness check results.

    Returns:
        Markdown string summarizing robustness checks.
    """
    section = "## Robustness Checks\n\n"

    # LODO Analysis
    section += "### Leave-One-Device-Out (LODO) Analysis\n\n"
    if lodo_df is not None and not lodo_df.empty:
        stable_count = lodo_df[lodo_df['is_lodo_stable'] == True].shape[0] if 'is_lodo_stable' in lodo_df.columns else 0
        total_count = len(lodo_df)
        section += f"Of {total_count} correlations tested, {stable_count} remained stable (|Δρ| ≤ 0.1) across all leave-one-device-out subsets.\n\n"
    else:
        section += "LODO analysis could not be performed due to missing data.\n\n"

    # Time Window Limitation
    section += "### Time Window Limitation\n\n"
    section += "FR-004 Time Window check could not be performed as the IBM Quantum API does not expose historical performance states for past dates. Correlation stability is assessed via LODO (T031a) and cross-sectional variance only.\n\n"

    return section


def generate_power_analysis_section(power_df: Optional[pd.DataFrame]) -> str:
    """
    Generate the Power Analysis section of the report.

    Args:
        power_df: DataFrame containing power analysis results.

    Returns:
        Markdown string summarizing power analysis.
    """
    section = "## Power Analysis\n\n"

    if power_df is not None and not power_df.empty:
        section += "### Minimum Detectable Effect Size (MDES)\n\n"
        section += "| Sample Size (N) | Power | Alpha | MDES (ρ) | 95% CI |\n"
        section += "|-----------------|-------|-------|----------|--------|\n"
        for _, row in power_df.iterrows():
            ci = f"({row.get('ci_lower', 0):.3f}, {row.get('ci_upper', 0):.3f})"
            section += f"| {row['sample_size']} | {row['power']} | {row['alpha']} | {row['mdes']:.3f} | {ci} |\n"
        section += "\n"
    else:
        section += "Power analysis could not be performed due to missing data.\n\n"
    
    section += "### Interpretation\n\n"
    section += "The MDES indicates the smallest correlation coefficient that can be detected with 80% power at α=0.05 given the current sample size. A larger MDES suggests limited statistical power to detect small effects.\n\n"

    return section


def generate_report() -> bool:
    """
    Generate the full report and save it to docs/report.md.

    Returns:
        True if report was generated successfully, False otherwise.
    """
    logger.info("Starting report generation...")

    # Load data
    corr_df = load_correlation_results()
    lodo_df = load_robustness_lodo()
    power_df = load_power_analysis()

    # Generate sections
    methodology = generate_methodology_section()
    results = generate_correlation_results_section(corr_df)
    robustness = generate_robustness_section(lodo_df)
    power = generate_power_analysis_section(power_df)

    # Assemble report
    report = f"""# Network Structure in Superconducting Qubit Coupling: Analysis Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{methodology}
{results}
{robustness}
{power}
"""

    # Save report
    try:
        with open(REPORT_PATH, 'w') as f:
            f.write(report)
        logger.info(f"Report successfully generated: {REPORT_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return False


def main():
    """
    Main entry point for report generation.
    """
    success = generate_report()
    if success:
        print(f"Report generated at: {REPORT_PATH}")
    else:
        print("Report generation failed. Check logs for details.")
        exit(1)


if __name__ == "__main__":
    main()