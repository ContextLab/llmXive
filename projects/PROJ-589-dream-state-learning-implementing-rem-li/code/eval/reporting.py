"""
Result reporting module for Dream-State Learning project.
Generates comparative reports between experimental (Wake/Dream) and baseline runs.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

def save_comparison_report(
    experimental_results: Dict[str, Any],
    baseline_results: Dict[str, Any],
    statistical_analysis: Dict[str, Any],
    config: Config,
    output_path: Optional[str] = None
) -> str:
    """
    Save a comprehensive comparative report to JSON.

    Args:
        experimental_results: Dict containing metrics from the Wake/Dream run
            (e.g., {'final_accuracy': 0.85, 'final_loss': 0.42, 'seeds': [0.85, 0.84, ...]})
        baseline_results: Dict containing metrics from the continuous SFT baseline
        statistical_analysis: Dict containing statistical test results
            (e.g., {'p_value': 0.03, 'method': 'wilcoxon', 'significant': True})
        config: Config object containing experiment metadata
        output_path: Optional custom output path. Defaults to config.report_output_path.

    Returns:
        str: The path to the saved report file.
    """
    if output_path is None:
        output_path = config.report_output_path

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    report = {
        "metadata": {
            "experiment_name": config.experiment_name,
            "timestamp": datetime.now().isoformat(),
            "config_seed": config.seed,
            "model_name": config.model_name,
            "dataset": config.dataset_name,
            "total_steps": config.total_steps,
            "wake_dream_ratio": config.wake_dream_ratio,
        },
        "experimental_run": {
            "type": "wake_dream_cycle",
            "metrics": experimental_results,
        },
        "baseline_run": {
            "type": "continuous_sft",
            "metrics": baseline_results,
        },
        "statistical_comparison": {
            "method": "wilcoxon_signed_rank",
            "alpha": 0.05,
            **statistical_analysis
        },
        "conclusion": {
            "significant_difference": statistical_analysis.get("significant", False),
            "p_value": statistical_analysis.get("p_value", None),
            "interpretation": generate_interpretation(statistical_analysis)
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Comparison report saved to: {output_path}")
    return output_path

def generate_interpretation(stats: Dict[str, Any]) -> str:
    """
    Generate a human-readable interpretation of the statistical results.
    """
    p_value = stats.get("p_value")
    significant = stats.get("significant", False)

    if p_value is None:
        return "Statistical comparison could not be performed (missing p-value)."

    if significant:
        return (
            f"Statistically significant difference detected (p={p_value:.4f} < 0.05). "
            "The Wake/Dream consolidation strategy yields a different performance profile "
            "compared to continuous SFT."
        )
    else:
        return (
            f"No statistically significant difference detected (p={p_value:.4f} >= 0.05). "
            "Performance between Wake/Dream and continuous SFT is comparable within the "
            "observed variance."
        )

def load_report(report_path: str) -> Dict[str, Any]:
    """
    Load a previously saved comparison report.
    """
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Report not found at {report_path}")

    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)
