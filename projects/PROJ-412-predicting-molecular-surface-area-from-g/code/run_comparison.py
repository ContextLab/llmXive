import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.seed import set_seed
from models.train import train_model, load_processed_graphs
from models.baseline import train_baseline_model, load_processed_data_for_baseline
from eval.metrics import (
    calculate_mae, 
    calculate_rmse, 
    calculate_r2, 
    calculate_all_metrics,
    paired_ttest,
    cohen_d
)

logger = get_logger(__name__)

def load_predictions_from_file(path: Path) -> tuple:
    """Load predictions and true values from a JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)
    return data['true_values'], data['predictions']

def run_comparison(args):
    """
    Integrate training and evaluation to produce final comparison report.
    
    This script:
    1. Loads processed data
    2. Trains the GCN model (if not already done)
    3. Trains the Random Forest baseline (if not already done)
    4. Evaluates both models on the test set
    5. Performs statistical comparison (paired t-test, Cohen's d)
    6. Generates a comprehensive report in results/reports/model_comparison.json
    """
    logger.info("Starting model comparison pipeline...")
    
    # Set seed for reproducibility
    set_seed(args.seed)
    
    # Paths
    processed_data_path = Path(args.data_path)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = results_dir / "model_comparison.json"
    gcn_preds_path = Path(args.gcn_predictions)
    rf_preds_path = Path(args.rf_predictions)
    
    # Check if predictions exist, if not train and evaluate
    gcn_metrics = None
    rf_metrics = None
    gcn_true = None
    gcn_pred = None
    rf_true = None
    rf_pred = None
    
    # Try to load existing predictions
    if gcn_preds_path.exists() and rf_preds_path.exists():
        logger.info("Loading existing predictions...")
        gcn_true, gcn_pred = load_predictions_from_file(gcn_preds_path)
        rf_true, rf_pred = load_predictions_from_file(rf_preds_path)
        
        # Recalculate metrics from loaded predictions to ensure consistency
        gcn_metrics = calculate_all_metrics(gcn_true, gcn_pred)
        rf_metrics = calculate_all_metrics(rf_true, rf_pred)
        logger.info("Loaded existing predictions and recalculated metrics.")
    else:
        logger.info("Predictions not found. Training and evaluating models...")
        
        # Load data for GCN
        logger.info("Loading processed graphs for GCN...")
        train_data, val_data, test_data = load_processed_graphs(
            processed_data_path, 
            args.train_split, 
            args.test_split
        )
        
        # Train GCN
        logger.info("Training GCN model...")
        gcn_model = train_model(
            train_data, 
            val_data, 
            device=args.device, 
            epochs=args.epochs, 
            patience=args.patience,
            learning_rate=args.learning_rate,
            batch_size=args.batch_size
        )
        
        # Evaluate GCN
        logger.info("Evaluating GCN model on test set...")
        gcn_true, gcn_pred = gcn_model.evaluate(test_data)
        gcn_metrics = calculate_all_metrics(gcn_true, gcn_pred)
        
        # Save GCN predictions
        with open(gcn_preds_path, 'w') as f:
            json.dump({
                'true_values': [float(x) for x in gcn_true],
                'predictions': [float(x) for x in gcn_pred]
            }, f, indent=2)
        
        # Load data for Baseline
        logger.info("Loading processed data for Random Forest baseline...")
        X_train, y_train, X_test, y_test = load_processed_data_for_baseline(
            processed_data_path,
            args.train_split,
            args.test_split
        )
        
        # Train Baseline
        logger.info("Training Random Forest baseline...")
        rf_model = train_baseline_model(X_train, y_train)
        
        # Evaluate Baseline
        logger.info("Evaluating Random Forest baseline on test set...")
        rf_pred, rf_true = evaluate_model(rf_model, X_test, y_test)
        rf_metrics = calculate_all_metrics(rf_true, rf_pred)
        
        # Save RF predictions
        with open(rf_preds_path, 'w') as f:
            json.dump({
                'true_values': [float(x) for x in rf_true],
                'predictions': [float(x) for x in rf_pred]
            }, f, indent=2)
    
    # Ensure we have aligned true values (should be the same for both models)
    if gcn_true is not None and rf_true is not None:
        # Convert to lists if they are numpy arrays
        gcn_true = list(gcn_true)
        rf_true = list(rf_true)
        gcn_pred = list(gcn_pred)
        rf_pred = list(rf_pred)
        
        # Statistical comparison
        logger.info("Performing statistical comparison...")
        
        # Paired t-test
        t_stat, p_value = paired_ttest(gcn_pred, rf_pred)
        
        # Cohen's d
        cohens_d = cohen_d(gcn_pred, rf_pred)
        
        # Determine which model is better based on MAE
        gcn_mae = gcn_metrics['mae']
        rf_mae = rf_metrics['mae']
        better_model = "GCN" if gcn_mae < rf_mae else "Random Forest"
        if gcn_mae == rf_mae:
            better_model = "Tie"
        
        # Construct report
        report = {
            "gcn_metrics": {
                "mae": float(gcn_metrics['mae']),
                "rmse": float(gcn_metrics['rmse']),
                "r2": float(gcn_metrics['r2']),
                "mae_std": float(gcn_metrics.get('mae_std', 0.0)),
                "rmse_std": float(gcn_metrics.get('rmse_std', 0.0))
            },
            "rf_metrics": {
                "mae": float(rf_metrics['mae']),
                "rmse": float(rf_metrics['rmse']),
                "r2": float(rf_metrics['r2']),
                "mae_std": float(rf_metrics.get('mae_std', 0.0)),
                "rmse_std": float(rf_metrics.get('rmse_std', 0.0))
            },
            "statistical_comparison": {
                "paired_ttest": {
                    "t_statistic": float(t_stat),
                    "p_value": float(p_value),
                    "significant_at_0.05": bool(p_value < 0.05)
                },
                "cohens_d": float(cohens_d),
                "effect_size_interpretation": interpret_effect_size(cohens_d),
                "better_model": better_model,
                "mae_difference": float(abs(gcn_mae - rf_mae))
            },
            "metadata": {
                "seed": args.seed,
                "epochs": args.epochs,
                "patience": args.patience,
                "device": args.device,
                "data_path": str(processed_data_path),
                "timestamp": None  # Can be populated if needed
            }
        }
        
        # Write report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Comparison report written to {report_path}")
        logger.info(f"GCN MAE: {gcn_mae:.4f}, RF MAE: {rf_mae:.4f}")
        logger.info(f"Better model: {better_model}")
        logger.info(f"P-value: {p_value:.4f}, Cohen's d: {cohens_d:.4f}")
        
        return report
    else:
        logger.error("Could not obtain predictions for both models.")
        raise RuntimeError("Failed to generate predictions for comparison.")

def interpret_effect_size(d: float) -> str:
    """Interpret Cohen's d effect size."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def main():
    parser = argparse.ArgumentParser(description="Run model comparison between GCN and Random Forest")
    parser.add_argument("--data_path", type=str, default="data/processed/graphs_with_features.parquet",
                        help="Path to processed data file")
    parser.add_argument("--train_split", type=str, default="data/splits/train_indices.csv",
                        help="Path to training indices")
    parser.add_argument("--test_split", type=str, default="data/splits/test_indices.csv",
                        help="Path to test indices")
    parser.add_argument("--results_dir", type=str, default="results/reports",
                        help="Directory to save results")
    parser.add_argument("--gcn_predictions", type=str, default="results/predictions/gcn_predictions.json",
                        help="Path to save/load GCN predictions")
    parser.add_argument("--rf_predictions", type=str, default="results/predictions/rf_predictions.json",
                        help="Path to save/load RF predictions")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Device to use for training (cpu or cuda)")
    parser.add_argument("--epochs", type=int, default=50,
                        help="Maximum number of training epochs")
    parser.add_argument("--patience", type=int, default=5,
                        help="Early stopping patience")
    parser.add_argument("--learning_rate", type=float, default=0.001,
                        help="Learning rate")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="Batch size")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_comparison(args)

if __name__ == "__main__":
    main()