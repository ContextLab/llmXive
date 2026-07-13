"""
Evaluation script for the material stiffness prediction model.
Loads predictions and ground truth, computes errors, and generates reports.
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from code.evaluation.stats_utils import compute_one_way_anova, compute_degradation_rate

def load_predictions(predictions_path: Path) -> Dict:
    """Load model predictions from JSON file."""
    with open(predictions_path, 'r') as f:
        return json.load(f)

def load_ground_truth(ground_truth_path: Path) -> Dict:
    """Load ground truth data from JSON file."""
    with open(ground_truth_path, 'r') as f:
        return json.load(f)

def compute_errors(predictions: Dict, ground_truth: Dict) -> Dict[str, np.ndarray]:
    """
    Compute prediction errors.
    
    Args:
        predictions: Dictionary containing model predictions
        ground_truth: Dictionary containing ground truth values
        
    Returns:
        Dictionary with error metrics
    """
    pred_values = np.array(predictions['predictions'])
    truth_values = np.array(ground_truth['stiffness_values'])
    
    errors = {
        'absolute_error': np.abs(pred_values - truth_values),
        'squared_error': (pred_values - truth_values) ** 2,
        'relative_error': np.abs((pred_values - truth_values) / truth_values)
    }
    
    return errors

def generate_report(errors: Dict, output_path: Path, metadata: Dict = None):
    """
    Generate evaluation report.
    
    Args:
        errors: Dictionary of computed errors
        output_path: Path to save the report
        metadata: Optional metadata to include in the report
    """
    report_lines = [
        "# Model Evaluation Report",
        "",
        "## Error Metrics",
        f"- Mean Absolute Error (MAE): {np.mean(errors['absolute_error']):.6f}",
        f"- Mean Squared Error (MSE): {np.mean(errors['squared_error']):.6f}",
        f"- Mean Relative Error: {np.mean(errors['relative_error']):.6f}",
        ""
    ]
    
    if metadata:
        report_lines.append("## Metadata")
        for key, value in metadata.items():
            report_lines.append(f"- {key}: {value}")
        report_lines.append("")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def main():
    """CLI entry point for evaluation."""
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate model predictions")
    parser.add_argument("--predictions", type=str, required=True, help="Path to predictions JSON")
    parser.add_argument("--ground_truth", type=str, required=True, help="Path to ground truth JSON")
    parser.add_argument("--output", type=str, default="data/processed/evaluation_report.md", help="Output report path")
    args = parser.parse_args()
    
    predictions_path = Path(args.predictions)
    ground_truth_path = Path(args.ground_truth)
    output_path = Path(args.output)
    
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    if not ground_truth_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {ground_truth_path}")
        
    predictions = load_predictions(predictions_path)
    ground_truth = load_ground_truth(ground_truth_path)
    
    errors = compute_errors(predictions, ground_truth)
    generate_report(errors, output_path)
    
    print(f"Evaluation report generated: {output_path}")

if __name__ == "__main__":
    main()
