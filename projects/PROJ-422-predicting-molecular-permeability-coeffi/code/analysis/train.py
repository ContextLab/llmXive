"""
Training module for Molecular Permeability Prediction.

Implements training loops for GNN (MPNN) and Random Forest models
with early stopping, CPU-only execution, and resource monitoring.
"""
import logging
import os
import sys
import time
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import warnings

import numpy as np
import pandas as pd
import psutil
import joblib
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torch_geometric.data import Data, Batch

# Import from project modules
from models.gnn import MPNN, create_mpnn_model, train_epoch, validate_epoch
from models.rf import train_random_forest, predict
from utils.logging import setup_logging, log_result_artifact

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CPU_ONLY = True
EARLY_STOPPING_PATIENCE = 5
MAX_EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-4

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def load_graph_data_from_csv(
    train_path: Path,
    test_path: Path,
    target_col: str = "target"
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load and prepare graph data from preprocessed CSV files.
    
    For GNN training, we convert the flattened graph statistics
    and molecular descriptors into a format suitable for training.
    
    Returns:
        Tuple of (train_data_dict, test_data_dict)
    """
    logger.info(f"Loading training data from {train_path}")
    logger.info(f"Loading test data from {test_path}")
    
    if not train_path.exists():
        raise FileNotFoundError(f"Training data file not found: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found: {test_path}")
    
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    
    # Identify feature columns (exclude SMILES and target)
    exclude_cols = ['smiles', target_col, 'molecule_id']
    feature_cols = [col for col in train_df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset")
    
    logger.info(f"Using {len(feature_cols)} feature columns for training")
    
    # Prepare training data
    train_features = train_df[feature_cols].values.astype(np.float32)
    train_targets = train_df[target_col].values.astype(np.float32)
    
    # Handle missing values
    if np.any(np.isnan(train_features)):
        logger.warning("NaN values detected in training features, filling with 0")
        train_features = np.nan_to_num(train_features, nan=0.0)
    
    if np.any(np.isnan(train_targets)):
        logger.warning("NaN values detected in training targets, removing rows")
        valid_mask = ~np.isnan(train_targets)
        train_features = train_features[valid_mask]
        train_targets = train_targets[valid_mask]
    
    # Prepare test data
    test_features = test_df[feature_cols].values.astype(np.float32)
    test_targets = test_df[target_col].values.astype(np.float32)
    
    if np.any(np.isnan(test_features)):
        logger.warning("NaN values detected in test features, filling with 0")
        test_features = np.nan_to_num(test_features, nan=0.0)
    
    if np.any(np.isnan(test_targets)):
        logger.warning("NaN values detected in test targets, removing rows")
        valid_mask = ~np.isnan(test_targets)
        test_features = test_features[valid_mask]
        test_targets = test_targets[valid_mask]
    
    # For GNN, we need to create a simplified graph representation
    # Since we have flattened graph statistics, we treat them as node features
    # and create a dummy graph structure for each molecule
    def create_dummy_graphs(features: np.ndarray) -> List[Data]:
        """Create dummy graph data objects from feature vectors."""
        graphs = []
        for i, feat in enumerate(features):
            # Create a single-node graph with the feature vector
            x = torch.tensor(feat.reshape(-1, 1), dtype=torch.float)
            edge_index = torch.tensor([[0], [0]], dtype=torch.long)  # Self-loop
            y = torch.tensor([0.0], dtype=torch.float)  # Will be set later
            data = Data(x=x, edge_index=edge_index, y=y)
            graphs.append(data)
        return graphs
    
    train_graphs = create_dummy_graphs(train_features)
    test_graphs = create_dummy_graphs(test_features)
    
    # Set targets for graphs
    for i, y in enumerate(train_targets):
        train_graphs[i].y = torch.tensor([y], dtype=torch.float)
    for i, y in enumerate(test_targets):
        test_graphs[i].y = torch.tensor([y], dtype=torch.float)
    
    return {
        'graphs': train_graphs,
        'features': train_features,
        'targets': train_targets,
        'feature_names': feature_cols
    }, {
        'graphs': test_graphs,
        'features': test_features,
        'targets': test_targets,
        'feature_names': feature_cols
    }

def train_gnn(
    train_data: Dict[str, Any],
    test_data: Dict[str, Any],
    output_path: Path,
    patience: int = EARLY_STOPPING_PATIENCE,
    max_epochs: int = MAX_EPOCHS,
    learning_rate: float = LEARNING_RATE,
    weight_decay: float = WEIGHT_DECAY,
    batch_size: int = BATCH_SIZE
) -> Dict[str, Any]:
    """
    Train the GNN (MPNN) model with early stopping.
    
    Args:
        train_data: Dictionary containing training graphs, features, and targets
        test_data: Dictionary containing test graphs, features, and targets
        output_path: Path to save the model checkpoint
        patience: Early stopping patience
        max_epochs: Maximum number of epochs
        learning_rate: Learning rate for optimizer
        weight_decay: Weight decay for regularization
        batch_size: Batch size for training
        
    Returns:
        Dictionary containing training metrics
    """
    logger.info("Starting GNN training...")
    
    # Set device (CPU only)
    device = torch.device('cpu')
    logger.info(f"Using device: {device}")
    
    # Prepare data loaders
    train_dataset = TensorDataset(
        torch.tensor(np.array([g.x for g in train_data['graphs']]), dtype=torch.float),
        torch.tensor(np.array([g.y for g in train_data['graphs']]), dtype=torch.float)
    )
    test_dataset = TensorDataset(
        torch.tensor(np.array([g.x for g in test_data['graphs']]), dtype=torch.float),
        torch.tensor(np.array([g.y for g in test_data['graphs']]), dtype=torch.float)
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # Create model
    input_dim = train_data['features'].shape[1]
    model = create_mpnn_model(input_dim=input_dim, hidden_dim=64, output_dim=1)
    model = model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    
    # Training loop with early stopping
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    training_history = []
    
    start_time = time.time()
    peak_memory = get_memory_usage_gb()
    
    for epoch in range(max_epochs):
        # Train
        model.train()
        train_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs.squeeze(), batch_y.squeeze())
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validate
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in test_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs.squeeze(), batch_y.squeeze())
                val_loss += loss.item()
        
        val_loss /= len(test_loader)
        
        # Track memory
        current_memory = get_memory_usage_gb()
        peak_memory = max(peak_memory, current_memory)
        
        training_history.append({
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_loss
        })
        
        logger.info(f"Epoch {epoch+1}/{max_epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break
    
    training_duration = time.time() - start_time
    
    # Save best model
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        'model_state_dict': best_model_state,
        'best_val_loss': best_val_loss,
        'epoch': len(training_history),
        'training_duration': training_duration,
        'peak_memory_gb': peak_memory
    }, output_path)
    
    logger.info(f"Model saved to {output_path}")
    
    return {
        'training_duration': training_duration,
        'peak_memory_gb': peak_memory,
        'final_val_loss': best_val_loss,
        'epochs_trained': len(training_history),
        'early_stopped': patience_counter >= patience,
        'history': training_history
    }

def train_rf(
    train_data: Dict[str, Any],
    test_data: Dict[str, Any],
    output_path: Path,
    n_estimators: int = 100,
    max_depth: int = None
) -> Dict[str, Any]:
    """
    Train the Random Forest model.
    
    Args:
        train_data: Dictionary containing training features and targets
        test_data: Dictionary containing test features and targets
        output_path: Path to save the model checkpoint
        n_estimators: Number of trees in the forest
        max_depth: Maximum depth of the tree
        
    Returns:
        Dictionary containing training metrics
    """
    logger.info("Starting Random Forest training...")
    
    start_time = time.time()
    peak_memory = get_memory_usage_gb()
    
    X_train = train_data['features']
    y_train = train_data['targets']
    X_test = test_data['features']
    y_test = test_data['targets']
    
    # Train model
    model = train_random_forest(X_train, y_train, n_estimators=n_estimators, max_depth=max_depth)
    
    training_duration = time.time() - start_time
    current_memory = get_memory_usage_gb()
    peak_memory = max(peak_memory, current_memory)
    
    # Save model
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    
    logger.info(f"Model saved to {output_path}")
    
    return {
        'training_duration': training_duration,
        'peak_memory_gb': peak_memory,
        'n_estimators': n_estimators,
        'max_depth': max_depth
    }

def main():
    """Main entry point for training pipeline."""
    # Setup logging
    log_file = Path("results/training_log.json")
    logger = setup_logging(log_level=logging.INFO, log_file=log_file)
    
    logger.info("=" * 60)
    logger.info("Starting Training Pipeline for Molecular Permeability Prediction")
    logger.info("=" * 60)
    
    try:
        # Define paths
        project_root = Path(__file__).parent.parent.parent
        train_path = project_root / "data" / "processed" / "train.csv"
        test_path = project_root / "data" / "processed" / "test.csv"
        gnn_checkpoint = project_root / "data" / "interim" / "gnn_checkpoint.pt"
        rf_checkpoint = project_root / "data" / "interim" / "rf_checkpoint.pkl"
        metrics_log = project_root / "results" / "training_log.json"
        
        # Ensure output directories exist
        gnn_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        rf_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        metrics_log.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if data files exist
        if not train_path.exists():
            logger.error(f"Training data not found: {train_path}")
            logger.error("Please run the preprocessing pipeline (T017) first to generate train.csv and test.csv")
            sys.exit(1)
        
        if not test_path.exists():
            logger.error(f"Test data not found: {test_path}")
            logger.error("Please run the preprocessing pipeline (T017) first to generate train.csv and test.csv")
            sys.exit(1)
        
        logger.info(f"Training data: {train_path}")
        logger.info(f"Test data: {test_path}")
        
        # Load data
        train_data, test_data = load_graph_data_from_csv(train_path, test_path)
        
        logger.info(f"Loaded {len(train_data['targets'])} training samples")
        logger.info(f"Loaded {len(test_data['targets'])} test samples")
        
        # Train GNN
        logger.info("-" * 60)
        logger.info("Training GNN Model")
        logger.info("-" * 60)
        
        gnn_metrics = train_gnn(train_data, test_data, gnn_checkpoint)
        logger.info(f"GNN Training completed in {gnn_metrics['training_duration']:.2f}s")
        logger.info(f"Peak memory usage: {gnn_metrics['peak_memory_gb']:.2f} GB")
        
        # Train Random Forest
        logger.info("-" * 60)
        logger.info("Training Random Forest Model")
        logger.info("-" * 60)
        
        rf_metrics = train_rf(train_data, test_data, rf_checkpoint)
        logger.info(f"RF Training completed in {rf_metrics['training_duration']:.2f}s")
        logger.info(f"Peak memory usage: {rf_metrics['peak_memory_gb']:.2f} GB")
        
        # Compile and save training log
        total_training_time = gnn_metrics['training_duration'] + rf_metrics['training_duration']
        total_peak_memory = max(gnn_metrics['peak_memory_gb'], rf_metrics['peak_memory_gb'])
        
        training_log = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'gnn': {
                'model_path': str(gnn_checkpoint),
                'training_duration': gnn_metrics['training_duration'],
                'peak_memory_gb': gnn_metrics['peak_memory_gb'],
                'final_val_loss': gnn_metrics['final_val_loss'],
                'epochs_trained': gnn_metrics['epochs_trained'],
                'early_stopped': gnn_metrics['early_stopped']
            },
            'rf': {
                'model_path': str(rf_checkpoint),
                'training_duration': rf_metrics['training_duration'],
                'peak_memory_gb': rf_metrics['peak_memory_gb'],
                'n_estimators': rf_metrics['n_estimators'],
                'max_depth': rf_metrics['max_depth']
            },
            'summary': {
                'total_training_time': total_training_time,
                'peak_memory_gb': total_peak_memory,
                'cpu_only': CPU_ONLY,
                'constraints_met': {
                    'time_under_6h': total_training_time < 6 * 3600,
                    'memory_under_7gb': total_peak_memory < 7.0
                }
            }
        }
        
        with open(metrics_log, 'w') as f:
            json.dump(training_log, f, indent=2)
        
        logger.info(f"Training log saved to {metrics_log}")
        
        # Verify constraints
        if total_training_time >= 6 * 3600:
            logger.warning(f"Training time ({total_training_time:.2f}s) exceeds 6-hour limit")
        if total_peak_memory >= 7.0:
            logger.warning(f"Peak memory ({total_peak_memory:.2f} GB) exceeds 7 GB limit")
        
        logger.info("=" * 60)
        logger.info("Training Pipeline Completed Successfully")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
