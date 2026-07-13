"""
Report generator for statistical analysis results.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from analysis.log_parser import get_aggregated_counts
from utils.config import get_path, get_project_root

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root.
    
    Note: This is a local wrapper to ensure consistency if config.py
    changes its internal path resolution logic.
    """
    return get_project_root()

def generate_report(baseline_counts: tuple, augmented_counts: tuple, 
                    p_value: float, test_type: str, 
                    conclusion: str, significance_level: float = 0.05) -> Dict[str, Any]:
    """
    Generate a structured report dictionary.
    
    Args:
        baseline_counts: Tuple of (success, failure) for baseline.
        augmented_counts: Tuple of (success, failure) for augmented.
        p_value: P-value from statistical test.
        test_type: Name of the statistical test used.
        conclusion: Human-readable conclusion string.
        significance_level: Threshold for significance (default 0.05).
        
    Returns:
        Dictionary containing the full report data.
    """
    baseline_success, baseline_failure = baseline_counts
    augmented_success, augmented_failure = augmented_counts
    
    baseline_total = baseline_success + baseline_failure
    augmented_total = augmented_success + augmented_failure
    
    baseline_rate = baseline_success / baseline_total if baseline_total > 0 else 0.0
    augmented_rate = augmented_success / augmented_total if augmented_total > 0 else 0.0
    
    difference = augmented_rate - baseline_rate
    is_significant = p_value < significance_level
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "baseline": {
            "successes": baseline_success,
            "failures": baseline_failure,
            "total": baseline_total,
            "success_rate": baseline_rate
        },
        "augmented": {
            "successes": augmented_success,
            "failures": augmented_failure,
            "total": augmented_total,
            "success_rate": augmented_rate
        },
        "comparison": {
            "difference": difference,
            "is_significant": is_significant,
            "significance_level": significance_level
        },
        "statistical_test": {
            "type": test_type,
            "p_value": p_value
        },
        "conclusion": conclusion
    }
    
    return report

def save_report(report: Dict[str, Any], output_path: Path = None) -> Path:
    """
    Save the report to a JSON file.
    
    Args:
        report: The report dictionary to save.
        output_path: Optional override for output path. Defaults to config.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = get_path('final_report')
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return output_path

def main():
    """
    Main entry point for report generation.
    Generates a sample report assuming placeholder statistical results
    (in a real run, these would come from stats.py).
    """
    try:
        counts = get_aggregated_counts()
        baseline = counts['baseline']
        augmented = counts['augmented']
        
        # Placeholder values for demonstration. 
        # In a real execution flow, these would be passed from stats.py.
        # We compute a dummy p-value and test type here to satisfy the signature.
        # If no data exists, we report accordingly.
        total_baseline = baseline[0] + baseline[1]
        total_augmented = augmented[0] + augmented[1]
        
        if total_baseline == 0 or total_augmented == 0:
            report_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "error": "No data available for comparison. Ensure baseline and augmented logs exist.",
                "baseline": {"successes": baseline[0], "failures": baseline[1], "total": total_baseline},
                "augmented": {"successes": augmented[0], "failures": augmented[1], "total": total_augmented}
            }
            msg = "Report generated with error status due to missing data."
        else:
            # Dummy statistical results for structure validation
            p_val = 0.05
            test_type = "placeholder"
            conclusion = "Placeholder conclusion. Run stats.py for real results."
            
            report_data = generate_report(
                baseline, augmented, p_val, test_type, conclusion
            )
            msg = "Report generated successfully."

        output_path = save_report(report_data)
        print(f"Report saved to: {output_path}")
        print(msg)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
