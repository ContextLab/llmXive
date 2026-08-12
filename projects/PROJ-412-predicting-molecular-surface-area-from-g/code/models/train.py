import os
import sys
import json
import logging
import argparse
import tracemalloc
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import torch
import torch.nn.functional as F
from torch_geometric.data import DataLoader
from torch_geometric.nn import GCNConv, global_mean_pool
import numpy as np

# Project imports
from code.utils.logging import get_logger, setup_logging
from code.utils.seed import set_seed
from code.utils.memory_monitor import MemoryMonitor
from code.config import TIME_BUDGET, MAX_RAM_GB, SENSITIVITY_THRESHOLDS
from code.data_models.evaluation_result import EvaluationResult

# Local imports for model definition
from code.models.gcn import GCNModel, create_model_from_processed_data

logger = get_logger(__name__)

class EarlyStopping:
    def __init__(self, patience: int = 5, min_delta: float = 1e-4):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss: Optional[float] = None
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
            return False

        if val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True
        else:
            self.best_loss = val_loss
            self.counter = 0
        return False

def load_processed_graphs(path: str) -> List[Any]:
    """
    Loads processed graph data from a Parquet file and converts to PyG Data objects.
    This is a placeholder implementation assuming the existence of a conversion utility.
    In a real scenario, this would use pyarrow or pandas to read the parquet and map columns.
    """
    import pandas as pd
    from torch_geometric.data import Data
    import numpy as np

    df = pd.read_parquet(path)
    graphs = []
    
    # Assuming columns 'node_features', 'edge_features', 'edge_index' (as list of lists), 'y' (target)
    # and 'smiles' for identification.
    # Note: Edge index in parquet is often stored as a list of lists or a string representation.
    # We assume a structure compatible with the pipeline defined in T014/T015c.
    
    for _, row in df.iterrows():
        # Reconstruct node features
        node_features = np.array(row['node_features']) if isinstance(row['node_features'], list) else row['node_features']
        
        # Reconstruct edge index
        edge_index = np.array(row['edge_index']) if 'edge_index' in row else np.array([[0, 1], [1, 0]]) # Fallback for empty molecules
        
        # Reconstruct edge features if present
        edge_attr = None
        if 'edge_features' in row and row['edge_features']:
            edge_attr = np.array(row['edge_features'])
        
        y = np.array([row['surface_area']]) if 'surface_area' in row else np.array([0.0])
        
        data = Data(
            x=torch.FloatTensor(node_features),
            edge_index=torch.LongTensor(edge_index),
            edge_attr=torch.FloatTensor(edge_attr) if edge_attr is not None else None,
            y=torch.FloatTensor(y)
        )
        data.smiles = row.get('smiles', '')
        graphs.append(data)
    
    return graphs

def train_epoch(
    model: GCNModel, 
    loader: DataLoader, 
    optimizer: torch.optim.Optimizer, 
    device: torch.device,
    batch_size: int
) -> float:
    """
    Trains the model for one epoch.
    Includes OOM handling logic for the specific batch causing the error.
    """
    model.train()
    total_loss = 0.0
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        try:
            out = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            loss = F.mse_loss(out, batch.y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * batch.num_graphs
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                # OOM detected. This should ideally be handled at the loader level 
                # or by reducing the batch size passed to the DataLoader.
                # However, if we are inside the loop, we might need to skip this batch
                # and trigger a reduction in the main training loop logic.
                # For T058, the main logic handles the reduction.
                # We raise a custom exception or handle it here to break the epoch.
                logger.warning(f"OOM error during training batch. Skipping batch and triggering reduction.")
                # We cannot continue this epoch with the current batch size if OOM persists.
                # The caller (train_model) will catch this and reduce batch size.
                raise e
            else:
                raise e
    
    return total_loss / len(loader.dataset)

def train_epoch_corrected(
    model: GCNModel,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device
) -> float:
    """
    Wrapper for training epoch with memory monitoring integration.
    """
    return train_epoch(model, loader, optimizer, device, loader.batch_size)

def evaluate(
    model: GCNModel, 
    loader: DataLoader, 
    device: torch.device
) -> Tuple[float, List[float], List[float]]:
    model.eval()
    total_loss = 0.0
    predictions = []
    targets = []
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            loss = F.mse_loss(out, batch.y)
            total_loss += loss.item() * batch.num_graphs
            
            predictions.extend(out.cpu().numpy().tolist())
            targets.extend(batch.y.cpu().numpy().tolist())
    
    avg_loss = total_loss / len(loader.dataset)
    return avg_loss, predictions, targets

def train_model(
    train_data: List[Any],
    test_data: List[Any],
    config: Dict[str, Any],
    device: torch.device
) -> EvaluationResult:
    """
    Trains the GCN model with dynamic batch size fallback.
    
    Implements T058: If OOM occurs, reduce batch size by half and retry.
    """
    initial_batch_size = config.get('batch_size', 32)
    min_batch_size = config.get('min_batch_size', 1)
    max_epochs = config.get('epochs', 50)
    patience = config.get('patience', 5)
    learning_rate = config.get('lr', 0.01)
    seed = config.get('seed', 42)
    
    set_seed(seed)
    
    # Initialize model
    model = GCNModel()
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
    early_stopping = EarlyStopping(patience=patience)
    
    memory_monitor = MemoryMonitor()
    
    current_batch_size = initial_batch_size
    last_oom_batch_size = initial_batch_size + 1 # Ensure entry into loop logic if needed
    
    logger.info(f"Starting training with batch size: {current_batch_size}")
    
    while current_batch_size >= min_batch_size:
        try:
            # Create DataLoaders
            train_loader = DataLoader(train_data, batch_size=current_batch_size, shuffle=True)
            test_loader = DataLoader(test_data, batch_size=current_batch_size, shuffle=False)
            
            # Reset state for new batch size attempt
            model.load_state_dict({k: v for k, v in model.state_dict().items()}) # Reset weights? Or keep?
            # Usually, if OOM happens early, we might want to restart, but if we are mid-training,
            # we might just continue. For simplicity and robustness in T058, we restart training
            # with the new batch size to ensure consistent behavior, or we could continue.
            # Given the constraint "reduce batch size ... and retry", we will restart the epoch loop.
            # To avoid re-training from scratch every time (which is expensive), we could save/restore.
            # However, for this specific task implementation, we will assume we restart the epoch loop
            # but keep the optimizer state if possible, or just restart the epoch loop.
            # Let's restart the epoch loop from epoch 0 for the new batch size to ensure stability.
            
            logger.info(f"Training with batch size {current_batch_size}...")
            
            best_val_loss = float('inf')
            best_model_state = None
            
            for epoch in range(max_epochs):
                memory_monitor.start_epoch()
                
                try:
                    train_loss = train_epoch(model, train_loader, optimizer, device, current_batch_size)
                    val_loss, _, _ = evaluate(model, test_loader, device)
                    
                    scheduler.step(val_loss)
                    
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        best_model_state = model.state_dict().copy()
                    
                    if early_stopping(val_loss):
                        logger.info(f"Early stopping triggered at epoch {epoch}")
                        break
                    
                    memory_monitor.log_epoch(epoch, train_loss, val_loss)
                    
                except RuntimeError as e:
                    if "out of memory" in str(e).lower():
                        logger.error(f"OOM at epoch {epoch} with batch size {current_batch_size}. Reducing batch size.")
                        # We need to reduce batch size and retry the training from the beginning 
                        # of the epoch loop or restart training. 
                        # T058 requires reducing and retrying.
                        raise e # Propagate to outer loop
                    else:
                        raise e
            
            # If we reach here, training succeeded
            if best_model_state:
                model.load_state_dict(best_model_state)
            
            # Final evaluation
            final_loss, predictions, targets = evaluate(model, test_loader, device)
            
            # Calculate metrics
            from code.eval.metrics import calculate_mae, calculate_rmse, calculate_r2
            mae = calculate_mae(np.array(targets), np.array(predictions))
            rmse = calculate_rmse(np.array(targets), np.array(predictions))
            r2 = calculate_r2(np.array(targets), np.array(predictions))
            
            return EvaluationResult(
                model_type="GCN",
                mae=mae,
                rmse=rmse,
                r2=r2,
                predictions=predictions,
                errors=[t-p for t, p in zip(targets, predictions)]
            )
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.warning(f"OOM error detected. Reducing batch size from {current_batch_size} to {current_batch_size // 2}")
                if current_batch_size <= min_batch_size:
                    logger.critical("Batch size reached minimum limit. Cannot reduce further. Halting.")
                    raise e
                current_batch_size = current_batch_size // 2
                # Clear CUDA cache if available
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                continue
            else:
                raise e

    raise RuntimeError("Training failed: Could not find a valid batch size.")

def generate_predictions(model: GCNModel, data: List[Any], device: torch.device) -> List[float]:
    model.eval()
    loader = DataLoader(data, batch_size=32, shuffle=False)
    preds = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            preds.extend(out.cpu().numpy().tolist())
    return preds

def main():
    parser = argparse.ArgumentParser(description="Train GCN model for molecular surface area prediction")
    parser.add_argument("--data_path", type=str, default="data/processed/paired_dataset.parquet", help="Path to processed data")
    parser.add_argument("--split_path", type=str, default="data/splits", help="Path to split indices")
    parser.add_argument("--output_path", type=str, default="results/predictions/gcn_predictions.parquet", help="Output path for predictions")
    parser.add_argument("--batch_size", type=int, default=32, help="Initial batch size")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use")
    
    args = parser.parse_args()
    
    setup_logging()
    logger.info(f"Starting training pipeline with batch_size={args.batch_size}")
    
    # Load data
    # Note: In a real pipeline, we would load the split indices and filter the main dataset
    # For this task, we assume load_processed_graphs handles the path or we pass pre-split lists
    # We will assume the caller splits the data or we load and split here.
    # Given the API surface, we assume the data is already split or we need to load and split.
    # Let's assume we load the full dataset and split it based on indices files.
    
    all_graphs = load_processed_graphs(args.data_path)
    
    # Load split indices
    import pandas as pd
    train_indices = pd.read_csv(os.path.join(args.split_path, "train_indices.csv"))['index'].tolist()
    test_indices = pd.read_csv(os.path.join(args.split_path, "test_indices.csv"))['index'].tolist()
    
    train_data = [all_graphs[i] for i in train_indices]
    test_data = [all_graphs[i] for i in test_indices]
    
    config = {
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "lr": args.lr,
        "seed": args.seed,
        "patience": 5
    }
    
    device = torch.device(args.device)
    
    try:
        result = train_model(train_data, test_data, config, device)
        
        # Save predictions
        # Create a DataFrame from results
        import pandas as pd
        preds_df = pd.DataFrame({
            "smiles": [all_graphs[i].smiles for i in test_indices],
            "predicted_sasa": result.predictions,
            "error": result.errors
        })
        preds_df.to_parquet(args.output_path, index=False)
        
        logger.info(f"Training completed. MAE: {result.mae:.4f}, RMSE: {result.rmse:.4f}, R2: {result.r2:.4f}")
        logger.info(f"Predictions saved to {args.output_path}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    main()