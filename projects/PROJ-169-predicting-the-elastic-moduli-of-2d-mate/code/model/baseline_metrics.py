import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import torch
from torch_geometric.data import DataLoader as PyGDataLoader
from torch_geometric.loader import DataLoader

from utils.config import Config
from utils.logger import get_logger
from model.gnn import LightweightGNN, create_model
from model.splitter import load_graphs_from_parquet, split_by_family
from model.eval import calculate_metrics, evaluate_model

@dataclass
class BaselineResult:
    mape: float
    rmse: float
    r2: float
    family: str
    sample_size: int

@dataclass
class BaselineReport:
    intra_family_metrics: List[Dict[str, Any]]
    aggregated_metrics: Dict[str, float]
    description: str

def run_intra_family_baseline(
    graphs: List[Dict[str, Any]],
    model: LightweightGNN,
    device: torch.device,
    batch_size: int = 32
) -> List[Dict[str, Any]]:
    """
    Run intra-family baseline metrics.
    
    Strategy:
    1. Group graphs by family_id (from the graph metadata).
    2. For each family with sufficient data (N > 10):
       - Perform a random 80/20 split within that family.
       - Train a fresh lightweight model on the 80% train set.
       - Evaluate on the 20% test set.
       - Record MAPE, RMSE, R2.
    
    This establishes the "best case" performance if the model never needs
    to generalize to unseen chemical families (SC-002 baseline).
    """
    logger = get_logger("baseline_metrics")
    
    # Group by family
    family_map: Dict[str, List[Dict[str, Any]]] = {}
    for g in graphs:
        fid = g.get("family_id", "unknown")
        if fid not in family_map:
            family_map[fid] = []
        family_map[fid].append(g)
    
    results = []
    
    # We need a simple training loop for the baseline
    # Re-using logic from model.train but simplified for intra-family
    from model.train import graph_to_pyg, train_epoch, evaluate as train_evaluate
    
    for family_id, family_graphs in family_map.items():
        if len(family_graphs) < 20:
            logger.info(f"Skipping family {family_id}: only {len(family_graphs)} samples (need >= 20)")
            continue
        
        logger.info(f"Processing intra-family baseline for: {family_id} (n={len(family_graphs)})")
        
        # Random split 80/20 within family
        np.random.shuffle(family_graphs)
        split_idx = int(len(family_graphs) * 0.8)
        train_graphs = family_graphs[:split_idx]
        test_graphs = family_graphs[split_idx:]
        
        # Convert to PyG Data objects
        train_data_list = [graph_to_pyg(g) for g in train_graphs]
        test_data_list = [graph_to_pyg(g) for g in test_graphs]
        
        train_loader = PyGDataLoader(train_data_list, batch_size=batch_size, shuffle=True)
        test_loader = PyGDataLoader(test_data_list, batch_size=batch_size, shuffle=False)
        
        # Initialize a fresh model for this family
        # Using the same architecture as the main model
        model = create_model(input_dim=12, hidden_dim=64, num_classes=1) # 12 is typical for node features, adjust if needed
        model = model.to(device)
        
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = torch.nn.MSELoss()
        
        # Train for a fixed number of epochs (e.g., 50) for the baseline
        epochs = 50
        for epoch in range(epochs):
            model.train()
            total_loss = 0
            for batch in train_loader:
                batch = batch.to(device)
                optimizer.zero_grad()
                out = model(batch.x, batch.edge_index, batch.batch)
                # Target is in batch.y (assuming y is the tensor of moduli)
                # Note: graph_to_pyg should have set y correctly
                if batch.y.dim() > 1 and batch.y.size(1) == 3:
                    # If we are predicting 3 targets (Young, Shear, Poisson), take mean or specific one
                    # For baseline, let's assume we predict the first one (Young's Modulus) or average
                    target = batch.y[:, 0] 
                else:
                    target = batch.y
                
                loss = criterion(out.squeeze(), target)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
        
        # Evaluate
        model.eval()
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for batch in test_loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.batch)
                if batch.y.dim() > 1 and batch.y.size(1) == 3:
                    target = batch.y[:, 0]
                else:
                    target = batch.y
                all_preds.append(out.squeeze().cpu().numpy())
                all_targets.append(target.cpu().numpy())
        
        all_preds = np.concatenate(all_preds)
        all_targets = np.concatenate(all_targets)
        
        # Calculate metrics
        mape = calculate_metrics(all_preds, all_targets, metric="mape")
        rmse = calculate_metrics(all_preds, all_targets, metric="rmse")
        r2 = calculate_metrics(all_preds, all_targets, metric="r2")
        
        results.append({
            "family_id": family_id,
            "mape": float(mape),
            "rmse": float(rmse),
            "r2": float(r2),
            "sample_size": len(test_graphs)
        })
        
        logger.info(f"  Family {family_id} Baseline -> MAPE: {mape:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Run Intra-Family Baseline Metrics")
    parser.add_argument("--input", type=str, default="data/processed/graphs_v1.parquet", help="Path to processed graphs parquet")
    parser.add_argument("--output", type=str, default="data/results/baseline_metrics.json", help="Path to output JSON report")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for training")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    # Setup
    Config.set_seed(args.seed)
    logger = get_logger("baseline_metrics")
    logger.info(f"Starting intra-family baseline on {args.input}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    # Load data
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}. Run T013 first.")
    
    graphs = load_graphs_from_parquet(args.input)
    logger.info(f"Loaded {len(graphs)} graphs")
    
    if not graphs:
        raise ValueError("No graphs loaded. Cannot run baseline.")
    
    # Run baseline
    results = run_intra_family_baseline(graphs, None, device, args.batch_size)
    
    # Aggregate
    if not results:
        logger.warning("No families had enough data for baseline. Writing empty report.")
        report = BaselineReport(
            intra_family_metrics=[],
            aggregated_metrics={"mape": 0.0, "rmse": 0.0, "r2": 0.0},
            description="No families met the minimum sample size threshold."
        )
    else:
        avg_mape = np.mean([r["mape"] for r in results])
        avg_rmse = np.mean([r["rmse"] for r in results])
        avg_r2 = np.mean([r["r2"] for r in results])
        
        report = BaselineReport(
            intra_family_metrics=results,
            aggregated_metrics={
                "mape": float(avg_mape),
                "rmse": float(avg_rmse),
                "r2": float(avg_r2)
            },
            description=f"Average metrics across {len(results)} families with sufficient data. "
                        "These values represent the theoretical upper bound of performance "
                        "if the model only encounters families seen during training."
        )
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump({
            "metadata": {
                "source": "T020a: Intra-Family Baseline",
                "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
            },
            "report": asdict(report)
        }, f, indent=2)
    
    logger.info(f"Baseline report saved to {output_path}")
    print(f"Aggregated MAPE: {report.aggregated_metrics['mape']:.4f}")
    print(f"Aggregated RMSE: {report.aggregated_metrics['rmse']:.4f}")
    print(f"Aggregated R2: {report.aggregated_metrics['r2']:.4f}")

if __name__ == "__main__":
    main()
