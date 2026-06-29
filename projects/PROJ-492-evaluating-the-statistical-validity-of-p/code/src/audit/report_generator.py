"""
Report generation module for A/B test audit pipeline.

Implements T047: Generate CSV summary report from audit artifacts.
"""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.src.utils.logger import get_default_logger


def generate_summary_report(
    audit_report_path: Path,
    prevalence_path: Path,
    bias_adjustment_path: Path,
    output_path: Path
) -> bool:
    """
    Generate summary CSV report from audit artifacts.

    Required columns (FR-047):
    - total_summaries
    - inconsistent_count
    - inconsistent_rate
    - bias_adjusted_rate
    - wilson_ci_lower
    - wilson_ci_upper
    """
    logger = get_default_logger(Path(__file__).parent.parent / 'logs' / 'report_generator.log')

    try:
        # Load audit report
        with open(audit_report_path, 'r') as f:
            audit_data = json.load(f)

        # Load prevalence results
        with open(prevalence_path, 'r') as f:
            prevalence_data = json.load(f)

        # Load bias adjustment results
        with open(bias_adjustment_path, 'r') as f:
            bias_data = json.load(f)

        # Extract values
        records = audit_data.get('records', [])
        total_summaries = len(records)
        inconsistent_count = sum(1 for r in records if r.get('is_inconsistent', False))
        inconsistent_rate = prevalence_data.get('inconsistency_rate', 0.0)
        bias_adjusted_rate = bias_data.get('bias_adjusted_rate', 0.0)
        wilson_ci_lower = prevalence_data.get('wilson_ci', {}).get('lower', 0.0)
        wilson_ci_upper = prevalence_data.get('wilson_ci', {}).get('upper', 1.0)

        # Write CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'total_summaries',
                'inconsistent_count',
                'inconsistent_rate',
                'bias_adjusted_rate',
                'wilson_ci_lower',
                'wilson_ci_upper',
                'timestamp'
            ])
            writer.writerow([
                total_summaries,
                inconsistent_count,
                f'{inconsistent_rate:.6f}',
                f'{bias_adjusted_rate:.6f}',
                f'{wilson_ci_lower:.6f}',
                f'{wilson_ci_upper:.6f}',
                datetime.utcnow().isoformat()
            ])

        logger.info(f"Summary report generated: {output_path}")
        return True

    except Exception as e:
        logger.error(f"ERR-471: Summary report generation failed: {e}")
        return False


def main():
    """Main entry point for standalone report generation."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate summary report')
    parser.add_argument('--audit-report', type=str, required=True, help='Input audit report JSON')
    parser.add_argument('--prevalence', type=str, required=True, help='Input prevalence JSON')
    parser.add_argument('--bias-adjustment', type=str, required=True, help='Input bias adjustment JSON')
    parser.add_argument('--output', type=str, required=True, help='Output CSV path')
    args = parser.parse_args()

    success = generate_summary_report(
        Path(args.audit_report),
        Path(args.prevalence),
        Path(args.bias_adjustment),
        Path(args.output)
    )

    if success:
        print(f"Summary report written to {args.output}")
    else:
        print("Report generation failed")
        exit(1)


if __name__ == '__main__':
    main()
