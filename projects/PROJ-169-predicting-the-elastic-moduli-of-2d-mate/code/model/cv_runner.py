import os
import json
import logging
import time
import gc
import tracemalloc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import torch

from utils.config import Config
from utils.logger import get_logger, log_training_metrics
from model.gnn import create_model, LightweightGNN
from model.splitter import split_by_family
from model.train import graph_to_pyg, train_epoch, evaluate
from model.eval import calculate_metrics

@dataclass
class FoldResult:
    fold: int
    mape: float
    rmse: float
    r2: float
    train_size: int
    val_size: int

@dataclass
class CrossValidationReport:
    folds: List[FoldResult]
    mean_mape: float
    mean_rmse: float
    mean_r2: float
    std_mape: float
    std_rmse: float
    std_r2: float
    metadata: Dict[str, Any]

def load_graphs_from_parquet(path: Path) -> List[Dict[str, Any]]:
    """Load graphs from parquet file."""
    import pyarrow.parquet as pq
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    table = pq.read_table(path)
    return [row.as_py() for row in table.to_pydict()]

def run_single_fold(
    fold: int,
    graphs: List[Dict[str, Any]],
    config: Dict[str, Any],
    logger: logging.Logger
) -> FoldResult:
    """Run a single cross-validation fold."""
    logger.info(f"Starting fold {fold}")
    
    # Initialize config for this fold
    fold_config = Config(
        seed=config.get('seed', 42) + fold,
        max_epochs=config.get('max_epochs', 50),
        patience=config.get('patience', 3),
        learning_rate=config.get('learning_rate', 1e-3),
        batch_size=config.get('batch_size', 32),
        device=config.get('device', 'cpu')
    )
    
    # Split data: use family-based splitting to ensure no data leakage
    # We need to simulate k-fold by splitting families
    # For simplicity, we'll do a stratified split by family_id
    family_groups: Dict[str, List[Dict[str, Any]]] = {}
    for g in graphs:
        fid = g.get('family_id', 'unknown')
        if fid not in family_groups:
            family_groups[fid] = []
        family_groups[fid].append(g)
    
    family_ids = list(family_groups.keys())
    np.random.seed(fold_config.seed)
    np.random.shuffle(family_ids)
    
    k = config.get('k_folds', 5)
    fold_size = len(family_ids) // k
    start_idx = fold_idx = fold * fold_size
    end_idx = start_idx + fold_size if fold < k - 1 else len(family_ids)
    
    val_families = set(family_ids[start_idx:end_idx])
    train_families = set(family_ids) - val_families
    
    train_graphs = [g for g in graphs if g.get('family_id') in train_families]
    val_graphs = [g for g in graphs if g.get('family_id') in val_families]
    
    if not train_graphs or not val_graphs:
        raise ValueError(f"Fold {fold}: Empty train or val split. Families: {len(family_ids)}")
    
    logger.info(f"Fold {fold}: Train={len(train_graphs)}, Val={len(val_graphs)}")
    
    # Convert to PyG Data
    train_data = [graph_to_pyg(g) for g in train_graphs]
    val_data = [graph_to_pyg(g) for g in val_graphs]
    
    # Create model
    model = create_model(
        node_dim=train_data[0].x.shape[1] if len(train_data) > 0 else 10,
        edge_dim=train_data[0].edge_attr.shape[1] if len(train_data) > 0 and train_data[0].edge_attr is not None else 10,
        out_dim=3,  # Young's, Shear, Poisson
        hidden_dim=config.get('hidden_dim', 64),
        num_layers=config.get('num_layers', 2)
    )
    model.to(fold_config.device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=fold_config.learning_rate)
    
    # Training loop with early stopping
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    training_history = []
    
    # Start memory tracking
    tracemalloc.start()
    
    for epoch in range(fold_config.max_epochs):
        model.train()
        epoch_loss = train_epoch(model, train_data, optimizer, fold_config.device)
        
        model.eval()
        with torch.no_grad():
            val_loss, val_preds, val_targets = evaluate(model, val_data, fold_config.device)
            metrics = calculate_metrics(val_targets, val_preds)
            
        current_mem = tracemalloc.get_traced_memory()[1] / (1024 * 1024)  # MB
        
        log_entry = {
            "fold": fold,
            "epoch": epoch,
            "loss": float(epoch_loss),
            "val_loss": float(val_loss),
            "metrics": {
                "mape": float(metrics['mape']),
                "rmse": float(metrics['rmse']),
                "r2": float(metrics['r2'])
            },
            "memory_peak_mb": float(current_mem)
        }
        training_history.append(log_entry)
        
        logger.info(f"Fold {fold} Epoch {epoch}: Loss={epoch_loss:.4f}, MAPE={metrics['mape']:.4f}")
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= fold_config.patience:
                logger.info(f"Fold {fold}: Early stopping at epoch {epoch}")
                break
    
    # Restore best model and evaluate final metrics
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    model.eval()
    with torch.no_grad():
        final_loss, final_preds, final_targets = evaluate(model, val_data, fold_config.device)
        final_metrics = calculate_metrics(final_targets, final_preds)
    
    tracemalloc.stop()
    
    result = FoldResult(
        fold=fold,
        mape=float(final_metrics['mape']),
        rmse=float(final_metrics['rmse']),
        r2=float(final_metrics['r2']),
        train_size=len(train_graphs),
        val_size=len(val_graphs)
    )
    
    # Save fold-specific log
    log_path = Path(config.get('log_dir', 'data/results')) / f"cv_fold_{fold}.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump({
            "fold": fold,
            "history": training_history,
            "final_metrics": final_metrics,
            "metadata": {
                "train_size": len(train_graphs),
                "val_size": len(val_graphs),
                "seed": fold_config.seed,
                "surrogate_warning": "WARNING: This model is a surrogate interpolating pre-computed DFT results. It does NOT solve the Schrödinger equation or perform first-principles calculations."
            }
        }, f, indent=2)
    
    return result

def run_k_fold_cross_validation(
    graphs: List[Dict[str, Any]],
    k: int = 5,
    config: Optional[Dict[str, Any]] = None
) -> CrossValidationReport:
    """Run k-fold cross-validation."""
    config = config or {}
    logger = get_logger("cv_runner")
    logger.info(f"Starting {k}-fold cross-validation on {len(graphs)} graphs")
    
    if k < 2:
        raise ValueError("k must be >= 2")
    if len(graphs) < k:
        raise ValueError(f"Not enough graphs ({len(graphs)}) for {k}-fold CV")
    
    folds = []
    for i in range(k):
        result = run_single_fold(i, graphs, config, logger)
        folds.append(result)
        # Clear memory between folds
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    mapes = [f.mape for f in folds]
    rmses = [f.rmse for f in folds]
    r2s = [f.r2 for f in folds]
    
    report = CrossValidationReport(
        folds=folds,
        mean_mape=float(np.mean(mapes)),
        mean_rmse=float(np.mean(rmses)),
        mean_r2=float(np.mean(r2s)),
        std_mape=float(np.std(mapes)),
        std_rmse=float(np.std(rmses)),
        std_r2=float(np.std(r2s)),
        metadata={
            "k": k,
            "total_graphs": len(graphs),
            "surrogate_warning": "WARNING: These results are ML interpolations of DFT data, not first-principles solutions.",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    
    return report

def main():
    parser = argparse.ArgumentParser(description="K-Fold Cross-Validation Runner")
    parser.add_argument("--input", type=str, default="data/processed/graphs_v1.parquet",
                      help="Path to input parquet file")
    parser.add_argument("--k", type=int, default=5, help="Number of folds")
    parser.add_argument("--output", type=str, default="data/results/cv_report.json",
                      help="Path to output report JSON")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--max_epochs", type=int, default=50, help="Max training epochs")
    parser.add_argument("--patience", type=int, default=3, help="Early stopping patience")
    parser.add_argument("--hidden_dim", type=int, default=64, help="Hidden dimension")
    parser.add_argument("--num_layers", type=int, default=2, help="Number of GNN layers")
    parser.add_argument("--learning_rate", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu/cuda)")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger("cv_runner")
    logger.info(f"Starting K-Fold CV: k={args.k}, input={args.input}")
    
    # Load graphs
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    graphs = load_graphs_from_parquet(input_path)
    logger.info(f"Loaded {len(graphs)} graphs")
    
    if len(graphs) == 0:
        raise ValueError("No graphs loaded. Check input file.")
    
    # Configuration
    config = {
        "seed": args.seed,
        "max_epochs": args.max_epochs,
        "patience": args.patience,
        "hidden_dim": args.hidden_dim,
        "num_layers": args.num_layers,
        "learning_rate": args.learning_rate,
        "device": args.device,
        "k_folds": args.k,
        "log_dir": str(Path(args.output).parent)
    }
    
    # Run CV
    report = run_k_fold_cross_validation(graphs, k=args.k, config=config)
    
    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_dict = {
        "folds": [asdict(f) for f in report.folds],
        "mean_mape": report.mean_mape,
        "mean_rmse": report.mean_rmse,
        "mean_r2": report.mean_r2,
        "std_mape": report.std_mape,
        "std_rmse": report.std_rmse,
        "std_r2": report.std_r2,
        "metadata": report.metadata
    }
    
    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)
    
    logger.info(f"Cross-validation complete. Report saved to {output_path}")
    logger.info(f"Mean MAPE: {report.mean_mape:.4f} (+/- {report.std_mape:.4f})")
    logger.info(f"Mean RMSE: {report.mean_rmse:.4f} (+/- {report.std_rmse:.4f})")
    logger.info(f"Mean R2: {report.mean_r2:.4f} (+/- {report.std_r2:.4f})")
    
    # Log summary to training logs for consistency
    summary_log = Path("data/results/training_logs.json")
    existing_logs = []
    if summary_log.exists():
        with open(summary_log, 'r') as f:
            existing_logs = json.load(f)
    
    summary_entry = {
        "type": "cv_summary",
        "k_folds": args.k,
        "mean_mape": report.mean_mape,
        "mean_rmse": report.mean_rmse,
        "mean_r2": report.mean_r2,
        "std_mape": report.std_mape,
        "std_rmse": report.std_rmse,
        "std_r2": report.std_r2,
        "metadata": {
            "surrogate_warning": "WARNING: This model is a surrogate interpolating pre-computed DFT results. It does NOT solve the Schrödinger equation or perform first-principles calculations."
        }
    }
    existing_logs.append(summary_entry)
    
    with open(summary_log, 'w') as f:
        json.dump(existing_logs, f, indent=2)
    
    logger.info("Summary logged to data/results/training_logs.json")

if __name__ == "__main__":
    main()
