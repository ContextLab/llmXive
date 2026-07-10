"""
Power Analysis and Underpowered Study Report Generation.

This module implements the logic to generate an 'Underpowered Study Report'
when the retrieved sample count is below the required threshold (500).
It replaces the previous hard-halt logic with a warning and quantification
of the power deficit, allowing the pipeline to proceed with Reduced Power Analysis.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import numpy as np
import pandas as pd
import yaml

# Add project root to path for imports if running as script
if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import get_logger
from utils.seeds import get_seed

# Configuration constants
SAMPLE_THRESHOLD = 500
CONFIDENCE_LEVEL = 0.95
EFFECT_SIZE_ESTIMATE = 0.3  # Cohen's d equivalent for correlation
ALPHA = 0.05

logger = get_logger(__name__)


def calculate_power_deficit(
    current_n: int,
    target_n: int = SAMPLE_THRESHOLD,
    alpha: float = ALPHA,
    power_target: float = 0.80,
    effect_size: float = EFFECT_SIZE_ESTIMATE
) -> Dict[str, float]:
    """
    Quantifies the power deficit and estimates the widening of confidence intervals.

    Args:
        current_n: The actual number of samples retrieved.
        target_n: The target sample size for full power.
        alpha: Significance level.
        power_target: Desired statistical power (typically 0.80).
        effect_size: Estimated effect size (Cohen's d or similar).

    Returns:
        A dictionary containing power deficit metrics.
    """
    if current_n <= 0:
        return {
            "power": 0.0,
            "ci_width_factor": float('inf'),
            "sample_deficit": target_n,
            "status": "critical"
        }

    # Approximate power calculation for correlation/t-test
    # Using simplified approximation: Power ~ Phi( sqrt(n)*d - z_alpha )
    # where d is effect size, z_alpha is critical value
    z_alpha = 1.96  # Approx for 0.05 two-tailed
    z_beta = 0.84   # Approx for 0.80 power

    # Current power estimate (simplified)
    # Non-centrality parameter lambda = sqrt(n) * effect_size
    lambda_current = np.sqrt(current_n) * effect_size
    power_current = 0.5 * (1 + np.math.erf((lambda_current - z_alpha) / np.sqrt(2)))
    power_current = max(0.0, min(1.0, power_current))

    # CI Width is proportional to 1/sqrt(n)
    # Factor by which CI is wider compared to target_n
    ci_width_factor = np.sqrt(target_n) / np.sqrt(current_n) if current_n > 0 else float('inf')

    sample_deficit = target_n - current_n

    status = "adequate"
    if power_current < 0.5:
        status = "critical"
    elif power_current < 0.8:
        status = "underpowered"

    return {
        "power": float(power_current),
        "ci_width_factor": float(ci_width_factor),
        "sample_deficit": int(sample_deficit),
        "status": status
    }


def generate_power_report(
    sample_count: int,
    source_info: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generates the Underpowered Study Report.

    Args:
        sample_count: The number of samples retrieved.
        source_info: Dictionary containing source metadata (optional).
        output_path: Path to save the report (optional).

    Returns:
        The report dictionary.
    """
    report_data = {
        "report_type": "Underpowered Study Report",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "threshold_met": sample_count >= SAMPLE_THRESHOLD,
        "sample_count": sample_count,
        "threshold_value": SAMPLE_THRESHOLD,
    }

    if not report_data["threshold_met"]:
        # Log the specific deficit message required by spec
        deficit_msg = f"Retrieved {sample_count} samples; threshold not met. Proceeding with Reduced Power Analysis"
        logger.warning(deficit_msg)
        report_data["deficit_message"] = deficit_msg

        # Calculate power metrics
        power_metrics = calculate_power_deficit(sample_count)
        report_data["power_analysis"] = power_metrics

        # Estimate impact on confidence intervals
        report_data["confidence_interval_impact"] = {
            "description": "Confidence intervals will be wider than planned.",
            "width_multiplier": power_metrics["ci_width_factor"],
            "interpretation": f"95% CIs are approximately {power_metrics['ci_width_factor']:.2f}x wider than with {SAMPLE_THRESHOLD} samples."
        }

        # Recommendations for reduced power analysis
        report_data["recommendations"] = [
            "Interpret model performance metrics with caution due to reduced statistical power.",
            "Prioritize effect size estimation over strict p-value thresholds.",
            "Consider bootstrapping with caution (potential underestimation of CI width).",
            "Flag all conclusions as preliminary pending larger dataset validation."
        ]
    else:
        logger.info(f"Sample count {sample_count} meets threshold of {SAMPLE_THRESHOLD}.")
        report_data["power_analysis"] = {
            "status": "adequate",
            "power": 1.0,
            "ci_width_factor": 1.0
        }
        report_data["recommendations"] = ["Proceed with standard analysis."]

    if source_info:
        report_data["data_source"] = source_info

    # Write to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(report_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Power report saved to {output_path}")

    return report_data


def main():
    """
    Main entry point for the power report generation.
    Can be called standalone or imported by the pipeline.
    """
    # Mock data for demonstration if run directly without context
    # In a real pipeline, this would receive data from the fetcher
    logger.info("Starting Power Report Generation")

    # Example: Simulate a low sample count scenario
    simulated_count = 150
    source_info = {
        "primary_source": "OQMD",
        "query_params": {"min_elements": 5},
        "timestamp": datetime.utcnow().isoformat()
    }

    report = generate_power_report(
        sample_count=simulated_count,
        source_info=source_info,
        output_path=Path("data/reports/power_analysis_report.yaml")
    )

    # Print summary to stdout
    print("\n--- Power Analysis Summary ---")
    print(f"Samples Retrieved: {report['sample_count']}")
    print(f"Threshold Met: {report['threshold_met']}")
    if not report['threshold_met']:
        print(f"Status: {report['power_analysis']['status'].upper()}")
        print(f"Power: {report['power_analysis']['power']:.2%}")
        print(f"CI Width Multiplier: {report['power_analysis']['ci_width_factor']:.2f}x")
        print(f"Message: {report['deficit_message']}")
    print("------------------------------\n")

    return report


if __name__ == "__main__":
    main()