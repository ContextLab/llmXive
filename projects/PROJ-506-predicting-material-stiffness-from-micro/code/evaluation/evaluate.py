"""
Evaluation script for model performance.
Computes errors, performs statistical analysis, and generates reports.
"""
import json
import numpy as np
from pathlib import Path
from code.evaluation.stats_utils import compute_one_way_anova, compute_degradation_rate

def load_predictions(predictions_path: Path):
    """Load model predictions."""
    with open(predictions_path, 'r') as f:
        return json.load(f)

def load_ground_truth(metadata_path: Path):
    """Load ground truth stiffness values."""
    with open(metadata_path, 'r') as f:
        return json.load(f)

def compute_errors(predictions, ground_truth) -> List[Dict]:
    """Compute prediction errors."""
    errors = []
    for pred, truth in zip(predictions, ground_truth):
        # Compute MAE for stiffness tensor
        pred_tensor = np.array(pred['prediction'])
        true_tensor = np.array(truth['stiffness_tensor'])
        mae = np.mean(np.abs(pred_tensor - true_tensor))
        
        errors.append({
            "seed": pred['seed'],
            "density": pred['density'],
            "mae": float(mae),
            "prediction": pred['prediction'],
            "ground_truth": truth['stiffness_tensor']
        })
    return errors

def generate_report(errors: List[Dict], output_path: Path):
    """Generate analysis report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Bin by density
    density_bins = {}
    for err in errors:
        density = err['density']
        if density < 0.2:
            bin_name = "low"
        elif density < 0.4:
            bin_name = "medium"
        else:
            bin_name = "high"
        
        if bin_name not in density_bins:
            density_bins[bin_name] = []
        density_bins[bin_name].append(err['mae'])
    
    # ANOVA test
    f_stat, p_val = compute_one_way_anova(density_bins)
    
    # Degradation rate (for OOD analysis)
    ood_densities = [e['density'] for e in errors if e['density'] > 0.4]
    ood_errors = [e['mae'] for e in errors if e['density'] > 0.4]
    degradation_rate = compute_degradation_rate(ood_densities, ood_errors) if ood_densities else 0.0
    
    # Write report
    with open(output_path, 'w') as f:
        f.write("# Model Evaluation Report\n\n")
        f.write("## Statistical Analysis\n")
        f.write(f"One-way ANOVA: F={f_stat:.4f}, p-value={p_val:.4f}\n\n")
        f.write("## Error by Density Bin\n")
        for bin_name, mae_list in density_bins.items():
            f.write(f"- {bin_name}: Mean MAE = {np.mean(mae_list):.4f}\n")
        f.write(f"\n## Degradation Rate\n")
        f.write(f"OOD Degradation Rate: {degradation_rate:.6f} MAE per % density\n")

def main():
    """CLI entry point for evaluation."""
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate model performance")
    parser.add_argument("--predictions", type=str, default="data/processed/predictions.json", help="Predictions file")
    parser.add_argument("--metadata", type=str, default="data/raw/stiffness_metadata.json", help="Ground truth metadata")
    parser.add_argument("--output", type=str, default="data/processed/analysis_report.md", help="Output report")
    args = parser.parse_args()
    
    predictions_path = Path(args.predictions)
    metadata_path = Path(args.metadata)
    output_path = Path(args.output)
    
    if not predictions_path.exists() or not metadata_path.exists():
        print("Error: Predictions or metadata file not found. Run training first.")
        return 1
    
    predictions = load_predictions(predictions_path)
    ground_truth = load_ground_truth(metadata_path)
    
    errors = compute_errors(predictions, ground_truth)
    generate_report(errors, output_path)
    
    print(f"Evaluation report saved to {output_path}")
    return 0

if __name__ == "__main__":
    exit(main())
