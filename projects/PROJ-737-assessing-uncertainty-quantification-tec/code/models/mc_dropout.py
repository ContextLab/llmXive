"""
Monte Carlo Dropout for UQ.
Implements run_mc_dropout function compatible with pipeline.
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Tuple, Optional, Dict, Any
import logging
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from utils.logger import get_logger

logger = get_logger(__name__)

class SimpleMLP(nn.Module):
    """Simple MLP with dropout for MC Dropout."""
    def __init__(self, input_dim: int, hidden_dims: list = [64, 32], dropout_rate: float = 0.1):
        super(SimpleMLP, self).__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_rate))
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)

class MCDropoutModel:
    """Wrapper for MC Dropout inference."""
    def __init__(self, model: SimpleMLP, n_samples: int = 100, threshold: float = 1e-4):
        self.model = model
        self.n_samples = n_samples
        self.threshold = threshold
    
    @torch.no_grad()
    def predict_uncertain(self, x: torch.Tensor) -> Tuple[np.ndarray, np.ndarray]:
        """Run multiple forward passes with dropout enabled."""
        self.model.train()  # Enable dropout
        predictions = []
        
        for _ in range(self.n_samples):
            pred = self.model(x)
            predictions.append(pred.cpu().numpy())
        
        predictions = np.array(predictions)  # (n_samples, n_test, 1)
        mean = np.mean(predictions, axis=0).squeeze()  # (n_test,)
        std = np.std(predictions, axis=0).squeeze()   # (n_test,)
        
        return mean, std

def run_mc_dropout(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Optional[pd.DataFrame]:
    """
    Run MC Dropout for UQ.
    """
    logger.info("Running MC Dropout model...")
    
    try:
        # Check for GPU availability, fallback to CPU
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
        
        # Initialize model
        input_dim = X_train_scaled.shape[1]
        model = SimpleMLP(input_dim).to(device)
        
        # Training setup
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        
        # Train
        model.train()
        n_epochs = 100
        batch_size = 32
        
        for epoch in range(n_epochs):
            optimizer.zero_grad()
            outputs = model(X_train_tensor).squeeze()
            loss = criterion(outputs, y_train_tensor)
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 20 == 0:
                logger.debug(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")
        
        # Inference with MC Dropout
        mc_model = MCDropoutModel(model, n_samples=50)
        predictions, stds = mc_model.predict_uncertain(X_test_tensor)
        
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
        
        logger.info(f"MC Dropout completed. Predictions: {len(results)}")
        return results
        
    except Exception as e:
        logger.error(f"MC Dropout failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Entry point for testing MC Dropout standalone."""
    logger.info("MC Dropout module loaded. Run via pipeline.py for full execution.")

if __name__ == "__main__":
    main()
