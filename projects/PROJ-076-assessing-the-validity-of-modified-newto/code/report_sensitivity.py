import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# Import from project API surface
from utils import get_logger, ensure_directory, get_timestamp
from sensitivity import load_fit_summary, compute_pass_rates

def load_sensitivity_data(summary_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load sensitivity analysis data from the results directory.
    Defaults to results/sensitivity_data.csv if no path provided.
    """
    if summary_path is None:
        summary_path = "results/sensitivity_data.csv"
    
    path = Path(summary_path)
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity data file not found: {summary_path}")
    
    logger = get_logger()
    logger.info(f"Loading sensitivity data from {summary_path}")
    
    df = pd.read_csv(summary_path)
    return df

def generate_report(
    sensitivity_df: pd.DataFrame,
    output_path: str = "results/sensitivity_report.md",
    thresholds: Optional[List[float]] = None
) -> None:
    """
    Generate a markdown report with visualizations (ASCII/tables) comparing
    pass rates for thresholds across a range of values.
    
    Args:
        sensitivity_df: DataFrame from sensitivity analysis with columns
                        including 'threshold', 'mond_pass_rate', 'nfw_pass_rate'
        output_path: Path to write the markdown report
        thresholds: Optional list of specific thresholds to highlight in summary
    """
    logger = get_logger()
    ensure_directory(output_path)
    
    # Default thresholds if not provided
    if thresholds is None:
        thresholds = [1.0, 1.25, 1.5, 1.75]
    
    logger.info(f"Generating sensitivity report to {output_path}")
    
    # Ensure required columns exist
    required_cols = ['threshold', 'mond_pass_rate', 'nfw_pass_rate']
    missing_cols = [c for c in required_cols if c not in sensitivity_df.columns]
    if missing_cols:
        raise ValueError(f"Sensitivity data missing required columns: {missing_cols}")
    
    # Sort by threshold
    sensitivity_df = sensitivity_df.sort_values('threshold').reset_index(drop=True)
    
    # Extract key statistics
    total_rows = len(sensitivity_df)
    min_threshold = sensitivity_df['threshold'].min()
    max_threshold = sensitivity_df['threshold'].max()
    
    # Calculate best performing model at each threshold
    sensitivity_df['better_model'] = sensitivity_df.apply(
        lambda row: 'MOND' if row['mond_pass_rate'] > row['nfw_pass_rate'] 
                    else 'NFW' if row['nfw_pass_rate'] > row['mond_pass_rate'] 
                    else 'Tie', axis=1
    )
    
    # Count wins
    mond_wins = (sensitivity_df['better_model'] == 'MOND').sum()
    nfw_wins = (sensitivity_df['better_model'] == 'NFW').sum()
    ties = (sensitivity_df['better_model'] == 'Tie').sum()
    
    # Build report content
    timestamp = get_timestamp()
    
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        f"**Generated**: {timestamp}",
        "",
        "## Executive Summary",
        "",
        "This report presents the sensitivity analysis of goodness-of-fit metrics",
        "for Modified Newtonian Dynamics (MOND) and NFW dark matter halo models",
        "across a range of chi-squared thresholds. The analysis evaluates the",
        "robustness of model comparisons under varying acceptance criteria.",
        "",
        "### Key Findings",
        "",
        f"- **Threshold Range Analyzed**: {min_threshold:.2f} to {max_threshold:.2f}",
        f"- **Total Threshold Points**: {total_rows}",
        f"- **MOND Dominance**: {mond_wins} thresholds where MOND outperforms NFW",
        f"- **NFW Dominance**: {nfw_wins} thresholds where NFW outperforms MOND",
        f"- **Ties**: {ties} thresholds with equal performance",
        "",
        "## Methodology",
        "",
        "The sensitivity analysis sweeps chi-squared thresholds across representative",
        "values to determine the pass rate for each model. A model 'passes' at a",
        "given threshold if its reduced chi-squared value is below that threshold.",
        "",
        "### Threshold Values",
        "",
        "The analysis includes the following critical thresholds:",
        "",
    ]
    
    # Add threshold table
    report_lines.append("| Threshold | MOND Pass Rate | NFW Pass Rate | Better Model |")
    report_lines.append("|-----------|----------------|---------------|--------------|")
    
    for _, row in sensitivity_df.iterrows():
        report_lines.append(
            f"| {row['threshold']:.2f} | {row['mond_pass_rate']*100:.1f}% | "
            f"{row['nfw_pass_rate']*100:.1f}% | {row['better_model']} |"
        )
    
    report_lines.extend([
        "",
        "## Visualizations",
        "",
        "### Pass Rate Comparison",
        "",
        "The following ASCII chart visualizes the pass rates for both models",
        "across the threshold range:",
        "",
    ])
    
    # Generate ASCII chart
    max_bar_len = 50
    chart_lines = []
    chart_lines.append("Threshold | MOND Pass Rate                          | NFW Pass Rate")
    chart_lines.append("----------+------------------------------------------+------------------------------------------")
    
    for _, row in sensitivity_df.iterrows():
        mond_bar_len = int(row['mond_pass_rate'] * max_bar_len)
        nfw_bar_len = int(row['nfw_pass_rate'] * max_bar_len)
        
        mond_bar = '█' * mond_bar_len + '░' * (max_bar_len - mond_bar_len)
        nfw_bar = '█' * nfw_bar_len + '░' * (max_bar_len - nfw_bar_len)
        
        chart_lines.append(
            f"{row['threshold']:>8.2f} | {mond_bar} | {nfw_bar}"
        )
    
    report_lines.extend(chart_lines)
    report_lines.extend([
        "",
        "## Threshold-Specific Analysis",
        "",
    ])
    
    # Analyze specific thresholds
    for thresh in thresholds:
        # Find closest threshold in data
        closest = sensitivity_df.loc[(sensitivity_df['threshold'] - thresh).abs().idxmin()]
        
        report_lines.extend([
            f"### Threshold = {thresh:.2f}",
            "",
            f"- **MOND Pass Rate**: {closest['mond_pass_rate']*100:.1f}%",
            f"- **NFW Pass Rate**: {closest['nfw_pass_rate']*100:.1f}%",
        ])
        
        diff = closest['mond_pass_rate'] - closest['nfw_pass_rate']
        if abs(diff) < 0.01:
            report_lines.append("- **Conclusion**: Models perform equivalently at this threshold.")
        elif diff > 0:
            report_lines.append(f"- **Conclusion**: MOND outperforms NFW by {diff*100:.1f} percentage points.")
        else:
            report_lines.append(f"- **Conclusion**: NFW outperforms MOND by {abs(diff)*100:.1f} percentage points.")
        
        report_lines.append("")
    
    report_lines.extend([
        "## Statistical Robustness",
        "",
        "The consistency of model performance across thresholds indicates the",
        "robustness of the conclusion. A model that consistently outperforms",
        "across a wide range of thresholds demonstrates greater reliability",
        "than one whose performance varies significantly with threshold choice.",
        "",
        "### Performance Variance",
        "",
        f"- **MOND Pass Rate Std Dev**: {sensitivity_df['mond_pass_rate'].std()*100:.1f}%",
        f"- **NFW Pass Rate Std Dev**: {sensitivity_df['nfw_pass_rate'].std()*100:.1f}%",
        "",
        "## Recommendations",
        "",
        "Based on this sensitivity analysis:",
        "",
    ])
    
    # Generate recommendation
    if mond_wins > nfw_wins + 2:
        report_lines.append("1. **MOND shows superior performance** across the tested thresholds.")
        report_lines.append("2. The MOND model demonstrates more consistent goodness-of-fit.")
        report_lines.append("3. Further investigation into MOND's physical interpretation is warranted.")
    elif nfw_wins > mond_wins + 2:
        report_lines.append("1. **NFW shows superior performance** across the tested thresholds.")
        report_lines.append("2. The NFW dark matter halo model demonstrates more consistent goodness-of-fit.")
        report_lines.append("3. Standard cold dark matter paradigm remains robust for this dataset.")
    else:
        report_lines.append("1. **Model performance is comparable** across thresholds.")
        report_lines.append("2. Neither model consistently outperforms the other.")
        report_lines.append("3. Consider additional metrics (residual analysis, block-bootstrap) for final verdict.")
    
    report_lines.extend([
        "",
        "## Appendix: Data Source",
        "",
        "This report was generated from the sensitivity analysis data produced",
        "by the `sensitivity.py` module. The underlying fit results are derived",
        "from the SPARC galaxy rotation curve dataset.",
        "",
        "---",
        "",
        f"*Report generated at {timestamp}*",
    ])
    
    # Write report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Sensitivity report successfully written to {output_path}")

def main():
    """Main entry point for sensitivity report generation."""
    logger = setup_logging()
    logger.info("Starting sensitivity report generation")
    
    try:
        # Load sensitivity data
        sensitivity_df = load_sensitivity_data("results/sensitivity_data.csv")
        
        # Generate report
        generate_report(
            sensitivity_df=sensitivity_df,
            output_path="results/sensitivity_report.md",
            thresholds=[1.0, 1.25, 1.5, 1.75]
        )
        
        logger.info("Sensitivity report generation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()
