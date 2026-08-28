"""
Training loop for GNN and Random Forest models.
Loads processed data, trains models, and saves checkpoints.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data
import joblib

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging import setup_logging, log_result_artifact
from models.gnn import create_mpnn_model, train_epoch, validate_epoch
from models.rf import train_random_forest, predict
from data.split import stratified_split

# Configure logging
logger = setup_logging(level=logging.INFO)

def load_graph_data(csv_path: str) -> tuple:
    """
    Loads data from a processed CSV containing SMILES and target.
    Constructs PyTorch Geometric Data objects and feature matrices.
    """
    df = pd.read_csv(csv_path)
    
    # Validate columns
    required_cols = ['smiles', 'permeability_coefficient']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input CSV must contain columns: {required_cols}")

    logger.info(f"Loaded {len(df)} samples from {csv_path}")

    # We assume the preprocessing step (T014) has already created the 
    # necessary graph structures or descriptor matrices.
    # For this training script, we expect the CSV to have the target and SMILES.
    # If the CSV contains pre-computed adjacency/feature tensors, we load them directly.
    # Otherwise, we construct them on the fly using RDKit (assuming rdkit is available).
    
    # Check for pre-computed graph columns (expected from T014)
    has_node_features = 'node_features' in df.columns
    has_edge_index = 'edge_index' in df.columns

    graphs = []
    X_rf = []
    y = []
    indices = []

    for idx, row in df.iterrows():
        # Target
        target_val = row['permeability_coefficient']
        if pd.isna(target_val):
            continue
        y.append(target_val)
        indices.append(idx)

        # RF Features: If 'descriptors' column exists, use it. Otherwise compute or fail.
        # T014 should have added a 'descriptors' column (list of floats) or flattened them.
        if 'descriptors' in df.columns:
            try:
                # Assuming it's stored as a string representation of a list or JSON
                if isinstance(row['descriptors'], str):
                    # Simple eval for list string, safer parsing preferred in prod
                    feat = eval(row['descriptors']) 
                else:
                    feat = list(row['descriptors'])
                X_rf.append(feat)
            except Exception as e:
                logger.warning(f"Row {idx} descriptor parsing failed: {e}")
                X_rf.append([0.0] * 10) # Fallback placeholder, though T014 should handle this
        else:
            # Fallback: If no descriptors, we cannot train RF. 
            # In a real pipeline, this would be an error or we compute on the fly.
            # For now, we assume T014 ensured this column exists.
            logger.warning(f"Row {idx} missing descriptors. Skipping RF feature extraction.")
            continue

        # GNN Data Construction
        if has_node_features and has_edge_index:
            # Load pre-computed
            node_feat = eval(row['node_features']) if isinstance(row['node_features'], str) else row['node_features']
            edge_idx = eval(row['edge_index']) if isinstance(row['edge_index'], str) else row['edge_index']
            x = torch.tensor(node_feat, dtype=torch.float)
            edge_index = torch.tensor(edge_idx, dtype=torch.long)
            data = Data(x=x, edge_index=edge_index)
        else:
            # Construct from SMILES if not pre-computed (slower, but robust)
            from rdkit import Chem
            from rdkit.Chem import Descriptors as RDKitDescriptors
            
            mol = Chem.MolFromSmiles(row['smiles'])
            if mol is None:
                logger.warning(f"Invalid SMILES at row {idx}, skipping GNN data construction")
                continue
            
            # Simplified graph construction: Nodes = atoms, Edges = bonds
            # Node features: Atomic number, degree, etc.
            # This is a minimal implementation; T014 should ideally produce optimized tensors.
            node_features = []
            edges = []
            
            for atom in mol.GetAtoms():
                # Simple feature vector: [Atomic Num, Degree, Num H, Formal Charge]
                vec = [
                    float(atom.GetAtomicNum()),
                    float(atom.GetDegree()),
                    float(atom.GetTotalNumHs()),
                    float(atom.GetFormalCharge())
                ]
                node_features.append(vec)
            
            for bond in mol.GetBonds():
                edges.append([bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()])
                edges.append([bond.GetEndAtomIdx(), bond.GetBeginAtomIdx()]) # Undirected
            
            if not node_features or not edges:
                continue

            x = torch.tensor(node_features, dtype=torch.float)
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
            data = Data(x=x, edge_index=edge_index)

        graphs.append(data)

    if not graphs:
        raise RuntimeError("No valid graph data constructed from input CSV.")

    return graphs, np.array(y), np.array(X_rf) if X_rf else None

def train_gnn(graphs: list, y: np.ndarray, epochs: int = 50, lr: float = 0.001, 
              batch_size: int = 32, patience: int = 5, device: str = 'cpu'):
    """
    Trains the MPNN model with early stopping.
    """
    logger.info("Starting GNN Training...")
    
    # Split data for early stopping (80/20)
    # We need to split graphs and y
    n = len(graphs)
    indices = list(range(n))
    np.random.seed(42)
    np.random.shuffle(indices)
    split_idx = int(0.8 * n)
    
    train_idx = indices[:split_idx]
    val_idx = indices[split_idx:]
    
    train_data = [graphs[i] for i in train_idx]
    train_y = y[train_idx]
    val_data = [graphs[i] for i in val_idx]
    val_y = y[val_idx]
    
    # Convert to tensors for batching if needed, but MPNN expects Data objects
    # We'll create a simple loader or just iterate
    
    model = create_mpnn_model(input_dim=train_data[0].x.shape[1], device=device)
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.MSELoss()
    
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    for epoch in range(epochs):
        # Training
        model.train()
        total_loss = 0
        for i in range(0, len(train_data), batch_size):
            batch_data = train_data[i:i+batch_size]
            batch_y = torch.tensor(train_y[i:i+batch_size], dtype=torch.float).to(device)
            
            # Forward pass (simplified: assuming model handles list of Data objects or we loop)
            # The create_mpnn_model returns a model that expects a Data object or batch
            # We'll iterate for simplicity in this script, or use a DataLoader if implemented
            batch_preds = []
            batch_loss = 0
            
            for d, target in zip(batch_data, batch_y):
                d = d.to(device)
                pred = model(d)
                loss = criterion(pred, target)
                batch_loss += loss
                batch_preds.append(pred)
            
            avg_batch_loss = batch_loss / len(batch_data)
            optimizer.zero_grad()
            avg_batch_loss.backward()
            optimizer.step()
            total_loss += avg_batch_loss.item()
        
        avg_train_loss = total_loss / (len(train_data) // batch_size + 1)
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for d, target in zip(val_data, val_y):
                d = d.to(device)
                target_t = torch.tensor([target], dtype=torch.float).to(device)
                pred = model(d)
                val_loss += criterion(pred, target_t).item()
        
        avg_val_loss = val_loss / len(val_data)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break
    
    if best_model_state:
        model.load_state_dict(best_model_state)
    return model

def train_rf(X: np.ndarray, y: np.ndarray):
    """
    Trains Random Forest model.
    """
    logger.info("Starting Random Forest Training...")
    if X is None:
        raise ValueError("No feature matrix provided for RF training.")
    
    model = train_random_forest(X, y)
    return model

def main():
    logger.info("=== Starting Training Pipeline ===")
    
    # Paths
    train_csv = PROJECT_ROOT / "data" / "processed" / "train.csv"
    if not train_csv.exists():
        raise FileNotFoundError(f"Training data not found at {train_csv}. Run preprocessing first.")
    
    output_dir = PROJECT_ROOT / "results" / "models"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load Data
    graphs, y, X_rf = load_graph_data(str(train_csv))
    
    if len(graphs) == 0:
        raise RuntimeError("No valid data loaded for training.")
    
    # Train GNN
    gnn_model = train_gnn(graphs, y, epochs=100, patience=10)
    gnn_path = output_dir / "gnn_model.pt"
    torch.save(gnn_model.state_dict(), gnn_path)
    logger.info(f"GNN model saved to {gnn_path}")
    
    # Train RF
    if X_rf is not None:
        rf_model = train_rf(X_rf, y)
        rf_path = output_dir / "rf_model.joblib"
        joblib.dump(rf_model, rf_path)
        logger.info(f"RF model saved to {rf_path}")
    else:
        logger.warning("No RF features found. Skipping RF training.")
        rf_path = None
    
    # Log artifacts
    log_result_artifact("gnn_model_path", str(gnn_path))
    if rf_path:
        log_result_artifact("rf_model_path", str(rf_path))
    
    logger.info("=== Training Complete ===")

if __name__ == "__main__":
    main()