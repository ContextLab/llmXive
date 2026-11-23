"""
Train GCN and Random Forest models using scaffold-aware cross-validation.
Implements core training loop with timeout enforcement and CPU-only execution.
"""
import os
import sys
import logging
import time
import signal
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import torch
import numpy as np
import pandas as pd
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from utils.config import get_config, ensure_dirs
from utils.logger import setup_logger
from data.split import scaffold_split, save_split_indices
from models.gcn import create_gcn_model, GCN
from models.rf import generate_morgan_fingerprints, train_random_forest, save_model_and_metrics

# Setup logging
logger = setup_logger()

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Training timeout exceeded")

def train_gcn_fold(
    train_data: List[Data],
    val_data: List[Data],
    fold_idx: int,
    config: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, float]:
    """
    Train a single GCN fold with timeout enforcement.
    Returns metrics: MAE, RMSE, R2.
    """
    device = torch.device('cpu')  # Force CPU as per requirements
    
    # Create model
    model = create_gcn_model(
        node_dim=config['node_feature_dim'],
        edge_dim=config['edge_feature_dim'],
        hidden_dim=config['gcn_hidden_dim'],
        num_layers=config['gcn_num_layers'],
        num_classes=1
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
    criterion = torch.nn.MSELoss()
    
    train_loader = DataLoader(train_data, batch_size=config['batch_size'], shuffle=True)
    val_loader = DataLoader(val_data, batch_size=config['batch_size'], shuffle=False)
    
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    epochs = config['max_epochs']
    timeout_seconds = config['fold_timeout_seconds']
    
    logger.info(f"Starting GCN training for fold {fold_idx} with {epochs} epochs and {timeout_seconds}s timeout")
    
    start_time = time.time()
    
    try:
        for epoch in range(epochs):
            # Check timeout before each epoch
            if time.time() - start_time > timeout_seconds:
                logger.warning(f"Fold {fold_idx}: Timeout reached at epoch {epoch}. Saving partial model.")
                break
            
            # Training phase
            model.train()
            total_train_loss = 0.0
            for batch in train_loader:
                batch = batch.to(device)
                optimizer.zero_grad()
                out = model(batch.x, batch.edge_index, batch.edge_attr).squeeze()
                loss = criterion(out, batch.y)
                loss.backward()
                optimizer.step()
                total_train_loss += loss.item()
            
            avg_train_loss = total_train_loss / len(train_loader)
            
            # Validation phase
            model.eval()
            total_val_loss = 0.0
            all_preds = []
            all_targets = []
            
            with torch.no_grad():
                for batch in val_loader:
                    batch = batch.to(device)
                    out = model(batch.x, batch.edge_index, batch.edge_attr).squeeze()
                    loss = criterion(out, batch.y)
                    total_val_loss += loss.item()
                    all_preds.extend(out.cpu().numpy())
                    all_targets.extend(batch.y.cpu().numpy())
            
            avg_val_loss = total_val_loss / len(val_loader)
            
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                best_model_state = model.state_dict().copy()
                patience_counter = 0
            else:
                patience_counter += 1
            
            if patience_counter >= config['patience']:
                logger.info(f"Fold {fold_idx}: Early stopping at epoch {epoch}")
                break
            
            if epoch % 10 == 0:
                logger.info(f"Fold {fold_idx} | Epoch {epoch} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
            
            # Check timeout after epoch
            if time.time() - start_time > timeout_seconds:
                logger.warning(f"Fold {fold_idx}: Timeout reached after epoch {epoch}. Saving partial model.")
                break
            
    except TimeoutError:
        logger.error(f"Fold {fold_idx}: Training terminated due to timeout")
    
    # Load best model for final evaluation
    if best_model_state:
        model.load_state_dict(best_model_state)
    
    # Final evaluation on validation set
    model.eval()
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for batch in val_loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.edge_attr).squeeze()
            all_preds.extend(out.cpu().numpy())
            all_targets.extend(batch.y.cpu().numpy())
    
    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    
    mae = mean_absolute_error(all_targets, all_preds)
    rmse = np.sqrt(mean_squared_error(all_targets, all_preds))
    r2 = r2_score(all_targets, all_preds)
    
    metrics = {
        'fold': fold_idx,
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'status': 'completed' if time.time() - start_time <= timeout_seconds else 'timeout'
    }
    
    logger.info(f"Fold {fold_idx} metrics: MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}, Status={metrics['status']}")
    
    # Save partial model if timeout occurred
    if metrics['status'] == 'timeout' and best_model_state:
        model.load_state_dict(best_model_state)
        model_path = Path(config['results_dir']) / 'model_artifacts' / f'gcn_fold_{fold_idx}_partial.pt'
        torch.save({
            'model_state_dict': model.state_dict(),
            'fold': fold_idx,
            'status': 'timeout'
        }, model_path)
        logger.info(f"Saved partial model for fold {fold_idx} to {model_path}")
    
    return metrics

def train_rf_fold(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    fold_idx: int,
    config: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, float]:
    """
    Train a single Random Forest fold.
    Returns metrics: MAE, RMSE, R2.
    """
    logger.info(f"Starting RF training for fold {fold_idx}")
    
    rf_model = RandomForestRegressor(
        n_estimators=config['rf_n_estimators'],
        max_depth=config['rf_max_depth'],
        random_state=config['seed'],
        n_jobs=1  # Single thread for consistency
    )
    
    rf_model.fit(X_train, y_train)
    
    y_pred_train = rf_model.predict(X_train)
    y_pred_val = rf_model.predict(X_val)
    
    train_mae = mean_absolute_error(y_train, y_pred_train)
    val_mae = mean_absolute_error(y_val, y_pred_val)
    val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))
    val_r2 = r2_score(y_val, y_pred_val)
    
    metrics = {
        'fold': fold_idx,
        'mae': val_mae,
        'rmse': val_rmse,
        'r2': val_r2,
        'train_mae': train_mae,
        'status': 'completed'
    }
    
    logger.info(f"Fold {fold_idx} RF metrics: MAE={val_mae:.4f}, RMSE={val_rmse:.4f}, R2={val_r2:.4f}")
    
    # Save model
    save_model_and_metrics(
        model=rf_model,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        fold_idx=fold_idx,
        output_dir=Path(config['results_dir']) / 'model_artifacts',
        logger=logger
    )
    
    return metrics

def main():
    """
    Main training pipeline:
    1. Load preprocessed data
    2. Perform scaffold split
    3. Train GCN and RF models for each fold
    4. Save fold-wise metrics to results/fold_metrics.json
    """
    config = get_config()
    ensure_dirs(config)
    
    logger.info("Starting model training pipeline")
    
    # Load preprocessed graph data
    graph_data_path = Path(config['processed_data_dir']) / 'graph_data.pt'
    if not graph_data_path.exists():
        logger.error(f"Graph data not found at {graph_data_path}. Run preprocessing first.")
        sys.exit(1)
    
    # Load data
    from torch_geometric.data import HeteroData
    import torch
    
    # Load the preprocessed data
    data_list = torch.load(graph_data_path)
    logger.info(f"Loaded {len(data_list)} molecules from {graph_data_path}")
    
    # Extract targets
    y_all = torch.cat([data.y for data in data_list]).numpy()
    
    # Perform scaffold split
    logger.info("Performing scaffold-aware split...")
    split_indices = scaffold_split(
        data_list=data_list,
        n_folds=config['n_folds'],
        seed=config['seed']
    )
    
    # Save split indices for reproducibility
    save_split_indices(
        split_indices=split_indices,
        output_path=Path(config['results_dir']) / 'scaffold_splits.json'
    )
    
    # Prepare fingerprint data for RF
    logger.info("Generating Morgan fingerprints for Random Forest...")
    # Re-load raw data for SMILES to generate fingerprints
    raw_data_path = Path(config['processed_data_dir']) / 'cleaned_data.csv'
    if not raw_data_path.exists():
        logger.error(f"Cleaned data not found at {raw_data_path}")
        sys.exit(1)
    
    df = pd.read_csv(raw_data_path)
    smiles_list = df['canonical_smiles'].tolist()
    
    # Generate fingerprints for all molecules
    fingerprints = generate_morgan_fingerprints(smiles_list, radius=2, n_bits=2048)
    X_all = np.array(fingerprints)
    
    # Initialize storage for fold metrics
    all_fold_metrics = {
        'gcn': [],
        'rf': []
    }
    
    results_dir = Path(config['results_dir'])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Train for each fold
    for fold_idx in range(config['n_folds']):
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing fold {fold_idx + 1}/{config['n_folds']}")
        logger.info(f"{'='*50}")
        
        train_idx = split_indices[fold_idx]['train']
        val_idx = split_indices[fold_idx]['val']
        
        # GCN Training
        logger.info(f"Training GCN on fold {fold_idx}...")
        train_data_gcn = [data_list[i] for i in train_idx]
        val_data_gcn = [data_list[i] for i in val_idx]
        
        gcn_metrics = train_gcn_fold(
            train_data=train_data_gcn,
            val_data=val_data_gcn,
            fold_idx=fold_idx,
            config=config,
            logger=logger
        )
        all_fold_metrics['gcn'].append(gcn_metrics)
        
        # RF Training
        logger.info(f"Training Random Forest on fold {fold_idx}...")
        X_train_rf = X_all[train_idx]
        y_train_rf = y_all[train_idx]
        X_val_rf = X_all[val_idx]
        y_val_rf = y_all[val_idx]
        
        rf_metrics = train_rf_fold(
            X_train=X_train_rf,
            y_train=y_train_rf,
            X_val=X_val_rf,
            y_val=y_val_rf,
            fold_idx=fold_idx,
            config=config,
            logger=logger
        )
        all_fold_metrics['rf'].append(rf_metrics)
    
    # Save fold-wise metrics
    output_path = results_dir / 'fold_metrics.json'
    with open(output_path, 'w') as f:
        json.dump(all_fold_metrics, f, indent=2)
    
    logger.info(f"Saved fold-wise metrics to {output_path}")
    logger.info("Training pipeline completed successfully")
    
    # Exit with appropriate code
    timeout_found = any(m['status'] == 'timeout' for m in all_fold_metrics['gcn'])
    if timeout_found:
        logger.warning("One or more folds hit the timeout limit.")
        sys.exit(124)  # Standard timeout exit code
    
    sys.exit(0)

if __name__ == '__main__':
    main()
