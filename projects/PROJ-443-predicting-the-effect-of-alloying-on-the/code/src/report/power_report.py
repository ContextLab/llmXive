"""
Power Analysis and Underpowered Study Report Generation.

This module implements the logic for detecting underpowered studies (sample count < 500)
and generating a detailed report quantifying the power deficit, replacing hard halt logic.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import yaml

# Import from project utilities
from src.utils.logging_config import get_logger

# Constants
MIN_SAMPLE_THRESHOLD = 500
DEFAULT_CONFIDENCE_LEVEL = 0.95
DEFAULT_EFFECT_SIZE = 0.5  # Cohen's d equivalent for rough estimation

logger = get_logger(__name__)


def calculate_power_deficit(
    current_samples: int,
    threshold: int = MIN_SAMPLE_THRESHOLD,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
    effect_size: float = DEFAULT_EFFECT_SIZE
) -> Dict[str, Any]:
    """
    Calculate the power deficit metrics for an underpowered study.

    Args:
        current_samples: The number of samples currently retrieved.
        threshold: The minimum required sample count (default 500).
        confidence_level: The desired confidence level (default 0.95).
        effect_size: Estimated effect size for power calculation (default 0.5).

    Returns:
        A dictionary containing:
            - deficit_ratio: current_samples / threshold
            - confidence_interval_widening: Estimated factor by which CI widens
            - power_loss_percent: Estimated percentage loss in statistical power
            - recommended_additional_samples: How many more samples are needed
    """
    if current_samples <= 0:
        return {
            "deficit_ratio": 0.0,
            "confidence_interval_widening": float('inf'),
            "power_loss_percent": 100.0,
            "recommended_additional_samples": threshold,
            "status": "critical"
        }

    deficit_ratio = current_samples / threshold
    recommended_additional = max(0, threshold - current_samples)

    # Approximation for CI widening: CI width is proportional to 1/sqrt(n)
    # Widening factor = sqrt(threshold) / sqrt(current_samples)
    ci_widening_factor = (threshold / current_samples) ** 0.5

    # Approximation for power loss (simplified model)
    # If power at N=500 is ~0.80, power at N=x drops roughly with sqrt(x/500)
    # This is a heuristic for reporting purposes
    estimated_power_at_threshold = 0.80
    estimated_current_power = estimated_power_at_threshold * (current_samples / threshold) ** 0.5
    power_loss = max(0, (estimated_power_at_threshold - estimated_current_power) / estimated_power_at_threshold * 100)

    status = "critical" if deficit_ratio < 0.5 else "warning"

    return {
        "deficit_ratio": round(deficit_ratio, 4),
        "confidence_interval_widening": round(ci_widening_factor, 4),
        "power_loss_percent": round(power_loss, 2),
        "recommended_additional_samples": recommended_additional,
        "status": status
    }


def generate_power_report(
    current_samples: int,
    threshold: int = MIN_SAMPLE_THRESHOLD,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive Underpowered Study Report.

    This function is called when the sample count falls below the threshold.
    It logs the specific deficit message and generates a report quantifying the deficit.

    Args:
        current_samples: The number of samples retrieved.
        threshold: The minimum required sample count.
        output_path: Optional path to write the report YAML file.

    Returns:
        The report dictionary.
    """
    logger.warning(f"Retrieved {current_samples} samples; threshold not met. Proceeding with Reduced Power Analysis")

    timestamp = datetime.utcnow().isoformat()
    deficit_metrics = calculate_power_deficit(current_samples, threshold)

    report = {
        "report_type": "Underpowered Study Report",
        "timestamp": timestamp,
        "sample_statistics": {
            "current_count": current_samples,
            "required_threshold": threshold,
            "shortfall": max(0, threshold - current_samples)
        },
        "power_analysis": deficit_metrics,
        "impact_assessment": {
            "confidence_interval_note": f"Confidence intervals may be widened by a factor of ~{deficit_metrics['confidence_interval_widening']:.2f}",
            "statistical_power_note": f"Estimated statistical power reduced by ~{deficit_metrics['power_loss_percent']:.1f}%",
            "recommendation": "Interpret results with caution. Consider data augmentation or literature synthesis if additional samples cannot be acquired."
        },
        "proceeding_flag": True,
        "message": f"Retrieved {current_samples} samples; threshold not met. Proceeding with Reduced Power Analysis"
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Power report written to {output_path}")

    return report


def main():
    """
    CLI entry point for testing the power report generation.
    Usage: python -m src.report.power_report --samples <count> --output <path>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate Underpowered Study Report")
    parser.add_argument("--samples", type=int, required=True, help="Number of samples retrieved")
    parser.add_argument("--threshold", type=int, default=MIN_SAMPLE_THRESHOLD, help="Minimum sample threshold")
    parser.add_argument("--output", type=str, help="Output path for the report YAML")

    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None

    report = generate_power_report(
        current_samples=args.samples,
        threshold=args.threshold,
        output_path=output_path
    )

    print("\n--- Underpowered Study Report ---")
    print(yaml.dump(report, default_flow_style=False))

    if report["proceeding_flag"]:
        print("\n[INFO] System proceeding with reduced power analysis.")
        sys.exit(0)
    else:
        print("\n[ERROR] System halted due to insufficient power.")
        sys.exit(1)


if __name__ == "__main__":
    main()