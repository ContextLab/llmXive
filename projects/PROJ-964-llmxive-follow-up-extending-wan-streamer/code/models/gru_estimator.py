import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import json
import logging

# Import shared utilities from the project's API surface
from utils.config import get_config_summary, set_seed
from utils.validators import validate_model_output, ValidationError
from utils.update_state_yaml import compute_file_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """
    Load configuration for the GRU Estimator.
    Returns a dictionary with model hyperparameters and paths.
    """
    config = get_config_summary()
    # Ensure specific keys exist for this model
    if 'gru' not in config:
        config['gru'] = {}
    
    # Defaults if not specified
    defaults = {
        'input_dim': 10,  # Default latent vector dimension
        'hidden_dim': 64,
        'num_layers': 2,
        'dropout': 0.2,
        'learning_rate': 1e-3,
        'batch_size': 32,
        'epochs': 10,
        'checkpoint_path': 'data/models/estimator_checkpoint.pt',
        'seed': 42
    }
    
    for k, v in defaults.items():
        if k not in config['gru']:
            config['gru'][k] = v
    
    return config['gru']

class GRUEstimator(nn.Module):
    """
    Lightweight GRU model for CPU inference.
    Outputs a tensor of shape [batch, 2]:
      - Column 0: Predicted Delta Magnitude
      - Column 1: Uncertainty Score (0.0 - 1.0)
    """
    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int, dropout: float):
        super(GRUEstimator, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # GRU Layer
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        # Fully connected layers for head
        # We map the last hidden state to 2 outputs
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 2)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape [batch, seq_len, input_dim]
        Returns:
            output: Tensor of shape [batch, 2]
        """
        # x shape: (batch, seq_len, input_dim)
        # GRU output: (batch, seq_len, hidden_dim)
        # We only need the last hidden state
        gru_out, hidden = self.gru(x)
        
        # Take the last time step
        last_hidden = gru_out[:, -1, :]  # (batch, hidden_dim)
        
        # Pass through head
        out = self.fc(last_hidden)  # (batch, 2)
        
        # Apply activation to separate concerns
        # Column 0: Delta Magnitude (can be any positive value, use ReLU)
        # Column 1: Uncertainty Score (0-1, use Sigmoid)
        delta_mag = F.relu(out[:, 0:1])
        uncertainty = torch.sigmoid(out[:, 1:2])
        
        return torch.cat([delta_mag, uncertainty], dim=1)

def train_step(model: GRUEstimator, batch: torch.Tensor, targets: torch.Tensor, optimizer: torch.optim.Optimizer, criterion: nn.Module) -> Tuple[float, float]:
    """
    Performs a single training step.
    Args:
        model: The GRU model
        batch: Input tensor [batch, seq_len, input_dim]
        targets: Target tensor [batch, 2] (delta_mag, uncertainty)
        optimizer: Optimizer instance
        criterion: Loss function (e.g., MSELoss)
    Returns:
        loss_value, delta_loss, unc_loss
    """
    model.train()
    optimizer.zero_grad()
    
    outputs = model(batch)
    pred_delta = outputs[:, 0]
    pred_unc = outputs[:, 1]
    target_delta = targets[:, 0]
    target_unc = targets[:, 1]
    
    # Combined loss: MSE for both, weighted equally for now
    # Note: Uncertainty targets should be in [0, 1] for MSE to make sense with sigmoid output
    loss = criterion(pred_delta, target_delta) + criterion(pred_unc, target_unc)
    
    loss.backward()
    optimizer.step()
    
    return loss.item(), criterion(pred_delta, target_delta).item(), criterion(pred_unc, target_unc).item()

def validate_step(model: GRUEstimator, batch: torch.Tensor, targets: torch.Tensor, criterion: nn.Module) -> Tuple[float, float, float]:
    """
    Performs a single validation step.
    """
    model.eval()
    with torch.no_grad():
        outputs = model(batch)
        pred_delta = outputs[:, 0]
        pred_unc = outputs[:, 1]
        target_delta = targets[:, 0]
        target_unc = targets[:, 1]
        
        loss = criterion(pred_delta, target_delta) + criterion(pred_unc, target_unc)
        return loss.item(), criterion(pred_delta, target_delta).item(), criterion(pred_unc, target_unc).item()

def compute_uncertainty_correlation(model: GRUEstimator, data_loader: torch.utils.data.DataLoader, device: torch.device) -> float:
    """
    Computes the correlation between predicted uncertainty and actual error on the validation set.
    Returns Pearson correlation coefficient.
    """
    model.eval()
    all_errors = []
    all_uncertainties = []
    
    with torch.no_grad():
        for batch, targets in data_loader:
            batch = batch.to(device)
            targets = targets.to(device)
            
            outputs = model(batch)
            pred_delta = outputs[:, 0]
            pred_unc = outputs[:, 1]
            target_delta = targets[:, 0]
            
            # Calculate error (absolute difference)
            errors = torch.abs(pred_delta - target_delta)
            
            all_errors.extend(errors.cpu().numpy().flatten())
            all_uncertainties.extend(pred_unc.cpu().numpy().flatten())
    
    all_errors = np.array(all_errors)
    all_uncertainties = np.array(all_uncertainties)
    
    if len(all_errors) < 2:
        logger.warning("Not enough data points to compute correlation.")
        return 0.0
    
    correlation = np.corrcoef(all_uncertainties, all_errors)[0, 1]
    if np.isnan(correlation):
        return 0.0
    
    return float(correlation)

def save_checkpoint(model: GRUEstimator, optimizer: torch.optim.Optimizer, epoch: int, path: str, status: str = 'pending_validation'):
    """
    Saves the model checkpoint.
    Args:
        model: The GRU model
        optimizer: The optimizer
        epoch: Current epoch
        path: Path to save the checkpoint
        status: 'pending_validation' or 'finalized'
    """
    # Ensure directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'status': status,
        'config': load_config() # Save config context
    }
    
    torch.save(checkpoint, path)
    logger.info(f"Checkpoint saved to {path} with status: {status}")
    
    # Update state.yaml with hash if finalized (though task says don't finalize here)
    # We only compute hash here for logging or future use if status changes
    if status == 'finalized':
        file_hash = compute_file_hash(path)
        logger.info(f"Checkpoint hash: {file_hash}")

def load_checkpoint(path: str, model: GRUEstimator, optimizer: Optional[torch.optim.Optimizer] = None) -> Tuple[GRUEstimator, Optional[torch.optim.Optimizer], int, str]:
    """
    Loads a model checkpoint.
    Returns: model, optimizer, epoch, status
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Checkpoint not found at {path}")
    
    checkpoint = torch.load(path, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    
    epoch = checkpoint.get('epoch', 0)
    status = checkpoint.get('status', 'unknown')
    
    if optimizer is not None and 'optimizer_state_dict' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    
    return model, optimizer, epoch, status

def main():
    """
    Main entry point for T018 implementation.
    This script defines the model, creates a dummy training loop to verify architecture,
    and saves a 'pending_validation' checkpoint as required.
    """
    logger.info("Starting T018: Implementing GRU Estimator")
    
    # 1. Load Config
    config = load_config()
    set_seed(config.get('seed', 42))
    
    input_dim = config['input_dim']
    hidden_dim = config['hidden_dim']
    num_layers = config['num_layers']
    dropout = config['dropout']
    learning_rate = config['learning_rate']
    batch_size = config['batch_size']
    epochs = config['epochs']
    checkpoint_path = config['checkpoint_path']
    
    device = torch.device('cpu') # CPU-only constraint
    logger.info(f"Device: {device}")
    
    # 2. Instantiate Model
    model = GRUEstimator(input_dim, hidden_dim, num_layers, dropout).to(device)
    logger.info(f"Model architecture:\n{model}")
    
    # 3. Dummy Data Generation for Verification (Real data loading handled by trainer T019)
    # We create a small synthetic sequence to verify forward pass and output shape
    seq_len = 10
    dummy_batch_size = 4
    dummy_x = torch.randn(dummy_batch_size, seq_len, input_dim)
    dummy_y = torch.rand(dummy_batch_size, 2) # [delta_mag, uncertainty]
    
    # Verify forward pass
    model.eval()
    with torch.no_grad():
        output = model(dummy_x)
    
    assert output.shape == (dummy_batch_size, 2), f"Output shape mismatch: {output.shape}"
    assert torch.all(output[:, 1] >= 0.0) and torch.all(output[:, 1] <= 1.0), "Uncertainty out of bounds"
    assert torch.all(output[:, 0] >= 0.0), "Delta magnitude negative"
    
    logger.info(f"Forward pass verified. Output shape: {output.shape}")
    
    # 4. Setup Training Components (Minimal for verification)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()
    
    # 5. Simulate a few steps to ensure training loop logic is sound
    # In a real run, this would load data from T014/T015 outputs
    logger.info("Running verification training steps...")
    for epoch in range(1, 3): # Just a couple of steps
        # Create a tiny batch
        x_batch = torch.randn(batch_size, seq_len, input_dim)
        y_batch = torch.rand(batch_size, 2)
        
        loss, d_loss, u_loss = train_step(model, x_batch, y_batch, optimizer, criterion)
        if epoch == 1:
            logger.info(f"Epoch {epoch} - Loss: {loss:.4f}, Delta Loss: {d_loss:.4f}, Unc Loss: {u_loss:.4f}")
    
    # 6. Save Checkpoint with 'pending_validation' status
    # Task Requirement: "save checkpoint to data/models/estimator_checkpoint.pt with a pending_validation flag"
    # Task Requirement: "Do NOT finalize the checkpoint; save only as 'pending'"
    
    save_checkpoint(model, optimizer, epoch=2, path=checkpoint_path, status='pending_validation')
    
    # 7. Validation: Verify the file exists and contains the correct status
    if os.path.exists(checkpoint_path):
        chk = torch.load(checkpoint_path, map_location='cpu')
        assert chk['status'] == 'pending_validation', "Checkpoint status is not pending_validation"
        logger.info(f"Successfully saved pending checkpoint at {checkpoint_path}")
    else:
        raise FileNotFoundError("Checkpoint file was not created.")
    
    logger.info("T018 Implementation Complete.")

if __name__ == "__main__":
    main()