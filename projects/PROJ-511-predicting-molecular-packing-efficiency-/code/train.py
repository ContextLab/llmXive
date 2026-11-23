"""
train.py - Train a Multi-Layer Perceptron to predict CAPE.

Inputs:
  - data/features_matrix.npy (Base features: Transformer embeddings + 3D descriptors + confounders)
  - data/targets.npy (CAPE values)

Outputs:
  - models/mlp.pt (Trained model weights)

Architecture:
  Input -> Hidden (ReLU) -> Dropout(0.1) -> Hidden (ReLU) -> Dropout(0.1) -> Output
  Total parameters <= 100,000 (FR-005).
"""
import os
import sys
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from typing import Tuple, Dict, Any

# Project imports
from config import get_models_dir, get_base_dir
from utils import fix_seed, setup_logging

# Constants
RANDOM_SEED = 42
DEVICE = torch.device("cpu")  # Enforce CPU for reproducibility on free runners
LEARNING_RATE = 1e-3
BATCH_SIZE = 32
EPOCHS = 100
DROPOUT_RATE = 0.1
MAX_PARAMS = 100000

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class MLP(nn.Module):
    """
    Multi-Layer Perceptron for CAPE prediction.
    Architecture: Input -> Hidden1 -> ReLU -> Dropout -> Hidden2 -> ReLU -> Dropout -> Output
    """
    def __init__(self, input_dim: int, hidden_dim1: int, hidden_dim2: int, output_dim: int = 1):
        super(MLP, self).__init__()
        self.layer1 = nn.Linear(input_dim, hidden_dim1)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(DROPOUT_RATE)
        
        self.layer2 = nn.Linear(hidden_dim1, hidden_dim2)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(DROPOUT_RATE)
        
        self.output_layer = nn.Linear(hidden_dim2, output_dim)
        
        # Calculate total parameters for verification
        total_params = sum(p.numel() for p in self.parameters())
        logger.info(f"Model initialized with {total_params:,} trainable parameters.")
        if total_params > MAX_PARAMS:
            logger.warning(f"Parameter count ({total_params}) exceeds limit ({MAX_PARAMS}).")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.dropout1(self.relu1(self.layer1(x)))
        x = self.dropout2(self.relu2(self.layer2(x)))
        return self.output_layer(x)

def load_data() -> Tuple[np.ndarray, np.ndarray]:
    """Load feature matrix and targets from disk."""
    features_path = os.path.join(get_base_dir(), "data", "features_matrix.npy")
    targets_path = os.path.join(get_base_dir(), "data", "targets.npy")

    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Feature matrix not found at {features_path}. "
                                "Ensure T024 (feature_assembly.py) has run successfully.")
    if not os.path.exists(targets_path):
        raise FileNotFoundError(f"Targets not found at {targets_path}. "
                                "Ensure T024 (feature_assembly.py) has run successfully.")

    logger.info(f"Loading features from {features_path}...")
    X = np.load(features_path)
    logger.info(f"Loading targets from {targets_path}...")
    y = np.load(targets_path)

    if X.shape[0] != y.shape[0]:
        raise ValueError(f"Shape mismatch: Features {X.shape[0]} vs Targets {y.shape[0]}")
    
    logger.info(f"Data loaded: {X.shape[0]} samples, {X.shape[1]} features.")
    return X, y

def train_model(X: np.ndarray, y: np.ndarray) -> MLP:
    """Train the MLP model."""
    fix_seed(RANDOM_SEED)
    
    # Convert to PyTorch tensors
    X_tensor = torch.FloatTensor(X).to(DEVICE)
    y_tensor = torch.FloatTensor(y).reshape(-1, 1).to(DEVICE)

    dataset = TensorDataset(X_tensor, y_tensor)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    input_dim = X.shape[1]
    # Heuristic for hidden dimensions to stay under 100k params
    # Params ~ (Input * H1) + (H1 * H2) + (H2 * 1)
    # If Input is ~768 (BERT) + 3 (desc) + 3 (conf) ~ 774
    # Try H1=128, H2=64 -> 774*128 + 128*64 + 64*1 = 99072 + 8192 + 64 ~ 107k (slightly over)
    # Try H1=100, H2=50 -> 774*100 + 100*50 + 50*1 = 77400 + 5000 + 50 = 82450 (Safe)
    hidden_dim1 = 100
    hidden_dim2 = 50

    model = MLP(input_dim, hidden_dim1, hidden_dim2).to(DEVICE)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    logger.info(f"Starting training for {EPOCHS} epochs...")
    
    best_loss = float('inf')
    patience = 10
    patience_counter = 0

    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0.0
        for batch_X, batch_y in dataloader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(dataloader)

        # Early stopping check
        if avg_loss < best_loss:
            best_loss = avg_loss
            patience_counter = 0
            # Save best model state
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1

        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch [{epoch+1}/{EPOCHS}], Loss: {avg_loss:.6f}")

        if patience_counter >= patience:
            logger.info(f"Early stopping triggered at epoch {epoch+1}")
            break

    # Load best model
    model.load_state_dict(best_model_state)
    return model

def save_model(model: MLP) -> str:
    """Save the trained model to disk."""
    models_dir = get_models_dir()
    os.makedirs(models_dir, exist_ok=True)
    output_path = os.path.join(models_dir, "mlp.pt")
    
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_dim': model.layer1.in_features,
        'hidden_dim1': model.layer1.out_features,
        'hidden_dim2': model.layer2.out_features,
        'dropout_rate': DROPOUT_RATE
    }, output_path)
    
    logger.info(f"Model saved to {output_path}")
    return output_path

def main():
    """Main entry point for training."""
    try:
        # 1. Load Data
        X, y = load_data()

        # 2. Train Model
        model = train_model(X, y)

        # 3. Save Model
        save_model(model)

        logger.info("Training pipeline completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Training failed with unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())