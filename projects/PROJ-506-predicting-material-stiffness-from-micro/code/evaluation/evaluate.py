"""
Evaluation script for the stiffness prediction model.

Computes MAE, MSE, R2 metrics and generates analysis reports.
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from code.evaluation.stats_utils import compute_one_way_anova, compute_degradation_rate
from code.utils.metrics import mean_absolute_error, mean_squared_error, r2_score

def load_predictions(predictions_file: Path) -> np.ndarray:
    """Load model predictions from JSON file."""
    with open(predictions_file, 'r') as f:
        data = json.load(f)
    return np.array(data)

def load_ground_truth(ground_truth_file: Path) -> np.ndarray:
    """Load ground truth stiffness tensors from JSON file."""
    with open(ground_truth_file, 'r') as f:
        data = json.load(f)
    return np.array(data)

def compute_errors(
    predictions: np.ndarray,
    ground_truth: np.ndarray
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Compute prediction errors and summary metrics.
    
    Args:
        predictions: Array of predictions
        ground_truth: Array of ground truth values
        
    Returns:
        Tuple of (element-wise errors, summary metrics dictionary)
    """
    # Flatten for scalar error calculation
    pred_flat = predictions.flatten()
    true_flat = ground_truth.flatten()
    
    # Element-wise absolute errors
    element_errors = np.abs(pred_flat - true_flat)
    
    # Summary metrics
    mae = mean_absolute_error(true_flat, pred_flat)
    mse = mean_squared_error(true_flat, pred_flat)
    r2 = r2_score(true_flat, pred_flat)
    
    metrics = {
        'mae': mae,
        'mse': mse,
        'r2': r2,
        'n_samples': len(pred_flat)
    }
    
    return element_errors, metrics

def generate_report(
    metrics: Dict[str, float],
    errors_by_density: Dict[str, List[float]],
    anova_results: Tuple[float, float],
    degradation_rate: float,
    output_path: Path
) -> None:
    """
    Generate markdown analysis report.
    
    Args:
        metrics: Summary metrics dictionary
        errors_by_density: Errors grouped by density bin
        anova_results: Tuple of (F-statistic, p-value)
        degradation_rate: Computed degradation rate
        output_path: Path to save report
    """
    report_lines = [
        "# Model Evaluation Report",
        "",
        "## Summary Metrics",
        f"- Mean Absolute Error (MAE): {metrics['mae']:.4f}",
        f"- Mean Squared Error (MSE): {metrics['mse']:.4f}",
        f"- R-squared (R2): {metrics['r2']:.4f}",
        f"- Number of Samples: {metrics['n_samples']}",
        "",
        "## Error Distribution by Density",
        ""
    ]
    
    for density_bin, errors in errors_by_density.items():
        avg_error = np.mean(errors)
        report_lines.append(f"- **{density_bin}**: Avg Error = {avg_error:.4f}")
    
    report_lines.extend([
        "",
        "## Statistical Analysis",
        f"- One-way ANOVA F-statistic: {anova_results[0]:.4f}",
        f"- One-way ANOVA p-value: {anova_results[1]:.4f}",
        f"- Degradation Rate (OOD): {degradation_rate:.4f} MAE per % density",
        ""
    ])
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def main(args) -> int:
    """
    Main entry point for evaluation.
    
    Args:
        args: Namespace with predictions_file, ground_truth_file, metadata_file
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Load data
        logger.info("Loading predictions and ground truth...")
        predictions = load_predictions(Path(args.predictions_file))
        ground_truth = load_ground_truth(Path(args.ground_truth_file))
        
        with open(args.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Compute errors
        logger.info("Computing errors...")
        element_errors, metrics = compute_errors(predictions, ground_truth)
        
        logger.info(f"MAE: {metrics['mae']:.4f}, MSE: {metrics['mse']:.4f}, R2: {metrics['r2']:.4f}")
        
        # Group errors by density bin
        density_bins = {'low': [], 'medium': [], 'high': []}
        densities = [m['inclusion_density'] for m in metadata]
        
        for i, density in enumerate(densities):
            # Calculate average error for this sample (across tensor elements)
            sample_error = np.mean(element_errors[i*4:(i+1)*4])
            
            if density < 0.2:
                density_bins['low'].append(sample_error)
            elif density < 0.4:
                density_bins['medium'].append(sample_error)
            else:
                density_bins['high'].append(sample_error)
        
        # Perform ANOVA
        logger.info("Performing statistical analysis...")
        f_stat, p_value = compute_one_way_anova(density_bins)
        
        # Compute degradation rate
        max_density = max(densities)
        deg_rate = compute_degradation_rate(
            np.array(densities),
            np.array([np.mean(element_errors[i*4:(i+1)*4]) for i in range(len(densities))]),
            max_density
        )
        
        # Generate report
        report_path = Path(args.report_file)
        generate_report(
            metrics=metrics,
            errors_by_density=density_bins,
            anova_results=(f_stat, p_value),
            degradation_rate=deg_rate,
            output_path=report_path
        )
        
        logger.info(f"Report saved to {report_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate stiffness prediction model")
    parser.add_argument("--predictions_file", type=str, default="data/processed/predictions.json")
    parser.add_argument("--ground_truth_file", type=str, default="data/processed/ground_truth.json")
    parser.add_argument("--metadata_file", type=str, default="data/raw/metadata.json")
    parser.add_argument("--report_file", type=str, default="data/processed/analysis_report.md")
    args = parser.parse_args()
    exit(main(args))
