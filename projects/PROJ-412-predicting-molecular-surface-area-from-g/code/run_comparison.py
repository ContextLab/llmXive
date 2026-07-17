import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging import setup_logging, get_logger
from utils.config import get_project_root, get_data_dir, get_results_dir
from utils.seed import set_seed, get_seed_from_env
from models.train import train_model, load_processed_graphs
from models.baseline_3d import predict_baseline_sasa
from eval.metrics import calculate_all_metrics, compare_models, calculate_mae
from data.split import load_processed_data
from data.logging_stats import log_dataset_statistics

def main():
    parser = argparse.ArgumentParser(description="Run model comparison: GCN vs 3D Baseline")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--epochs", type=int, default=50, help="Maximum training epochs")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    # Setup seed
    seed = args.seed if args.seed is not None else get_seed_from_env()
    set_seed(seed)
    logger.info(f"Using seed: {seed}")

    project_root = get_project_root()
    data_dir = get_data_dir()
    results_dir = get_results_dir()
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "reports" / "model_comparison.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading processed data from {data_dir / 'processed'}...")
    
    # Load processed data
    # Assuming the processed data is in a standard location as per previous tasks
    processed_data_path = data_dir / "processed" / "molecules.parquet"
    if not processed_data_path.exists():
        # Fallback to a generic path if specific one isn't found, 
        # but in a real scenario, this should be strictly defined.
        processed_data_path = data_dir / "processed" / "data.parquet"
    
    if not processed_data_path.exists():
        logger.error(f"Processed data not found at {processed_data_path}. Run preprocessing first.")
        sys.exit(1)

    # Load train/test indices
    train_indices_path = data_dir / "splits" / "train_indices.csv"
    test_indices_path = data_dir / "splits" / "test_indices.csv"

    if not train_indices_path.exists() or not test_indices_path.exists():
        logger.error("Split indices not found. Run split task first.")
        sys.exit(1)

    # 1. Train GCN Model
    logger.info("Starting GCN training...")
    gcn_model_path = results_dir / "models" / "gcn_model.pt"
    gcn_model_path.parent.mkdir(parents=True, exist_ok=True)

    # We need to load the data in a format suitable for training
    # The train.py module handles loading processed graphs
    # We assume load_processed_graphs reads from the parquet and splits
    try:
        # This call mimics the training script logic
        # We pass the paths directly or rely on the module's internal logic
        # Since train_model expects specific arguments, we construct them
        
        # Re-using the logic from train.py main but adapted for comparison
        from models.train import load_processed_graphs, train_epoch, evaluate, early_stopping
        
        # Load data
        train_graphs, test_graphs = load_processed_graphs(
            data_path=str(processed_data_path),
            train_indices_path=str(train_indices_path),
            test_indices_path=str(test_indices_path)
        )

        if not train_graphs:
            logger.error("No training graphs loaded.")
            sys.exit(1)

        # Train
        gcn_model, train_history = train_model(
            train_graphs=train_graphs,
            test_graphs=test_graphs,
            epochs=args.epochs,
            patience=args.patience,
            device="cpu", # Force CPU as per constraints
            save_path=str(gcn_model_path)
        )
        
        logger.info(f"GCN training complete. Model saved to {gcn_model_path}")
    except Exception as e:
        logger.error(f"GCN training failed: {e}", exc_info=True)
        # If training fails, we cannot produce a valid comparison report
        # We should exit with an error or produce a report indicating failure
        sys.exit(1)

    # 2. Evaluate GCN Model
    logger.info("Evaluating GCN model...")
    # We need to run inference on the test set
    # Assuming we can load the model and run forward pass
    # The train.py evaluate function returns metrics
    # We need to re-evaluate on the test set to get predictions
    
    # Let's assume we have a function to get predictions
    # Since the API surface doesn't explicitly show a 'predict' function,
    # we will rely on the 'evaluate' function from train.py if it returns metrics
    # or we implement a simple inference loop.
    
    # Re-implementing a simple evaluation loop based on typical GCN usage
    # to ensure we get predictions for the comparison
    from models.gcn import GCNModel
    import torch
    
    # Load the model
    model = GCNModel(input_dim=train_graphs[0].x.shape[1], hidden_dim=64, output_dim=1)
    model.load_state_dict(torch.load(gcn_model_path))
    model.eval()
    
    gcn_y_true = []
    gcn_y_pred = []
    
    with torch.no_grad():
        for graph in test_graphs:
            # Move to CPU
            graph = graph.to('cpu')
            out = model(graph.x.float(), graph.edge_index, graph.batch)
            # Assuming output is [N, 1], flatten
            preds = out.squeeze().tolist()
            targets = graph.y.squeeze().tolist()
            
            if isinstance(targets, list):
                gcn_y_true.extend(targets)
                gcn_y_pred.extend(preds)
            else:
                gcn_y_true.append(targets)
                gcn_y_pred.append(preds)
    
    gcn_metrics = calculate_all_metrics(gcn_y_true, gcn_y_pred)
    logger.info(f"GCN Metrics: {gcn_metrics}")

    # 3. Run 3D Baseline
    logger.info("Running 3D Baseline predictions...")
    # The baseline_3d module has predict_baseline_sasa
    # It likely takes the processed data or SMILES and returns predictions
    # We need to load the SMILES for the test set to run the baseline
    
    # Re-load data to get SMILES for test set
    # Assuming load_processed_data returns a dataframe or similar
    import pandas as pd
    df = pd.read_parquet(processed_data_path)
    
    # Filter for test indices
    test_indices = pd.read_csv(test_indices_path, header=None)[0].tolist()
    test_df = df.iloc[test_indices].reset_index(drop=True)
    
    if 'smiles' not in test_df.columns:
        logger.error("SMILES column not found in processed data. Cannot run baseline.")
        sys.exit(1)
    
    smiles_list = test_df['smiles'].tolist()
    
    baseline_y_true = []
    baseline_y_pred = []
    
    # Run baseline prediction
    # predict_baseline_sasa returns a list of predictions
    try:
        baseline_predictions = predict_baseline_sasa(smiles_list)
        if len(baseline_predictions) != len(smiles_list):
            logger.warning("Prediction count mismatch. Using available.")
            baseline_predictions = baseline_predictions[:len(smiles_list)]
        
        # Get true values
        true_values = test_df['sasa'].tolist()
        
        baseline_y_pred = baseline_predictions
        baseline_y_true = true_values
    except Exception as e:
        logger.error(f"Baseline prediction failed: {e}", exc_info=True)
        sys.exit(1)

    baseline_metrics = calculate_all_metrics(baseline_y_true, baseline_y_pred)
    logger.info(f"Baseline Metrics: {baseline_metrics}")

    # 4. Compare Models
    logger.info("Comparing models...")
    
    # Ensure lists are same length (they should be)
    if len(gcn_y_true) != len(baseline_y_true):
        logger.error("True value lists for GCN and Baseline are of different lengths.")
        sys.exit(1)
    
    comparison = compare_models(gcn_y_true, gcn_y_pred, baseline_y_true, baseline_y_pred)
    
    # 5. Generate Report
    report = {
        "gcn": {
            "mae": gcn_metrics['mae'],
            "rmse": gcn_metrics['rmse'],
            "r2": gcn_metrics['r2']
        },
        "baseline": {
            "mae": baseline_metrics['mae'],
            "rmse": baseline_metrics['rmse'],
            "r2": baseline_metrics['r2']
        },
        "comparison": {
            "p_value": comparison['p_value'],
            "cohen_d": comparison['cohen_d'],
            "winner": comparison['winner'] # 'gcn' or 'baseline' or 'tie'
        },
        "metadata": {
            "seed": seed,
            "epochs": args.epochs,
            "patience": args.patience,
            "test_size": len(gcn_y_true)
        }
    }

    # Save report
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Comparison report saved to {report_path}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()