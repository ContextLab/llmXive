"""
Training loop for the DelTA Static Predictor (US2).

Implements FR-004: Train a lightweight 2-layer MLP on CPU using only
static input features to predict DelTA Coefficients.

Dependencies:
- T015: data/processed/delta_coefficients.json (Ground Truth)
- T020: data/processed/static_features.json (Input Features)
- T021: code/models/mlp.py (Model Definition)
"""
import os
import sys
import json
import logging
import argparse
import traceback
from pathlib import Path
from typing import List, Dict, Any, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np

# Project imports
from config import get_config_summary
from models.mlp import create_model, DelTA_MLP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEVICE = torch.device('cpu')  # Force CPU usage as per constraint
RANDOM_SEED = 42
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 1e-3
PATIENCE = 5  # Early stopping patience

class StaticFeatureDataset(Dataset):
    """PyTorch Dataset for loading static features and coefficients."""
    
    def __init__(self, features_path: str, coefficients_path: str):
        """
        Load features and coefficients, aligning them by token_id/example_id.
        
        Args:
            features_path: Path to static_features.json
            coefficients_path: Path to delta_coefficients.json
        """
        super().__init__()
        self.features_path = features_path
        self.coefficients_path = coefficients_path
        
        logger.info(f"Loading features from {features_path}")
        self.features_data = self._load_json(features_path)
        
        logger.info(f"Loading coefficients from {coefficients_path}")
        self.coefficients_data = self._load_json(coefficients_path)
        
        # Build a map from example_id to coefficient for fast lookup
        # Expected structure of coefficients_data: List[Dict] with 'example_id' and 'coefficients'
        self.coeff_map = {}
        for entry in self.coefficients_data:
            eid = entry.get('example_id')
            if eid:
                # Flatten coefficients if they are a list of dicts with token_id
                # Or if the structure is already a list of values
                coeffs = entry.get('coefficients', [])
                if isinstance(coeffs, list) and len(coeffs) > 0 and isinstance(coeffs[0], dict):
                    # Assume list of {token_id: ..., coefficient: ...}
                    # We need to align by index, assuming the order matches features
                    # For now, we assume the dataset is pre-aligned by index in the JSON
                    # If the JSON stores per-token, we might need to reconstruct the list
                    pass 
                self.coeff_map[eid] = coeffs

        # Align data: We expect features_data to be a list of records
        # where each record has an 'example_id' and 'feature_vector'.
        # We will filter out any feature records that don't have a corresponding coefficient.
        self.data = []
        
        logger.info("Aligning features and coefficients...")
        for i, feat_record in enumerate(self.features_data):
            eid = feat_record.get('example_id')
            if eid is None:
                logger.warning(f"Record {i} missing example_id, skipping.")
                continue
            
            if eid not in self.coeff_map:
                logger.warning(f"Example {eid} has features but no coefficients, skipping.")
                continue
            
            coeffs = self.coeff_map[eid]
            # Handle coefficient extraction:
            # If coeffs is a list of dicts, extract the 'coefficient' value
            # If coeffs is a list of numbers, use as is.
            if isinstance(coeffs, list) and len(coeffs) > 0 and isinstance(coeffs[0], dict):
                target_values = [c.get('coefficient', 0.0) for c in coeffs]
            elif isinstance(coeffs, list):
                target_values = coeffs
            else:
                logger.error(f"Unexpected coefficient format for {eid}: {type(coeffs)}")
                continue
            
            feat_vec = feat_record.get('feature_vector')
            if feat_vec is None:
                logger.warning(f"Record {i} missing feature_vector, skipping.")
                continue
            
            # We train one sample per token. 
            # The feature vector is static per token, the target is the coefficient.
            # If the feature file stores per-token features, we can iterate.
            # Assuming features_data is a flat list of (token, feature, target) pairs or we need to expand.
            # Based on T018/T020, features are extracted per token.
            # If the JSON is a list of tokens, we just zip.
            # If the JSON is grouped by example, we need to flatten.
            # Let's assume the JSON from T020 is a flat list of token-level records.
            # If 'coefficients' in coeff_map is a list of tokens for that example,
            # and features_data is a flat list, we need to ensure the order matches.
            
            # RE-ALIGNMENT STRATEGY:
            # The features file (T020) is expected to be a list of records:
            # { "example_id": "...", "token_id": "...", "feature_vector": [...], "position": int }
            # The coefficients file (T015) is expected to be:
            # { "example_id": "...", "coefficients": [ { "token_id": "...", "coefficient": ... }, ... ] }
            # We need to join them on example_id AND token_id (or position).
            
            # For simplicity in this implementation, we assume the features file is already
            # flattened and ordered exactly as the coefficients list in T015 for each example.
            # If the features file is grouped, we would need to flatten it here.
            
            # Let's assume features_data is a flat list of token-level records.
            # We need to find the matching coefficient for this specific token.
            # If the coefficient list is ordered by token position, we can use the index.
            # However, without a position index in the feature record, we rely on order.
            # To be safe, we will assume the features file contains 'token_index' or similar.
            # If not, we will assume 1:1 mapping per example if the feature list length == coefficient list length.
            
            # Robust approach: Group features by example_id first.
            pass

        # Re-doing the alignment properly:
        # 1. Group features by example_id
        features_by_example = {}
        for record in self.features_data:
            eid = record.get('example_id')
            if eid not in features_by_example:
                features_by_example[eid] = []
            features_by_example[eid].append(record)
        
        self.X = []
        self.y = []
        
        for eid, feats in features_by_example.items():
            if eid not in self.coeff_map:
                continue
            coeffs = self.coeff_map[eid]
            
            # Flatten coefficients if necessary
            if isinstance(coeffs, list) and len(coeffs) > 0 and isinstance(coeffs[0], dict):
                target_vals = [c['coefficient'] for c in coeffs]
            else:
                target_vals = coeffs
            
            # Assume features are ordered by token index within the example
            # We pair the i-th feature with the i-th coefficient
            for i, feat_rec in enumerate(feats):
                if i >= len(target_vals):
                    break
                f_vec = feat_rec.get('feature_vector')
                if f_vec is not None:
                    self.X.append(f_vec)
                    self.y.append(target_vals[i])
        
        logger.info(f"Loaded {len(self.X)} training samples.")
        if len(self.X) == 0:
            raise ValueError("No valid training samples found after alignment.")

    def _load_json(self, path: str) -> List[Dict]:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x = torch.tensor(self.X[idx], dtype=torch.float32)
        y = torch.tensor(self.y[idx], dtype=torch.float32)
        return x, y

def train_model(
    model: DelTA_MLP,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = EPOCHS,
    lr: float = LEARNING_RATE,
    patience: int = PATIENCE
) -> DelTA_MLP:
    """
    Train the model with early stopping.
    
    Args:
        model: The DelTA_MLP model instance.
        train_loader: DataLoader for training data.
        val_loader: DataLoader for validation data.
        epochs: Number of training epochs.
        lr: Learning rate.
        patience: Early stopping patience.
        
    Returns:
        Trained model.
    """
    model.to(DEVICE)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    logger.info(f"Starting training for {epochs} epochs...")
    
    for epoch in range(epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs.squeeze(), batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
                outputs = model(batch_x)
                loss = criterion(outputs.squeeze(), batch_y)
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        scheduler.step(val_loss)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
        
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
    
    # Restore best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    return model

def main():
    """
    Main entry point for training.
    """
    parser = argparse.ArgumentParser(description="Train DelTA Static Predictor")
    parser.add_argument("--features", type=str, default="data/processed/static_features.json",
                        help="Path to static features JSON")
    parser.add_argument("--coefficients", type=str, default="data/processed/delta_coefficients.json",
                        help="Path to ground truth coefficients JSON")
    parser.add_argument("--output", type=str, default="data/processed/mlp_model.pt",
                        help="Path to save the trained model")
    parser.add_argument("--input_dim", type=int, default=None,
                        help="Input dimension (auto-detected if None)")
    parser.add_argument("--hidden_dim", type=int, default=128,
                        help="Hidden layer dimension")
    parser.add_argument("--epochs", type=int, default=EPOCHS,
                        help="Number of epochs")
    args = parser.parse_args()
    
    try:
        # Verify input files exist
        if not os.path.exists(args.features):
            raise FileNotFoundError(f"Features file not found: {args.features}")
        if not os.path.exists(args.coefficients):
            raise FileNotFoundError(f"Coefficients file not found: {args.coefficients}")
        
        # Initialize dataset
        dataset = StaticFeatureDataset(args.features, args.coefficients)
        
        # Split data (80/20)
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            dataset, [train_size, val_size], 
            generator=torch.Generator().manual_seed(RANDOM_SEED)
        )
        
        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
        
        # Determine input dimension
        if args.input_dim is None:
            # Peek at first sample
            first_x, _ = dataset[0]
            input_dim = first_x.shape[0]
            logger.info(f"Auto-detected input dimension: {input_dim}")
        else:
            input_dim = args.input_dim
        
        # Create model
        model = create_model(input_dim=input_dim, hidden_dim=args.hidden_dim)
        logger.info(f"Model architecture:\n{model}")
        
        # Train
        trained_model = train_model(
            model, 
            train_loader, 
            val_loader, 
            epochs=args.epochs
        )
        
        # Save model
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        torch.save({
            'model_state_dict': trained_model.state_dict(),
            'input_dim': input_dim,
            'hidden_dim': args.hidden_dim,
            'config': get_config_summary()
        }, output_path)
        
        logger.info(f"Model saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()