"""
Sampling and Power Analysis Module.

This module handles data sampling strategies and statistical power analysis
to ensure the dataset is representative and sufficient for the study's
statistical requirements.
"""
import os
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_extracted_data(filepath: str) -> pd.DataFrame:
    """
    Load the extracted thread data from a CSV file.

    Args:
        filepath: Path to the CSV file containing extracted threads.

    Returns:
        DataFrame with thread data.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Extracted data file not found: {filepath}")

    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} threads from {filepath}")
    return df

def load_thread_metrics(filepath: str) -> pd.DataFrame:
    """
    Load thread metrics from a CSV file.

    Args:
        filepath: Path to the CSV file containing thread metrics.

    Returns:
        DataFrame with thread metrics.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Thread metrics file not found: {filepath}")

    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} thread metrics from {filepath}")
    return df

def calculate_stratification_grid(df: pd.DataFrame, stratify_cols: List[str] = None) -> Dict[str, Any]:
    """
    Calculate the stratification grid for representative sampling.

    Args:
        df: DataFrame containing thread data.
        stratify_cols: List of columns to use for stratification.

    Returns:
        Dictionary with stratification details.
    """
    if stratify_cols is None:
        stratify_cols = ['subreddit', 'thread_length_bin']

    # Create bins for thread length if not present
    if 'thread_length_bin' not in df.columns and 'reply_count' in df.columns:
        df['thread_length_bin'] = pd.cut(
            df['reply_count'],
            bins=[0, 5, 10, 20, 50, float('inf')],
            labels=['0-5', '6-10', '11-20', '21-50', '50+']
        )

    # Calculate distribution
    distribution = {}
    for col in stratify_cols:
        if col in df.columns:
            dist = df[col].value_counts(normalize=True).to_dict()
            distribution[col] = {k: float(v) for k, v in dist.items()}

    return {
        'stratification_columns': stratify_cols,
        'distribution': distribution,
        'total_count': len(df)
    }

def generate_power_analysis_report(
    df: pd.DataFrame,
    expected_effect_size: float = 0.3,
    power_target: float = 0.8,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a power analysis report for the current dataset.

    Args:
        df: DataFrame containing thread data.
        expected_effect_size: Expected effect size (Cohen's d).
        power_target: Target statistical power.
        alpha: Significance level.

    Returns:
        Dictionary with power analysis results.
    """
    # Calculate sample size needed for correlation analysis
    # Using simplified approximation for Pearson correlation
    n = len(df)

    # For correlation, approximate required n based on effect size
    # This is a simplified calculation; real power analysis would use statsmodels
    if expected_effect_size > 0:
        # Approximation: n ≈ (Z_alpha + Z_beta)^2 / effect_size^2
        # For alpha=0.05 (Z=1.96), power=0.8 (Z=0.84)
        z_alpha = 1.96
        z_beta = 0.84
        required_n = int(((z_alpha + z_beta) ** 2) / (expected_effect_size ** 2))
    else:
        required_n = 0

    # Calculate actual power achieved
    if n > 0 and expected_effect_size > 0:
        # Simplified power calculation
        achieved_power = 1.0 - (1.0 / (1.0 + (n * expected_effect_size ** 2)))
    else:
        achieved_power = 0.0

    # Analyze subgroup sizes
    subgroup_analysis = {}
    if 'subreddit' in df.columns:
        for subreddit, group in df.groupby('subreddit'):
            subgroup_analysis[subreddit] = {
                'count': len(group),
                'percentage': len(group) / n * 100 if n > 0 else 0
            }

    # Check for power limitations
    power_limitation = n < 100
    warning_message = ""
    if power_limitation:
        warning_message = (
            f"Power limitation detected: n = {n} threads (target: {required_n}). "
            "Results should be interpreted with caution due to limited statistical power."
        )

    report = {
        'total_threads': n,
        'expected_effect_size': expected_effect_size,
        'target_power': power_target,
        'alpha': alpha,
        'required_sample_size': required_n,
        'achieved_power': achieved_power,
        'power_limitation': power_limitation,
        'warning_message': warning_message if power_limitation else None,
        'subgroup_analysis': subgroup_analysis,
        'recommendation': (
            "Consider increasing sample size" if power_limitation else
            "Sample size appears sufficient for effect size"
        )
    }

    logger.info(f"Power analysis complete: {n} threads, required: {required_n}")
    return report

def update_analysis_summary_with_power_limitations(
    summary_path: str,
    power_report: Dict[str, Any]
) -> None:
    """
    Update the analysis summary document with power limitation warnings.

    Args:
        summary_path: Path to the analysis summary markdown file.
        power_report: Dictionary containing power analysis results.
    """
    summary_file = Path(summary_path)
    if not summary_file.exists():
        logger.warning(f"Analysis summary file not found: {summary_path}")
        return

    # Read existing content
    with open(summary_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Prepare power limitation section
    power_section = "\n\n## Statistical Power Analysis\n\n"

    if power_report.get('power_limitation'):
        power_section += f"**⚠️ WARNING**: {power_report.get('warning_message', '')}\n\n"
        power_section += f"- Total threads: {power_report.get('total_threads')}\n"
        power_section += f"- Required sample size (for effect size {power_report.get('expected_effect_size')}): {power_report.get('required_sample_size')}\n"
        power_section += f"- Achieved power: {power_report.get('achieved_power', 0):.3f}\n"
        power_section += f"- Recommendation: {power_report.get('recommendation')}\n"
    else:
        power_section += f"**✓ Sufficient Power**: Sample size of {power_report.get('total_threads')} threads meets requirements.\n"
        power_section += f"- Required sample size: {power_report.get('required_sample_size')}\n"
        power_section += f"- Achieved power: {power_report.get('achieved_power', 0):.3f}\n"

    # Append to summary if not already present
    if "Statistical Power Analysis" not in content:
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(power_section)
        logger.info(f"Updated analysis summary with power analysis at {summary_path}")
    else:
        logger.info("Power analysis section already exists in summary")

def main():
    """
    Main function to run the sampling and power analysis pipeline.
    """
    # Define paths
    base_path = Path(__file__).parent.parent.parent
    extracted_data_path = base_path / "data" / "processed" / "all_threads_classified.csv"
    metrics_path = base_path / "data" / "processed" / "thread_metrics.csv"
    summary_path = base_path / "docs" / "analysis_summary.md"
    output_path = base_path / "state" / "power_analysis_report.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load data
        logger.info("Loading extracted thread data...")
        df = load_extracted_data(str(extracted_data_path))

        # Calculate stratification grid
        logger.info("Calculating stratification grid...")
        stratification = calculate_stratification_grid(df)

        # Generate power analysis report
        logger.info("Generating power analysis report...")
        power_report = generate_power_analysis_report(df)

        # Save power analysis report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(power_report, f, indent=2, default=str)
        logger.info(f"Saved power analysis report to {output_path}")

        # Update analysis summary
        logger.info("Updating analysis summary...")
        update_analysis_summary_with_power_limitations(str(summary_path), power_report)

        # Print summary
        print("\n=== Power Analysis Summary ===")
        print(f"Total threads: {power_report['total_threads']}")
        print(f"Required sample size: {power_report['required_sample_size']}")
        print(f"Power limitation: {power_report['power_limitation']}")
        if power_report['power_limitation']:
            print(f"Warning: {power_report['warning_message']}")
        print("==============================\n")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during power analysis: {e}")
        raise

if __name__ == "__main__":
    main()
