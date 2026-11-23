import os
import sys
import json
import logging
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from statsmodels.stats.power import TTestIndPower, zt_ind_solve_power
from statsmodels.stats.effect_size import CohensD

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_EFFECT_SIZE = 0.5  # Medium effect size for power calculation
DEFAULT_SIGMA = 1.0        # Standard deviation for z-test
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80

def load_classified_threads(filepath: str = "data/processed/all_threads_classified.csv") -> pd.DataFrame:
    """Load the classified threads dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Classified threads file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} classified threads from {filepath}")
    return df

def load_thread_metrics(filepath: str = "data/processed/thread_metrics.csv") -> pd.DataFrame:
    """Load the thread metrics dataset."""
    if not os.path.exists(filepath):
        logger.warning(f"Thread metrics file not found: {filepath}. Using empty DataFrame.")
        return pd.DataFrame()
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} thread metrics from {filepath}")
    return df

def calculate_effect_size(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: Series of values for group 1
        group2: Series of values for group 2
        
    Returns:
        Cohen's d effect size
    """
    if len(group1) == 0 or len(group2) == 0:
        return 0.0
    
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(ddof=1), group2.std(ddof=1)
    
    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    if std1 == 0 and std2 == 0:
        return 0.0
        
    pooled_std = math.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def calculate_power(n: int, effect_size: float, alpha: float = DEFAULT_ALPHA) -> float:
    """
    Calculate post-hoc power for a two-sample t-test.
    
    Args:
        n: Sample size (per group, assuming equal groups)
        effect_size: Cohen's d effect size
        alpha: Significance level
        
    Returns:
        Statistical power (probability of detecting the effect)
    """
    if n <= 0 or effect_size == 0:
        return 0.0
    
    # Use TTestIndPower for two-sample t-test power
    power_analysis = TTestIndPower()
    try:
        power = power_analysis.power(effect_size=effect_size, nobs1=n, alpha=alpha, ratio=1.0)
        return float(power)
    except Exception as e:
        logger.warning(f"Power calculation failed for n={n}, effect_size={effect_size}: {e}")
        return 0.0

def analyze_sampling_issues(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze potential sampling issues in the dataset.
    
    Args:
        df: DataFrame with classified threads
        
    Returns:
        Dictionary with sampling analysis results
    """
    issues = []
    
    # Check for class imbalance
    if 'is_valid' in df.columns:
        valid_count = df['is_valid'].sum()
        total_count = len(df)
        valid_ratio = valid_count / total_count if total_count > 0 else 0
        
        if valid_ratio < 0.3:
            issues.append({
                'type': 'class_imbalance',
                'severity': 'high',
                'description': f'Low valid thread ratio: {valid_ratio:.2%} (threshold: 30%)',
                'valid_count': int(valid_count),
                'total_count': int(total_count)
            })
        elif valid_ratio < 0.5:
            issues.append({
                'type': 'class_imbalance',
                'severity': 'medium',
                'description': f'Moderate valid thread ratio: {valid_ratio:.2%}',
                'valid_count': int(valid_count),
                'total_count': int(total_count)
            })
    
    # Check for small sample sizes in subgroups
    if 'subreddit' in df.columns:
        subreddit_counts = df['subreddit'].value_counts()
        for subreddit, count in subreddit_counts.items():
            if count < 30:
                issues.append({
                    'type': 'small_subgroup',
                    'severity': 'medium',
                    'description': f'Small sample size for {subreddit}: {count} threads',
                    'subreddit': subreddit,
                    'count': int(count)
                })
    
    # Check for missing data
    missing_cols = df.columns[df.isnull().any()].tolist()
    if missing_cols:
        for col in missing_cols:
            missing_pct = df[col].isnull().sum() / len(df) * 100
            if missing_pct > 5:
                issues.append({
                    'type': 'missing_data',
                    'severity': 'high' if missing_pct > 20 else 'medium',
                    'description': f'Missing data in {col}: {missing_pct:.1f}%',
                    'column': col,
                    'missing_pct': float(missing_pct)
                })
    
    return {
        'issues': issues,
        'total_issues': len(issues),
        'high_severity': sum(1 for i in issues if i['severity'] == 'high'),
        'medium_severity': sum(1 for i in issues if i['severity'] == 'medium')
    }

def generate_power_analysis_report(
    classified_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    effect_size: float = DEFAULT_EFFECT_SIZE,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Generate a comprehensive power analysis report.
    
    Args:
        classified_df: DataFrame with classified threads
        metrics_df: DataFrame with thread metrics
        effect_size: Expected effect size for power calculation
        alpha: Significance level
        
    Returns:
        Dictionary with power analysis results
    """
    report = {
        'total_threads': len(classified_df),
        'valid_threads': int(classified_df['is_valid'].sum()) if 'is_valid' in classified_df.columns else 0,
        'invalid_threads': int(len(classified_df) - classified_df['is_valid'].sum()) if 'is_valid' in classified_df.columns else len(classified_df),
        'valid_ratio': float(classified_df['is_valid'].mean()) if 'is_valid' in classified_df.columns else 0.0,
        'effect_size_used': effect_size,
        'alpha': alpha,
        'power_analysis': {},
        'sampling_issues': {},
        'recommendations': []
    }
    
    # Calculate power for the main comparison (valid vs invalid)
    if 'is_valid' in classified_df.columns and len(classified_df) > 10:
        valid_df = classified_df[classified_df['is_valid'] == True]
        invalid_df = classified_df[classified_df['is_valid'] == False]
        
        n_valid = len(valid_df)
        n_invalid = len(invalid_df)
        
        # Calculate observed effect size if we have a metric to compare
        if 'contagion_index' in metrics_df.columns:
            # Merge to get metrics for each thread
            merged = classified_df.merge(metrics_df[['thread_id', 'contagion_index']], on='thread_id', how='left')
            valid_scores = merged[merged['is_valid']]['contagion_index'].dropna()
            invalid_scores = merged[~merged['is_valid']]['contagion_index'].dropna()
            
            if len(valid_scores) > 1 and len(invalid_scores) > 1:
                observed_effect = calculate_effect_size(valid_scores, invalid_scores)
                report['power_analysis']['observed_effect_size'] = float(observed_effect)
                
                # Calculate power for observed effect
                power_valid = calculate_power(n_valid, observed_effect, alpha)
                power_invalid = calculate_power(n_invalid, observed_effect, alpha)
                report['power_analysis']['power_valid_group'] = float(power_valid)
                report['power_analysis']['power_invalid_group'] = float(power_invalid)
                report['power_analysis']['average_power'] = float((power_valid + power_invalid) / 2)
            else:
                report['power_analysis']['observed_effect_size'] = None
                report['power_analysis']['power_valid_group'] = None
                report['power_analysis']['power_invalid_group'] = None
                report['power_analysis']['average_power'] = None
        else:
            # Use expected effect size for power calculation
            power_valid = calculate_power(n_valid, effect_size, alpha)
            power_invalid = calculate_power(n_invalid, effect_size, alpha)
            report['power_analysis']['expected_effect_size'] = effect_size
            report['power_analysis']['power_valid_group'] = float(power_valid)
            report['power_analysis']['power_invalid_group'] = float(power_invalid)
            report['power_analysis']['average_power'] = float((power_valid + power_invalid) / 2)
    
    # Analyze sampling issues
    report['sampling_issues'] = analyze_sampling_issues(classified_df)
    
    # Generate recommendations
    if report['power_analysis'].get('average_power', 0) < 0.8:
        report['recommendations'].append({
            'type': 'low_power',
            'message': f"Statistical power is below 0.8 (current: {report['power_analysis'].get('average_power', 0):.2f}). Consider increasing sample size or interpreting results with caution."
        })
    
    if report['sampling_issues']['high_severity'] > 0:
        report['recommendations'].append({
            'type': 'sampling_issues',
            'message': f"Found {report['sampling_issues']['high_severity']} high-severity sampling issues that may affect validity."
        })
    
    if report['valid_ratio'] < 0.3:
        report['recommendations'].append({
            'type': 'ground_truth_threshold',
            'message': "Valid thread ratio is below 30% threshold. Results may be limited by ground truth availability."
        })
    
    return report

def append_to_summary(summary_path: str, report: Dict[str, Any]) -> None:
    """
    Append power analysis results to the analysis summary document.
    
    Args:
        summary_path: Path to the analysis summary markdown file
        report: Power analysis report dictionary
    """
    summary_file = Path(summary_path)
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create the power analysis section
    power_section = [
        "\n## Post-Hoc Power Analysis\n",
        f"**Total Threads Analyzed**: {report['total_threads']}\n",
        f"**Valid Threads**: {report['valid_threads']} ({report['valid_ratio']:.1%})\n",
        f"**Invalid Threads**: {report['invalid_threads']}\n\n"
    ]
    
    if report['power_analysis']:
        power_section.append("### Power Calculation Results\n")
        if 'observed_effect_size' in report['power_analysis'] and report['power_analysis']['observed_effect_size'] is not None:
            power_section.append(f"- **Observed Effect Size (Cohen's d)**: {report['power_analysis']['observed_effect_size']:.3f}\n")
        elif 'expected_effect_size' in report['power_analysis']:
            power_section.append(f"- **Expected Effect Size (Cohen's d)**: {report['power_analysis']['expected_effect_size']:.3f}\n")
        
        if report['power_analysis'].get('average_power') is not None:
            power_section.append(f"- **Statistical Power**: {report['power_analysis']['average_power']:.2f}\n")
            if report['power_analysis']['average_power'] < 0.8:
                power_section.append("  - ⚠️ **Warning**: Power is below the recommended threshold of 0.8. Results should be interpreted with caution.\n")
            else:
                power_section.append("  - ✓ Power is sufficient for detecting the specified effect size.\n")
        else:
            power_section.append("- **Statistical Power**: Unable to calculate (insufficient data)\n")
        
        if report['power_analysis'].get('power_valid_group') is not None:
            power_section.append(f"- **Power (Valid Group)**: {report['power_analysis']['power_valid_group']:.2f}\n")
        if report['power_analysis'].get('power_invalid_group') is not None:
            power_section.append(f"- **Power (Invalid Group)**: {report['power_analysis']['power_invalid_group']:.2f}\n")
    
    if report['sampling_issues'].get('issues'):
        power_section.append("\n### Sampling Issues\n")
        for issue in report['sampling_issues']['issues']:
            severity_icon = "🔴" if issue['severity'] == 'high' else "🟡"
            power_section.append(f"- {severity_icon} **{issue['type']}**: {issue['description']}\n")
    
    if report['recommendations']:
        power_section.append("\n### Recommendations\n")
        for rec in report['recommendations']:
            power_section.append(f"- **{rec['type']}**: {rec['message']}\n")
    
    # Append to summary file
    summary_text = "".join(power_section)
    
    # Check if file exists and has content
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Avoid duplicate sections
        if "## Post-Hoc Power Analysis" in existing_content:
            logger.info("Power analysis section already exists in summary. Updating...")
            # Simple approach: replace the section (in a real implementation, we'd use more sophisticated parsing)
            # For now, we'll just append to ensure the latest data is there
            with open(summary_file, 'a', encoding='utf-8') as f:
                f.write("\n\n---\n\n" + summary_text)
        else:
            with open(summary_file, 'a', encoding='utf-8') as f:
                f.write(summary_text)
    else:
        # Create new file with the section
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_text)
    
    logger.info(f"Appended power analysis to {summary_path}")

def main():
    """Main entry point for the power analysis script."""
    logger.info("Starting post-hoc power analysis...")
    
    # File paths
    classified_path = "data/processed/all_threads_classified.csv"
    metrics_path = "data/processed/thread_metrics.csv"
    summary_path = "docs/analysis_summary.md"
    output_path = "state/power_analysis_report.json"
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        logger.info(f"Loading classified threads from {classified_path}...")
        classified_df = load_classified_threads(classified_path)
        
        logger.info(f"Loading thread metrics from {metrics_path}...")
        metrics_df = load_thread_metrics(metrics_path)
        
        # Generate report
        logger.info("Generating power analysis report...")
        report = generate_power_analysis_report(classified_df, metrics_df)
        
        # Save report to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Saved power analysis report to {output_path}")
        
        # Append to summary
        logger.info(f"Appending results to {summary_path}...")
        append_to_summary(summary_path, report)
        
        # Print summary
        print("\n=== Power Analysis Summary ===")
        print(f"Total threads: {report['total_threads']}")
        print(f"Valid threads: {report['valid_threads']} ({report['valid_ratio']:.1%})")
        if report['power_analysis'].get('average_power') is not None:
            print(f"Statistical power: {report['power_analysis']['average_power']:.2f}")
        if report['recommendations']:
            print("\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  - {rec['message']}")
        print("=============================\n")
        
        logger.info("Power analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during power analysis: {e}")
        raise

if __name__ == "__main__":
    main()
