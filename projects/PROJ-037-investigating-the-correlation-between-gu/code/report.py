"""
report.py
Generate final research report.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import get_logger

logger = get_logger(__name__)

DATA_OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"

def load_correlation_results(path: Path = None) -> pd.DataFrame:
    if path is None:
        path = DATA_OUTPUTS_DIR / "correlation_results.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def load_validation_status(path: Path = None) -> Dict[str, Any]:
    if path is None:
        path = DATA_OUTPUTS_DIR / "validation_status.json"
    if not path.exists():
        return {}
    import json
    with open(path, 'r') as f:
        return json.load(f)

def load_sensitivity_report(path: Path = None) -> pd.DataFrame:
    if path is None:
        path = DATA_OUTPUTS_DIR / "sensitivity_report.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def load_bootstrap_results(validation_status: Dict[str, Any]) -> List[Dict]:
    return validation_status.get('top_correlations', [])

def generate_report_section_bootstrap_stability(bootstrap_results: List[Dict]) -> str:
    """Generate report section on bootstrap stability."""
    section = "\n--- Bootstrap Stability Analysis ---\n"
    if not bootstrap_results:
        section += "Bootstrap resampling was skipped due to insufficient sample size.\n"
        return section
    
    for corr in bootstrap_results:
        ci_str = f"[{corr['ci_lower']:.3f}, {corr['ci_upper']:.3f}]"
        zero_note = " (includes zero: valid negative result)" if corr['includes_zero'] else ""
        section += f"{corr['sleep_variable']} vs {corr['diversity_variable']}: r={corr['effect_size']:.3f}, 95% CI {ci_str}{zero_note}\n"
    
    section += "\nNote: Confidence intervals including zero are treated as valid negative results (methodological correction per SC-002).\n"
    return section

def generate_report_section_sensitivity(sensitivity_df: pd.DataFrame) -> str:
    """Generate report section on sensitivity analysis."""
    section = "\n--- Sensitivity Analysis ---\n"
    if sensitivity_df.empty:
        section += "No sensitivity analysis performed.\n"
        return section
    
    section += "Variation in significant taxa counts across thresholds:\n"
    for _, row in sensitivity_df.iterrows():
        section += f"  Threshold {row['threshold']}: {row['significant_taxa_count']} significant associations\n"
    return section

def generate_full_report(correlation_df: pd.DataFrame, validation_status: Dict[str, Any], sensitivity_df: pd.DataFrame) -> str:
    """Generate the full research report."""
    report = "# Research Report: Gut Microbiome and Circadian Rhythm\n\n"
    
    report += "## Methodological Notes\n"
    report += "All findings are explicitly framed as **associational**. No causal claims are made.\n\n"
    
    report += "## Limitations\n"
    report += "1. **Diet Timing**: 'diet timing' variable unavailable in AGP; 'diet type' used as substitute (per plan mitigation).\n"
    
    if correlation_df.empty:
        report += "2. **Sample Size**: Insufficient data for robust analysis.\n"
    else:
        n = len(correlation_df)
        if n < 200:
            report += f"2. **Power Limitation**: Sample size N={n} < 200 reduces ability to detect small effect sizes.\n"
    
    report += "\n## Results\n"
    if not correlation_df.empty:
        significant = correlation_df[correlation_df['fdr_p'] < 0.05]
        report += f"Found {len(significant)} significant associations (FDR < 0.05).\n\n"
        report += "Top associations:\n"
        for _, row in correlation_df.head(5).iterrows():
            report += f"- {row['sleep_variable']} vs {row['diversity_variable']}: r={row['spearman_r']:.3f}, p(FDR)={row['fdr_p']:.3f}\n"
    else:
        report += "No significant associations found.\n"
    
    report += generate_report_section_bootstrap_stability(load_bootstrap_results(validation_status))
    report += generate_report_section_sensitivity(sensitivity_df)
    
    report += "\n## Conclusion\n"
    report += "This study identifies **associations** between gut microbiome composition and circadian rhythm disruption. "
    report += "Further mechanistic studies are required to establish causality.\n"
    
    return report

def main():
    """
    Main report generation.
    """
    try:
        DATA_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load data
        correlation_df = load_correlation_results()
        validation_status = load_validation_status()
        sensitivity_df = load_sensitivity_report()
        
        # Generate report
        report_text = generate_full_report(correlation_df, validation_status, sensitivity_df)
        
        # Save report
        output_path = DATA_OUTPUTS_DIR / "research_report.txt"
        with open(output_path, 'w') as f:
            f.write(report_text)
        
        logger.info(f"Saved research report to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        return 1