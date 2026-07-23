"""
Deep Ensemble for UQ.
Implements run_deep_ensemble function compatible with pipeline.
"""
import os
import gc
import logging
import time
from typing import Tuple, List, Dict, Any, Optional, Callable
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from utils.logger import get_logger

logger = get_logger(__name__)

class SimpleMLP(nn.Module):
    """Simple MLP for ensemble members."""
    def __init__(self, input_dim: int, hidden_dims: list = [64, 32]):
        super(SimpleMLP, self).__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)

class DeepEnsembleModel:
    """Wrapper for Deep Ensemble inference."""
    def __init__(self, models: List[SimpleMLP]):
        self.models = models
        self.n_models = len(models)
    
    @torch.no_grad()
    def predict_ensemble(self, x: torch.Tensor) -> Tuple[np.ndarray, np.ndarray]:
        """Run inference on all ensemble members."""
        predictions = []
        for model in self.models:
            model.eval()
            pred = model(x)
            predictions.append(pred.cpu().numpy())
        
        predictions = np.array(predictions)  # (n_models, n_test, 1)
        mean = np.mean(predictions, axis=0).squeeze()  # (n_test,)
        std = np.std(predictions, axis=0).squeeze()   # (n_test,)
        
        return mean, std

def run_deep_ensemble(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Optional[pd.DataFrame]:
    """
    Run Deep Ensemble for UQ.
    """
    logger.info("Running Deep Ensemble model...")
    
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")
        
        # Standardize features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train_scaled).to(device)
        y_train_tensor = torch.FloatTensor(y_train.values).to(device)
        X_test_tensor = torch.FloatTensor(X_test_scaled).to(device)
        
        input_dim = X_train_scaled.shape[1]
        ensemble_size = 3
        models = []
        
        # Train ensemble members
        for i in range(ensemble_size):
            logger.info(f"Training ensemble member {i+1}/{ensemble_size}...")
            model = SimpleMLP(input_dim).to(device)
            
            # Different random seed for each member
            torch.manual_seed(42 + i)
            
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            
            model.train()
            n_epochs = 100
            
            for epoch in range(n_epochs):
                optimizer.zero_grad()
                outputs = model(X_train_tensor).squeeze()
                loss = criterion(outputs, y_train_tensor)
                loss.backward()
                optimizer.step()
            
            models.append(model)
            gc.collect()
        
        # Inference
        ensemble = DeepEnsembleModel(models)
        predictions, stds = ensemble.predict_ensemble(X_test_tensor)
        
        # Calculate 95% CI
        alpha = 1.96
        lower_bound = predictions - alpha * stds
        upper_bound = predictions + alpha * stds
        
        # Create result DataFrame
        results = pd.DataFrame({
            'prediction': predictions,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'ground_truth': y_test.values
        })
        
        logger.info(f"Deep Ensemble completed. Predictions: {len(results)}")
        return results
        
    except Exception as e:
        logger.error(f"Deep Ensemble failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Entry point for testing Deep Ensemble standalone."""
    logger.info("Deep Ensemble module loaded. Run via pipeline.py for full execution.")

if __name__ == "__main__":
    main()
