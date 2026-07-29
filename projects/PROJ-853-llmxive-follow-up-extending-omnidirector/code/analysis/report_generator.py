"""
Report Generator for OmniDirector Statistical Analysis (T034)

Generates the final statistical report 'report.md' containing:
SC-001: Reconstruction Error Analysis
SC-002: Correlation Analysis (Complexity vs Accuracy)
SC-003: Aspect Ratio Validation
SC-004: Dataset Filtering Success Rate
SC-005: Execution Timing
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import from existing project modules
from analysis.metrics import calculate_reconstruction_error, compute_statistics
from analysis.results_aggregator import load_poses_estimated, load_filtered_sequences
from analysis.validation import validate_aspect_ratio_against_ground_truth
from analysis.scoring import calculate_filtering_success_rate
from analysis.timing import format_duration, get_current_timestamp
from config import get_path, load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_results_data() -> Dict[str, Any]:
    """Load all necessary data files for report generation."""
    config = load_config()
    
    # Load filtered sequences (for SC-004)
    filtered_path = get_path('filtered_sequences', config)
    filtered_data = load_filtered_sequences(filtered_path)
    
    # Load poses estimated (for SC-001, SC-002, SC-003)
    poses_path = get_path('poses_estimated', config)
    poses_data = load_poses_estimated(poses_path)
    
    # Load final reconstruction results (for SC-004, SC-005)
    results_path = get_path('reconstruction_results', config)
    results_data = None
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                results_data = rows[0]  # Single row summary
    
    return {
        'filtered': filtered_data,
        'poses': poses_data,
        'results': results_data
    }

def calculate_error_summary(poses_data: List[Dict]) -> Dict[str, Any]:
    """Calculate reconstruction error statistics (SC-001)."""
    if not poses_data:
        return {
            'mean_error': 0.0,
            'median_error': 0.0,
            'std_error': 0.0,
            'max_error': 0.0,
            'min_error': 0.0,
            'total_sequences': 0,
            'error_distribution': {}
        }
    
    errors = []
    for seq in poses_data:
        if 'reconstruction_error' in seq and seq['reconstruction_error'] is not None:
            errors.append(float(seq['reconstruction_error']))
    
    if not errors:
        return {
            'mean_error': 0.0,
            'median_error': 0.0,
            'std_error': 0.0,
            'max_error': 0.0,
            'min_error': 0.0,
            'total_sequences': len(poses_data),
            'error_distribution': {}
        }
    
    import numpy as np
    errors_arr = np.array(errors)
    
    # Create error distribution buckets
    distribution = {
        '0-5%': 0,
        '5-10%': 0,
        '10-20%': 0,
        '20-50%': 0,
        '>50%': 0
    }
    
    for err in errors_arr:
        if err < 0.05:
            distribution['0-5%'] += 1
        elif err < 0.10:
            distribution['5-10%'] += 1
        elif err < 0.20:
            distribution['10-20%'] += 1
        elif err < 0.50:
            distribution['20-50%'] += 1
        else:
            distribution['>50%'] += 1
    
    return {
        'mean_error': float(np.mean(errors_arr)),
        'median_error': float(np.median(errors_arr)),
        'std_error': float(np.std(errors_arr)),
        'max_error': float(np.max(errors_arr)),
        'min_error': float(np.min(errors_arr)),
        'total_sequences': len(errors),
        'error_distribution': distribution
    }

def calculate_correlation_summary(poses_data: List[Dict]) -> Dict[str, Any]:
    """Calculate correlation between complexity and accuracy (SC-002)."""
    if not poses_data or len(poses_data) < 2:
        return {
            'pearson_r': None,
            'p_value': None,
            'interpretation': 'Insufficient data for correlation analysis',
            'sample_size': len(poses_data)
        }
    
    complexities = []
    errors = []
    
    for seq in poses_data:
        if ('camera_complexity' in seq and seq['camera_complexity'] is not None and
            'reconstruction_error' in seq and seq['reconstruction_error'] is not None):
            complexities.append(float(seq['camera_complexity']))
            errors.append(float(seq['reconstruction_error']))
    
    if len(complexities) < 2:
        return {
            'pearson_r': None,
            'p_value': None,
            'interpretation': 'Insufficient valid pairs for correlation',
            'sample_size': len(complexities)
        }
    
    import numpy as np
    from scipy import stats
    
    r, p_value = stats.pearsonr(complexities, errors)
    
    interpretation = "No correlation"
    if r > 0.7:
        interpretation = "Strong positive correlation"
    elif r > 0.3:
        interpretation = "Moderate positive correlation"
    elif r < -0.7:
        interpretation = "Strong negative correlation"
    elif r < -0.3:
        interpretation = "Moderate negative correlation"
    
    return {
        'pearson_r': float(r),
        'p_value': float(p_value),
        'interpretation': interpretation,
        'sample_size': len(complexities)
    }

def calculate_aspect_ratio_summary(poses_data: List[Dict]) -> Dict[str, Any]:
    """Calculate aspect ratio validation results (SC-003)."""
    if not poses_data:
        return {
            'total_validated': 0,
            'passed': 0,
            'failed': 0,
            'pass_rate': 0.0,
            'details': []
        }
    
    passed = 0
    failed = 0
    details = []
    
    for seq in poses_data:
        if 'aspect_ratio_validated' in seq:
            is_valid = seq['aspect_ratio_validated']
            if is_valid:
                passed += 1
            else:
                failed += 1
            details.append({
                'sequence_id': seq.get('sequence_id', 'unknown'),
                'valid': is_valid,
                'estimated_ar': seq.get('estimated_aspect_ratio', 'N/A'),
                'expected_ar': seq.get('expected_aspect_ratio', 'N/A')
            })
    
    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0.0
    
    return {
        'total_validated': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': pass_rate,
        'details': details[:10]  # Limit to first 10 for report
    }

def generate_report(data: Dict[str, Any], output_path: Path) -> None:
    """Generate the final markdown report."""
    
    # Calculate all metrics
    error_summary = calculate_error_summary(data['poses'])
    correlation_summary = calculate_correlation_summary(data['poses'])
    aspect_ratio_summary = calculate_aspect_ratio_summary(data['poses'])
    
    # SC-004: Filter Rate
    total_sequences = len(data['filtered']) if data['filtered'] else 0
    # Filter rate is calculated in results if available
    filter_rate = 0.0
    if data['results'] and 'filtering_success_rate' in data['results']:
        filter_rate = float(data['results']['filtering_success_rate'])
    
    # SC-005: Timing
    execution_time = "N/A"
    if data['results'] and 'execution_time_seconds' in data['results']:
        execution_time = format_duration(float(data['results']['execution_time_seconds']))
    
    # Build report content
    report_lines = [
        "# OmniDirector Statistical Analysis Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## SC-001: Reconstruction Error Analysis",
        "",
        "This section reports the reconstruction error statistics across all processed sequences.",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Mean Error | {error_summary['mean_error']:.4f} |",
        f"| Median Error | {error_summary['median_error']:.4f} |",
        f"| Standard Deviation | {error_summary['std_error']:.4f} |",
        f"| Max Error | {error_summary['max_error']:.4f} |",
        f"| Min Error | {error_summary['min_error']:.4f} |",
        f"| Total Sequences Analyzed | {error_summary['total_sequences']} |",
        "",
        "### Error Distribution",
        "",
        "| Range | Count |",
        "|-------|-------|",
    ]
    
    for range_key, count in error_summary['error_distribution'].items():
        report_lines.append(f"| {range_key} | {count} |")
    
    report_lines.extend([
        "",
        "---",
        "",
        "## SC-002: Correlation Analysis",
        "",
        "Analysis of the relationship between camera motion complexity and reconstruction accuracy.",
        "",
        f"- **Pearson's r**: {correlation_summary['pearson_r'] if correlation_summary['pearson_r'] is not None else 'N/A'}",
        f"- **P-value**: {correlation_summary['p_value'] if correlation_summary['p_value'] is not None else 'N/A'}",
        f"- **Interpretation**: {correlation_summary['interpretation']}",
        f"- **Sample Size**: {correlation_summary['sample_size']}",
        "",
        "---",
        "",
        "## SC-003: Aspect Ratio Validation",
        "",
        "Validation of reconstructed bounding box aspect ratios against known ground truth (±5% tolerance).",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Validated | {aspect_ratio_summary['total_validated']} |",
        f"| Passed | {aspect_ratio_summary['passed']} |",
        f"| Failed | {aspect_ratio_summary['failed']} |",
        f"| Pass Rate | {aspect_ratio_summary['pass_rate']:.2f}% |",
        "",
        "### Sample Results (First 10)",
        "",
        "| Sequence ID | Valid | Estimated AR | Expected AR |",
        "|-------------|-------|--------------|-------------|",
    ])
    
    for detail in aspect_ratio_summary['details']:
        report_lines.append(
            f"| {detail['sequence_id']} | {'✓' if detail['valid'] else '✗'} | "
            f"{detail['estimated_ar']} | {detail['expected_ar']} |"
        )
    
    report_lines.extend([
        "",
        "---",
        "",
        "## SC-004: Dataset Filtering Success Rate",
        "",
        "Percentage of sequences retained after geometric filtering (FR-001).",
        "",
        f"- **Total Sequences**: {total_sequences}",
        f"- **Filtering Success Rate**: {filter_rate:.2f}%",
        "",
        "---",
        "",
        "## SC-005: Execution Timing",
        "",
        "Total pipeline execution time.",
        "",
        f"- **Execution Time**: {execution_time}",
        "",
        "---",
        "",
        "## Summary",
        "",
        "This report summarizes the statistical validation of the OmniDirector camera cloning pipeline.",
        "Key findings:",
        "",
        f"1. Reconstruction errors are distributed with a mean of {error_summary['mean_error']:.4f}.",
        f"2. {'A significant' if correlation_summary['pearson_r'] and abs(correlation_summary['pearson_r']) > 0.3 else 'No significant'} "
        f"correlation was found between camera complexity and reconstruction accuracy.",
        f"3. Aspect ratio validation passed for {aspect_ratio_summary['pass_rate']:.2f}% of sequences.",
        f"4. The filtering process retained {filter_rate:.2f}% of input sequences.",
        f"5. Total pipeline execution completed in {execution_time}.",
        "",
        "---",
        "",
        "*Report generated by llmXive automated science pipeline*"
    ])
    
    # Write report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Report generated successfully: {output_path}")

def main():
    """Main entry point for report generation."""
    config = load_config()
    output_path = get_path('report', config)
    
    logger.info(f"Starting report generation. Output: {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    data = load_results_data()
    
    # Generate report
    generate_report(data, output_path)
    
    logger.info("Report generation completed.")
    return 0

if __name__ == '__main__':
    exit(main())