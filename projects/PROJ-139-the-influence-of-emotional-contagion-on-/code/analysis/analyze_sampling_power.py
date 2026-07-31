"""
Post-hoc power analysis for the emotional contagion study.

This module enhances T033 by implementing a rigorous post-hoc power calculation
using statsmodels.stats.power, rather than just a simple threshold check.
"""
import os
import sys
import json
import logging
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from statsmodels.stats.power import TTestIndPower, FTestAnovaPower, GofChisquarePower

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state"
DOCS_DIR = PROJECT_ROOT / "docs"

# Ensure directories exist
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def load_classified_threads() -> Optional[pd.DataFrame]:
    """Load the classified threads dataset."""
    path = DATA_PROCESSED / "all_threads_classified.csv"
    if not path.exists():
        logger.error(f"Classified threads file not found: {path}")
        return None
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} threads from {path}")
        return df
    except Exception as e:
        logger.error(f"Error loading classified threads: {e}")
        return None

def load_thread_metrics() -> Optional[pd.DataFrame]:
    """Load the thread metrics dataset."""
    path = DATA_PROCESSED / "thread_metrics.csv"
    if not path.exists():
        logger.error(f"Thread metrics file not found: {path}")
        return None
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} thread metrics from {path}")
        return df
    except Exception as e:
        logger.error(f"Error loading thread metrics: {e}")
        return None

def calculate_effect_size(df: pd.DataFrame, group_col: str, value_col: str) -> float:
    """
    Calculate Cohen's d effect size between two groups defined by group_col.
    Assumes binary group_col for simplicity in this context.
    """
    if group_col not in df.columns or value_col not in df.columns:
        logger.warning(f"Columns {group_col} or {value_col} not found in dataframe")
        return 0.0

    # Drop NaNs
    clean_df = df[[group_col, value_col]].dropna()
    if len(clean_df) < 2:
        return 0.0

    # Assume binary groups (0 and 1)
    groups = clean_df[group_col].unique()
    if len(groups) != 2:
        # If not binary, try to binarize or return 0
        logger.warning(f"Group column {group_col} is not binary. Cannot calculate Cohen's d.")
        return 0.0

    g0 = clean_df[clean_df[group_col] == groups[0]][value_col]
    g1 = clean_df[clean_df[group_col] == groups[1]][value_col]

    if len(g0) == 0 or len(g1) == 0:
        return 0.0

    mean0, mean1 = g0.mean(), g1.mean()
    std0, std1 = g0.std(), g1.std()

    # Pooled standard deviation
    n0, n1 = len(g0), len(g1)
    pooled_std = math.sqrt(((n0 - 1) * std0**2 + (n1 - 1) * std1**2) / (n0 + n1 - 2))

    if pooled_std == 0:
        return 0.0

    cohens_d = (mean1 - mean0) / pooled_std
    return abs(cohens_d)

def calculate_power(effect_size: float, n_obs: int, alpha: float = 0.05) -> float:
    """
    Calculate statistical power for a two-sample t-test given effect size and sample size.
    """
    if effect_size <= 0 or n_obs <= 1:
        return 0.0

    # TTestIndPower expects total sample size (n1 + n2) and ratio=1.0 for equal groups
    # However, we often have one large group (n_obs) representing the effective sample.
    # For a conservative estimate, assume equal split if possible, or use n_obs/2 per group.
    # A more robust approach: use the actual n per group if known.
    # Here we approximate: n_per_group = n_obs / 2
    n_per_group = n_obs / 2.0

    power_analysis = TTestIndPower()
    try:
        power = power_analysis.solve_power(effect_size=effect_size,
                                           nobs1=n_per_group,
                                           alpha=alpha,
                                           power=None,
                                           ratio=1.0)
        return power if not math.isnan(power) else 0.0
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}")
        return 0.0

def analyze_sampling_issues(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze the dataset for sampling issues (e.g., small n, missing data).
    """
    issues = []
    total_rows = len(df)
    if total_rows < 30:
        issues.append({
            "type": "small_sample",
            "message": f"Sample size ({total_rows}) is below recommended minimum of 30.",
            "severity": "high"
        })
    
    # Check for missing values in key columns
    key_cols = ['thread_id', 'sentiment_score', 'contagion_index']
    for col in key_cols:
        if col in df.columns:
            missing = df[col].isna().sum()
            if missing > 0:
                pct = (missing / total_rows) * 100
                issues.append({
                    "type": "missing_data",
                    "column": col,
                    "count": int(missing),
                    "percentage": round(pct, 2),
                    "severity": "medium" if pct < 10 else "high"
                })
    
    return {
        "total_samples": total_rows,
        "issues": issues
    }

def generate_power_analysis_report(
    classified_df: Optional[pd.DataFrame],
    metrics_df: Optional[pd.DataFrame],
    observed_effect_col: str = 'contagion_index',
    group_col: str = 'is_valid' # Example grouping, adjust based on actual analysis needs
) -> Dict[str, Any]:
    """
    Generate a comprehensive post-hoc power analysis report.
    """
    report = {
        "status": "success",
        "sample_size": 0,
        "effect_size": 0.0,
        "power": 0.0,
        "interpretation": "",
        "issues": [],
        "recommendations": []
    }

    if classified_df is None or metrics_df is None:
        report["status"] = "error"
        report["interpretation"] = "Could not load required datasets."
        return report

    # Merge on thread_id to get combined data if necessary
    # For simplicity, assume we are calculating power on the metrics_df if it has the effect
    # or classified_df if it has the group.
    # Let's assume we want to test the difference in 'contagion_index' between 'is_valid' groups.
    
    # If metrics_df has 'contagion_index' and classified_df has 'is_valid', we need to merge.
    if 'contagion_index' not in metrics_df.columns:
        report["status"] = "warning"
        report["interpretation"] = "Contagion index not found in metrics. Using sample size only."
        report["sample_size"] = len(metrics_df)
        return report

    # Merge to get group labels for the metrics
    # Assuming thread_id is the key
    merged_df = pd.merge(metrics_df, classified_df[['thread_id', 'is_valid']], on='thread_id', how='inner')
    
    if len(merged_df) == 0:
        report["status"] = "error"
        report["interpretation"] = "No overlapping data between metrics and classified threads."
        return report

    report["sample_size"] = len(merged_df)

    # Calculate effect size (Cohen's d)
    effect_size = calculate_effect_size(merged_df, 'is_valid', 'contagion_index')
    report["effect_size"] = round(effect_size, 4)

    # Calculate power
    power = calculate_power(effect_size, len(merged_df))
    report["power"] = round(power, 4)

    # Interpretation
    if power < 0.8:
        report["interpretation"] = f"Post-hoc power analysis indicates low statistical power ({power:.2f}). " \
                                   f"The study may be underpowered to detect the observed effect size ({effect_size:.4f}). " \
                                   f"Results should be interpreted with caution."
        report["recommendations"].append("Consider increasing sample size in future studies.")
    else:
        report["interpretation"] = f"Post-hoc power analysis indicates sufficient statistical power ({power:.2f}). " \
                                   f"The study is adequately powered to detect the observed effect size ({effect_size:.4f})."

    # Analyze sampling issues
    issues = analyze_sampling_issues(merged_df)
    report["issues"] = issues["issues"]

    return report

def append_to_summary(report: Dict[str, Any]) -> bool:
    """
    Append the power analysis results to the docs/analysis_summary.md file.
    """
    summary_path = DOCS_DIR / "analysis_summary.md"
    
    section_header = "\n### Post-Hoc Power Analysis\n\n"
    
    content_lines = []
    content_lines.append(f"- **Sample Size**: {report.get('sample_size', 'N/A')}")
    content_lines.append(f"- **Observed Effect Size (Cohen\\'s d)**: {report.get('effect_size', 'N/A')}")
    content_lines.append(f"- **Calculated Power**: {report.get('power', 'N/A')}")
    content_lines.append(f"- **Interpretation**: {report.get('interpretation', 'N/A')}")
    
    if report.get('recommendations'):
        content_lines.append("\n**Recommendations**:")
        for rec in report['recommendations']:
            content_lines.append(f"- {rec}")

    if report.get('issues'):
        content_lines.append("\n**Identified Issues**:")
        for issue in report['issues']:
            content_lines.append(f"- {issue.get('message', 'Unknown issue')}")

    new_section = section_header + "\n".join(content_lines) + "\n"

    try:
        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # Check if section already exists to avoid duplication
            if "### Post-Hoc Power Analysis" in existing_content:
                # Replace existing section
                import re
                pattern = r'\n### Post-Hoc Power Analysis.*?(?=\n###|\Z)'
                new_content = re.sub(pattern, new_section, existing_content, flags=re.DOTALL)
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info("Updated existing Post-Hoc Power Analysis section.")
            else:
                with open(summary_path, 'a', encoding='utf-8') as f:
                    f.write(new_section)
                logger.info("Appended Post-Hoc Power Analysis section.")
        else:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("# Analysis Summary\n" + new_section)
            logger.info("Created new analysis_summary.md with Post-Hoc Power Analysis.")
        
        return True
    except Exception as e:
        logger.error(f"Failed to update analysis summary: {e}")
        return False

def main():
    """Main entry point for the power analysis task."""
    logger.info("Starting Post-Hoc Power Analysis (T060)...")
    
    classified_df = load_classified_threads()
    metrics_df = load_thread_metrics()
    
    if classified_df is None or metrics_df is None:
        logger.error("Missing required data files. Cannot proceed with power analysis.")
        # Create a failure report
        report = {
            "status": "error",
            "message": "Missing data files",
            "sample_size": 0,
            "effect_size": 0.0,
            "power": 0.0,
            "interpretation": "Could not load required datasets. Check if all_threads_classified.csv and thread_metrics.csv exist."
        }
        output_path = DATA_PROCESSED / "power_analysis_report.json"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Power analysis failure report written to {output_path}")
        return 1

    report = generate_power_analysis_report(classified_df, metrics_df)
    
    # Save report to JSON
    output_path = DATA_PROCESSED / "power_analysis_report.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Power analysis report saved to {output_path}")
    
    # Append to summary
    if append_to_summary(report):
        logger.info("Successfully appended power analysis to docs/analysis_summary.md")
    else:
        logger.warning("Failed to append power analysis to docs/analysis_summary.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())