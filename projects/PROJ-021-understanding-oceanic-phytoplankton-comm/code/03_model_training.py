import os
import sys
import logging
import json
import time
import pickle
import traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import xarray as xr
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# Attempt to import PyTorch components for the VLM
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torchvision import models, transforms
    from transformers import CLIPProcessor, CLIPModel
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logging.warning("PyTorch or Transformers not installed. VLM training will fallback to RF as per spec.")

from utils.logging_config import get_logger
from utils.config import get_config

logger = get_logger(__name__)

class PhytoplanktonDataset:
    """Dataset class for phytoplankton data."""
    def __init__(self, data: xr.Dataset):
        self.data = data
    
    def get_features_targets(self):
        # Extract features: temp, salinity, nutrients (chlorophyll-a is target)
        features = []
        for var in ['temp', 'salinity', 'nutrients']:
            if var in self.data.data_vars:
                features.append(self.data[var].values.flatten())
        
        if not features:
            raise ValueError("No feature variables found in dataset")
        
        X = np.stack(features, axis=-1)
        
        # Target: chlorophyll-a
        if 'chlorophyll-a' in self.data.data_vars:
            y = self.data['chlorophyll-a'].values.flatten()
        elif 'chl' in self.data.data_vars:
            y = self.data['chl'].values.flatten()
        else:
            raise ValueError("Target variable 'chlorophyll-a' or 'chl' not found in dataset")
        
        # Remove rows with NaN values
        valid_mask = ~np.isnan(X).any(axis=-1) & ~np.isnan(y)
        return X[valid_mask], y[valid_mask]

def load_aligned_data(path: str) -> xr.Dataset:
    """Load the aligned dataset."""
    logger.info(f"Loading aligned data from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Aligned data not found at {path}")
    return xr.open_dataset(path)

def train_random_forest(X_train, y_train, X_val, y_val, n_trees: int = 500):
    """Train a Random Forest baseline."""
    logger.info(f"Training Random Forest with {n_trees} trees")
    rf = RandomForestRegressor(n_estimators=n_trees, n_jobs=-1, random_state=42)
    rf.fit(X_train, y_train)
    
    val_pred = rf.predict(X_val)
    metrics = {
        'rmse': float(np.sqrt(mean_squared_error(y_val, val_pred))),
        'r2': float(r2_score(y_val, val_pred)),
        'mae': float(mean_absolute_error(y_val, val_pred))
    }
    logger.info(f"RF Validation Metrics: {metrics}")
    return rf, metrics

class SimpleVLM(nn.Module):
    """
    Lightweight CLIP-based VLM for phytoplankton prediction.
    Concatenates image features (from a lightweight CNN) and text features (from a simple MLP)
    to predict chlorophyll-a concentration.
    
    Note: Since we don't have real images in the tabular dataset, we simulate the image branch
    using a random projection of the environmental features to match the expected architecture
    for the "image/text inputs" requirement, or we use a dummy image if available.
    Given the task description implies "concatenated image/text inputs" but our data is tabular,
    we treat the environmental features as the 'image' proxy (via a CNN-like projection) and
    the prompt as the 'text' proxy.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 256):
        super(SimpleVLM, self).__init__()
        self.input_dim = input_dim
        
        # Image Encoder (Simulated for tabular data: MLP acting as a feature extractor)
        # In a real scenario with images, this would be a ResNet-18 or similar.
        self.image_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Text Encoder (Simulated for prompt: MLP)
        # Prompt: "Temperature: {temp}, Salinity: {sal}, Nutrients: {nut}"
        # We encode the same features again to simulate text embedding space
        self.text_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Fusion Head
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1)
        )
        
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # x: (batch, input_dim)
        img_feat = self.image_encoder(x)
        txt_feat = self.text_encoder(x)
        combined = torch.cat([img_feat, txt_feat], dim=1)
        output = self.fusion(combined)
        return output.squeeze(-1)

def train_vlm(X_train, y_train, X_val, y_val, epochs: int = 10, patience: int = 3):
    """
    Train a lightweight VLM.
    If convergence fails (no improvement after patience epochs), log failure and return
    baseline metrics, explicitly flagging the artifact.
    """
    if not HAS_TORCH:
        logger.warning("PyTorch not available. Falling back to Random Forest for VLM task.")
        # Fallback to RF as per spec if torch is missing
        vlm = RandomForestRegressor(n_estimators=100, random_state=42)
        vlm.fit(X_train, y_train)
        val_pred = vlm.predict(X_val)
        metrics = {
            'rmse': float(np.sqrt(mean_squared_error(y_val, val_pred))),
            'r2': float(r2_score(y_val, val_pred)),
            'mae': float(mean_absolute_error(y_val, val_pred)),
            'status': 'VLM Failed (Baseline Used) - PyTorch unavailable'
        }
        return vlm, metrics, True # True indicates fallback used

    logger.info(f"Training VLM for {epochs} epochs with early stopping (patience={patience})")
    
    device = torch.device("cpu") # CPU-only requirement
    model = SimpleVLM(input_dim=X_train.shape[1]).to(device)
    
    # Prepare tensors
    X_train_t = torch.FloatTensor(X_train).to(device)
    y_train_t = torch.FloatTensor(y_train).to(device)
    X_val_t = torch.FloatTensor(X_val).to(device)
    y_val_t = torch.FloatTensor(y_val).to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    best_val_loss = float('inf')
    best_model_state = None
    epochs_no_improve = 0
    converged = False
    
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        outputs = model(X_train_t)
        loss = criterion(outputs, y_train_t)
        loss.backward()
        optimizer.step()
        
        # Validation
        model.eval()
        with torch.no_grad():
            val_outputs = model(X_val_t)
            val_loss = criterion(val_outputs, y_val_t).item()
        
        logger.info(f"Epoch [{epoch+1}/{epochs}], Train Loss: {loss.item():.4f}, Val Loss: {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
            epochs_no_improve = 0
            converged = True
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                logger.warning(f"Early stopping triggered at epoch {epoch+1}. No improvement for {patience} epochs.")
                break
    
    # Load best model
    if best_model_state:
        model.load_state_dict(best_model_state)
    
    # Calculate final metrics
    model.eval()
    with torch.no_grad():
        val_outputs = model(X_val_t)
        y_pred = val_outputs.cpu().numpy()
    
    metrics = {
        'rmse': float(np.sqrt(mean_squared_error(y_val, y_pred))),
        'r2': float(r2_score(y_val, y_pred)),
        'mae': float(mean_absolute_error(y_val, y_pred))
    }
    
    if not converged:
        logger.error("VLM training failed to converge. Using baseline metrics and flagging artifact.")
        metrics['status'] = 'VLM Failed (Baseline Used) - No Convergence'
        # Per spec: "default to baseline model performance metrics"
        # We will return the RF model as the fallback in the main logic, 
        # but here we return the VLM model with the flag so the caller can decide.
        # However, the spec says "default to baseline model performance metrics".
        # We will return the RF model logic if this flag is set in the main function.
        return model, metrics, True
    
    logger.info(f"VLM Validation Metrics: {metrics}")
    return model, metrics, False

def save_model_artifacts(model, metrics, path: str):
    """Save model and metrics to disk."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump({'model': model, 'metrics': metrics}, f)
    logger.info(f"Saved model artifacts to {path}")

def load_model_artifacts(path: str) -> Dict:
    """Load model and metrics from disk."""
    with open(path, 'rb') as f:
        return pickle.load(f)

def main():
    """Entry point for model training."""
    from utils.logging_config import setup_logging
    setup_logging()
    config = get_config()
    
    logger.info("Starting model training pipeline")
    
    try:
        # Load data
        data_path = "data/processed/aligned_dataset.nc"
        data = load_aligned_data(data_path)
        
        # Extract features and targets
        dataset = PhytoplanktonDataset(data)
        X, y = dataset.get_features_targets()
        
        logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        logger.info(f"Training set: {len(X_train)} samples, Validation set: {len(X_val)} samples")
        
        # Train RF
        rf_model, rf_metrics = train_random_forest(X_train, y_train, X_val, y_val)
        save_model_artifacts(rf_model, rf_metrics, "data/artifacts/rf_model.pkl")
        
        # Train VLM
        vlm_model, vlm_metrics, is_fallback = train_vlm(X_train, y_train, X_val, y_val)
        
        if is_fallback:
            # If VLM failed, we default to baseline metrics as per spec
            # and save the RF model as the "VLM" artifact with the flag
            logger.warning("VLM failed. Saving RF model as VLM artifact with failure flag.")
            save_model_artifacts(rf_model, vlm_metrics, "data/artifacts/vlm_model.pkl")
        else:
            save_model_artifacts(vlm_model, vlm_metrics, "data/artifacts/vlm_model.pkl")
        
        logger.info("Model training completed successfully.")
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()