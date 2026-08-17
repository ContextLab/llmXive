import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from code.evaluation.stats_utils import compute_one_way_anova, compute_degradation_rate
from code.utils.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_predictions(predictions_path: str) -> Dict[str, np.ndarray]:
    """Load model predictions from a JSON file."""
    path = Path(predictions_path)
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Expecting a list of dicts with 'seed', 'prediction', 'error'
    predictions = {}
    for entry in data:
        seed = entry['seed']
        predictions[seed] = np.array(entry['prediction'])
    return predictions

def load_ground_truth(ground_truth_path: str) -> Dict[str, np.ndarray]:
    """Load ground truth stiffness tensors from a JSON file."""
    path = Path(ground_truth_path)
    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {ground_truth_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Expecting a list of dicts with 'seed', 'stiffness_tensor'
    ground_truth = {}
    for entry in data:
        seed = entry['seed']
        ground_truth[seed] = np.array(entry['stiffness_tensor'])
    return ground_truth

def compute_errors(predictions: Dict[str, np.ndarray], ground_truth: Dict[str, np.ndarray]) -> List[Dict]:
    """Compute MAE, MSE, R2 for each sample and aggregate metrics."""
    results = []
    all_pred_values = []
    all_true_values = []

    common_seeds = set(predictions.keys()) & set(ground_truth.keys())
    if not common_seeds:
        raise ValueError("No common seeds found between predictions and ground truth.")

    for seed in common_seeds:
        pred = predictions[seed]
        true = ground_truth[seed]
        
        # Flatten for scalar metrics if necessary, or compute per component
        # Assuming stiffness tensor is flattened or we want a scalar error metric
        # For R2, we need 1D arrays. Let's flatten both.
        pred_flat = pred.flatten()
        true_flat = true.flatten()
        
        all_pred_values.extend(pred_flat)
        all_true_values.extend(true_flat)
        
        # Sample-level errors (using flattened arrays)
        sample_mae = mean_absolute_error(true_flat, pred_flat)
        sample_mse = mean_squared_error(true_flat, pred_flat)
        sample_r2 = r2_score(true_flat, pred_flat)
        
        results.append({
            "seed": seed,
            "mae": sample_mae,
            "mse": sample_mse,
            "r2": sample_r2
        })

    # Aggregate metrics over all data
    agg_mae = mean_absolute_error(np.array(all_true_values), np.array(all_pred_values))
    agg_mse = mean_squared_error(np.array(all_true_values), np.array(all_pred_values))
    agg_r2 = r2_score(np.array(all_true_values), np.array(all_pred_values))

    return results, {"mae": agg_mae, "mse": agg_mse, "r2": agg_r2}

def generate_report(results: List[Dict], aggregate: Dict, output_path: str, density_metadata: Dict[str, float] = None):
    """Generate a markdown report with evaluation metrics."""
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        f.write("# Model Evaluation Report\n\n")
        f.write("## Aggregate Metrics\n\n")
        f.write(f"- **Mean Absolute Error (MAE)**: {aggregate['mae']:.6f}\n")
        f.write(f"- **Mean Squared Error (MSE)**: {aggregate['mse']:.6f}\n")
        f.write(f"- **R-squared (R2)**: {aggregate['r2']:.6f}\n\n")
        
        f.write("## Per-Sample Results\n\n")
        f.write("| Seed | MAE | MSE | R2 |\n")
        f.write("|---|---|---|---|\n")
        for r in results:
            f.write(f"| {r['seed']} | {r['mae']:.6f} | {r['mse']:.6f} | {r['r2']:.6f} |\n")
        
        if density_metadata:
            f.write("\n## Statistical Analysis (Density Bins)\n\n")
            # Prepare data for ANOVA
            density_groups = {}
            for r in results:
                seed = r['seed']
                if seed in density_metadata:
                    density = density_metadata[seed]
                    # Bin density into categories (e.g., Low, Medium, High)
                    if density < 0.3:
                        bin_label = "Low"
                    elif density < 0.6:
                        bin_label = "Medium"
                    else:
                        bin_label = "High"
                    
                    if bin_label not in density_groups:
                        density_groups[bin_label] = []
                    density_groups[bin_label].append(r['mae'])
            
            if len(density_groups) > 1:
                groups = list(density_groups.values())
                group_names = list(density_groups.keys())
                
                f.write("### One-way ANOVA Results\n\n")
                anova_result = compute_one_way_anova(groups)
                f.write(f"- **F-statistic**: {anova_result['f_stat']:.4f}\n")
                f.write(f"- **P-value**: {anova_result['p_value']:.4f}\n")
                if anova_result['p_value'] < 0.05:
                    f.write("- **Conclusion**: Statistically significant difference in MAE across density bins (p < 0.05).\n")
                else:
                    f.write("- **Conclusion**: No statistically significant difference in MAE across density bins (p >= 0.05).\n")
                
                f.write("\n### Degradation Rate Analysis\n\n")
                # Compute degradation rate using the utility
                # We need to map seeds to densities and errors
                seed_to_density_error = {}
                for r in results:
                    if r['seed'] in density_metadata:
                        seed_to_density_error[r['seed']] = (density_metadata[r['seed']], r['mae'])
                
                degradation = compute_degradation_rate(seed_to_density_error)
                f.write(f"- **Degradation Rate**: {degradation['slope']:.6f} MAE per unit density\n")
                f.write(f"- **R-squared of degradation fit**: {degradation['r2']:.4f}\n")

def main():
    """Main entry point for evaluation script."""
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate CNN model on held-out test set.")
    parser.add_argument("--predictions", type=str, required=True, help="Path to predictions JSON file")
    parser.add_argument("--ground_truth", type=str, required=True, help="Path to ground truth JSON file")
    parser.add_argument("--metadata", type=str, required=False, help="Path to metadata JSON file for density info")
    parser.add_argument("--output", type=str, default="data/processed/evaluation_report.md", help="Path to output report")
    args = parser.parse_args()

    logger.info(f"Loading predictions from {args.predictions}")
    predictions = load_predictions(args.predictions)
    
    logger.info(f"Loading ground truth from {args.ground_truth}")
    ground_truth = load_ground_truth(args.ground_truth)
    
    density_metadata = None
    if args.metadata:
        logger.info(f"Loading metadata from {args.metadata}")
        with open(args.metadata, 'r') as f:
            metadata = json.load(f)
            density_metadata = {entry['seed']: entry['inclusion_density'] for entry in metadata}

    logger.info("Computing errors...")
    results, aggregate = compute_errors(predictions, ground_truth)
    
    logger.info(f"Aggregate MAE: {aggregate['mae']:.6f}")
    logger.info(f"Aggregate MSE: {aggregate['mse']:.6f}")
    logger.info(f"Aggregate R2: {aggregate['r2']:.6f}")
    
    logger.info(f"Generating report to {args.output}")
    generate_report(results, aggregate, args.output, density_metadata)
    
    logger.info("Evaluation complete.")

if __name__ == "__main__":
    main()