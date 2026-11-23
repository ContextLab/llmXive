"""
Exclusion analysis module for T020.
Provides functions to analyze and report on excluded subjects.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from utils.logging import setup_logger
from utils.config import get_config

def load_exclusion_log(exclusion_path: str) -> pd.DataFrame:
    """Load exclusion log from CSV file."""
    path = Path(exclusion_path)
    if not path.exists():
        raise FileNotFoundError(f"Exclusion log not found: {exclusion_path}")
    
    return pd.read_csv(path)

def summarize_exclusions(exclusion_df: pd.DataFrame) -> Dict:
    """Generate summary statistics of exclusions."""
    if exclusion_df.empty:
        return {
            'total_excluded': 0,
            'by_reason': {},
            'excluded_subjects': []
        }
    
    reason_counts = exclusion_df['reason'].value_counts().to_dict()
    
    return {
        'total_excluded': len(exclusion_df),
        'by_reason': reason_counts,
        'excluded_subjects': exclusion_df['subject_id'].tolist()
    }

def generate_exclusion_report(exclusion_df: pd.DataFrame, output_path: str):
    """Generate a detailed exclusion report."""
    summary = summarize_exclusions(exclusion_df)
    
    report_lines = [
        "=== EXCLUSION LOG REPORT ===",
        f"Total Excluded Subjects: {summary['total_excluded']}",
        "",
        "Breakdown by Reason:"
    ]
    
    for reason, count in summary['by_reason'].items():
        report_lines.append(f"  - {reason}: {count}")
    
    if summary['excluded_subjects']:
        report_lines.append("")
        report_lines.append("Excluded Subject IDs:")
        for subj_id in summary['excluded_subjects']:
            report_lines.append(f"  - {subj_id}")
    
    report_content = "\n".join(report_lines)
    
    # Save report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(report_content)
    
    logging.info(f"Exclusion report saved to {output_path}")
    return report_content

def run_exclusion_analysis(exclusion_path: str = None, report_path: str = None):
    """
    Run exclusion analysis and generate report.
    
    Args:
        exclusion_path: Path to exclusion_log.csv
        report_path: Path to save exclusion_report.txt
    """
    config = get_config()
    exclusion_file = exclusion_path or config.output_paths.exclusion_log
    report_file = report_path or config.output_paths.exclusion_report
    
    logger = setup_logger('exclusion_analysis')
    logger.info("Starting exclusion analysis")
    
    try:
        exclusion_df = load_exclusion_log(exclusion_file)
        logger.info(f"Loaded {len(exclusion_df)} exclusion records")
        
        report = generate_exclusion_report(exclusion_df, report_file)
        logger.info("Exclusion analysis completed successfully")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in exclusion analysis: {e}")
        raise

def main():
    """Entry point for exclusion analysis script."""
    run_exclusion_analysis()

if __name__ == '__main__':
    main()
