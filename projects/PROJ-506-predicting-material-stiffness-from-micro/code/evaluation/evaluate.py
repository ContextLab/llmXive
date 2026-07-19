"""
Evaluation Script for Stiffness Prediction Model.

Loads predictions and ground truth, computes errors, and generates reports.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from code.evaluation.stats_utils import compute_one_way_anova, compute_degradation_rate

def load_predictions(predictions_path: Path) -> List[float]:
    """
    Load model predictions from file.

    Args:
        predictions_path: Path to JSON file containing predictions.

    Returns:
        List of predicted values.
    """
    with open(predictions_path, 'r') as f:
        data = json.load(f)
    return data['predictions']

def load_ground_truth(metadata_path: Path) -> Tuple[List[float], List[float]]:
    """
    Load ground truth stiffness and density from metadata.

    Args:
        metadata_path: Path to JSON file containing metadata.

    Returns:
        Tuple of (stiffness_values, densities).
    """
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    stiffness = [sample['stiffness'] for sample in data['samples']]
    densities = [sample['inclusion_density'] for sample in data['samples']]
    return stiffness, densities

def compute_errors(
    predictions: List[float],
    ground_truth: List[float]
) -> Dict[str, float]:
    """
    Compute error metrics between predictions and ground truth.

    Args:
        predictions: List of predicted values.
        ground_truth: List of actual values.

    Returns:
        Dictionary of error metrics (MAE, MSE, R2).
    """
    preds = np.array(predictions)
    truths = np.array(ground_truth)
    
    mae = np.mean(np.abs(preds - truths))
    mse = np.mean((preds - truths) ** 2)
    
    ss_res = np.sum((truths - preds) ** 2)
    ss_tot = np.sum((truths - np.mean(truths)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return {
        'mae': float(mae),
        'mse': float(mse),
        'r2': float(r2)
    }

def generate_report(
    errors: Dict[str, float],
    anova_results: Tuple[float, float],
    degradation_rate: float,
    output_path: Path
) -> None:
    """
    Generate evaluation report and save to file.

    Args:
        errors: Dictionary of error metrics.
        anova_results: Tuple of (F-statistic, p-value) from ANOVA.
        degradation_rate: Computed degradation rate for OOD data.
        output_path: Path to save the report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_lines = [
        "# Model Evaluation Report",
        "",
        "## Error Metrics",
        f"- MAE: {errors['mae']:.4f}",
        f"- MSE: {errors['mse']:.4f}",
        f"- R2: {errors['r2']:.4f}",
        "",
        "## Statistical Analysis",
        f"- ANOVA F-statistic: {anova_results[0]:.4f}",
        f"- ANOVA p-value: {anova_results[1]:.4f}",
        "",
        "## Generalization",
        f"- Degradation Rate: {degradation_rate:.4f} MAE per % density",
        ""
    ]
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def main():
    """Main evaluation entry point."""
    print("Evaluation script loaded.")
