"""
Report generator module for generating summary reports from audit results.

This module generates:
- summary_report.csv: Overall audit summary with inconsistency rates
- subgroup_report.csv: Subgroup analysis results (mirrors subgroup JSON)
"""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.src.audit.subgroup_analysis import write_subgroup_csv
from code.src.utils.logger import get_default_logger, AuditLogger


def generate_summary_report(
    audit_report_path: Path,
    output_path: Path,
    logger: Optional[AuditLogger] = None
) -> bool:
    """
    Generate summary report CSV from audit report JSON.
    
    Args:
        audit_report_path: Path to audit_report.json
        output_path: Path to write summary_report.csv
        logger: Optional logger instance
        
    Returns:
        True if successful, False otherwise
    """
    if logger is None:
        logger = get_default_logger(__name__)
    
    try:
        # Read audit report
        with open(audit_report_path, 'r', encoding='utf-8') as f:
            audit_records = json.load(f)
        
        # Calculate summary statistics
        total_summaries = len(audit_records)
        inconsistent_count = sum(1 for r in audit_records if r.get('is_inconsistent', False))
        consistent_count = total_summaries - inconsistent_count
        
        # Calculate rates
        inconsistent_rate = inconsistent_count / total_summaries if total_summaries > 0 else 0.0
        consistent_rate = consistent_count / total_summaries if total_summaries > 0 else 0.0
        
        # Write summary report CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'total_summaries',
                'consistent_count',
                'inconsistent_count',
                'inconsistent_rate',
                'consistent_rate',
                'generated_at'
            ])
            writer.writerow([
                total_summaries,
                consistent_count,
                inconsistent_count,
                f'{inconsistent_rate:.6f}',
                f'{consistent_rate:.6f}',
                datetime.utcnow().isoformat()
            ])
        
        logger.info(f"Generated summary report: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate summary report: {e}")
        return False


def generate_subgroup_report(
    subgroup_json_path: Path,
    output_path: Path,
    logger: Optional[AuditLogger] = None
) -> bool:
    """
    Generate subgroup report CSV from subgroup analysis JSON.
    
    This function mirrors the subgroup JSON data into CSV format for easy inspection.
    
    Args:
        subgroup_json_path: Path to subgroup_report.json
        output_path: Path to write subgroup_report.csv
        logger: Optional logger instance
        
    Returns:
        True if successful, False otherwise
    """
    if logger is None:
        logger = get_default_logger(__name__)
    
    try:
        # Use the existing write_subgroup_csv function from subgroup_analysis
        return write_subgroup_csv(subgroup_json_path, output_path, logger)
        
    except Exception as e:
        logger.error(f"Failed to generate subgroup report CSV: {e}")
        return False


def main() -> int:
    """
    Main entry point for report generation.
    
    This function generates both summary and subgroup reports.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = get_default_logger(__name__)
    
    # Define paths
    base_path = Path(__file__).parent.parent.parent.parent
    output_dir = base_path / 'output'
    audit_report_path = output_dir / 'audit_report.json'
    subgroup_json_path = output_dir / 'subgroup_report.json'
    summary_csv_path = output_dir / 'summary_report.csv'
    subgroup_csv_path = output_dir / 'subgroup_report.csv'
    
    success = True
    
    # Generate summary report
    if audit_report_path.exists():
        if not generate_summary_report(audit_report_path, summary_csv_path, logger):
            success = False
    else:
        logger.warning(f"Audit report not found: {audit_report_path}")
    
    # Generate subgroup report CSV
    if subgroup_json_path.exists():
        if not generate_subgroup_report(subgroup_json_path, subgroup_csv_path, logger):
            success = False
    else:
        logger.warning(f"Subgroup report JSON not found: {subgroup_json_path}")
    
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())