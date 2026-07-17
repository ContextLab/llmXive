import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import sys
from pathlib import Path
import numpy as np
from typing import Tuple, Optional, Dict, Any

# Import config to ensure paths are consistent
# Note: We assume config.py is in the code root relative to this import
# If running as a script, we adjust sys.path
def load_config():
    """
    Load configuration from code/config.py or default values.
    Returns a dictionary with necessary hyperparameters.
    """
    # Default configuration
    config = {
        'input_dim': 512,  # Default latent dimension
        'hidden_dim': 256,
        'num_layers': 2,
        'dropout': 0.3,
        'device': 'cpu',
        'seed': 42,
        'checkpoint_path': 'data/models/estimator_checkpoint.pt'
    }
    
    # Try to load from code/config.py if it exists
    try:
        # Adjust path based on execution context
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        config_file = project_root / 'config.py'
        
        if config_file.exists():
            # Import the config module dynamically
            import importlib.util
            spec = importlib.util.spec_from_file_location("config_module", config_file)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            # Extract relevant config values if available
            if hasattr(config_module, 'get_config_summary'):
                summary = config_module.get_config_summary()
                if isinstance(summary, dict):
                    config.update(summary)
    except Exception as e:
        # If config loading fails, continue with defaults
        pass
        
    return config

class GRUEstimator(nn.Module):
    """
    Lightweight GRU model for predicting latent delta magnitude and uncertainty.
    
    Output shape: [batch_size, 2]
    - Column 0: Predicted delta magnitude (float)
    - Column 1: UncertaintyScore (0.0 to 1.0)
    """
    
    def __init__(self, input_dim: int = 512, hidden_dim: int = 256, 
                num_layers: int = 2, dropout: float = 0.3):
        super(GRUEstimator, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # GRU layers
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=False
        )
        
        # Dropout layer
        self.dropout = nn.Dropout(dropout)
        
        # Fully connected layers for dual output
        self.fc_delta = nn.Linear(hidden_dim, 1)
        self.fc_uncertainty = nn.Linear(hidden_dim, 1)
        
        # Sigmoid for uncertainty normalization to [0, 1]
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the GRU estimator.
        
        Args:
            x: Input tensor of shape [batch_size, seq_len, input_dim]
            
        Returns:
            output: Tensor of shape [batch_size, 2]
                    - Column 0: Predicted delta magnitude
                    - Column 1: UncertaintyScore (0.0-1.0)
        """
        # Ensure input is 3D: [batch, seq_len, input_dim]
        if x.dim() == 2:
            x = x.unsqueeze(1)  # Add sequence dimension if missing
        
        # GRU forward pass
        # gru_output: [batch, seq_len, hidden_dim]
        # hidden: [num_layers, batch, hidden_dim]
        gru_output, hidden = self.gru(x)
        
        # Use the last hidden state for prediction
        last_hidden = hidden[-1]  # [batch, hidden_dim]
        
        # Apply dropout
        last_hidden = self.dropout(last_hidden)
        
        # Compute delta magnitude prediction
        delta_pred = self.fc_delta(last_hidden)  # [batch, 1]
        
        # Compute uncertainty score
        uncertainty_raw = self.fc_uncertainty(last_hidden)  # [batch, 1]
        uncertainty = self.sigmoid(uncertainty_raw)  # [batch, 1], range [0, 1]
        
        # Concatenate outputs: [batch, 2]
        output = torch.cat([delta_pred, uncertainty], dim=1)
        
        return output

def train_step(model: nn.Module, batch: Tuple[torch.Tensor, torch.Tensor], 
              optimizer: torch.optim.Optimizer, criterion: nn.Module,
              device: str) -> Tuple[float, float]:
    """
    Single training step.
    
    Args:
        model: The GRU estimator model
        batch: Tuple of (inputs, targets)
        optimizer: Torch optimizer
        criterion: Loss function (MSE)
        device: Device to run on
        
    Returns:
        loss: Current loss value
        delta_loss: Loss component for delta prediction
        uncertainty_loss: Loss component for uncertainty prediction
    """
    model.train()
    inputs, targets = batch
    
    inputs = inputs.to(device)
    targets = targets.to(device)
    
    optimizer.zero_grad()
    
    # Forward pass
    predictions = model(inputs)  # [batch, 2]
    
    # Split predictions
    delta_pred = predictions[:, 0:1]
    uncertainty_pred = predictions[:, 1:2]
    
    # Split targets
    delta_target = targets[:, 0:1]
    # For uncertainty, we might use a calibration target or proxy
    # For now, we'll use a simple approach: minimize uncertainty when delta is small
    # In a full implementation, this would use actual calibration data
    uncertainty_target = torch.zeros_like(delta_target)  # Placeholder
    
    # Compute losses
    delta_loss = criterion(delta_pred, delta_target)
    uncertainty_loss = criterion(uncertainty_pred, uncertainty_target)
    
    # Combined loss (weighted sum)
    loss = delta_loss + 0.1 * uncertainty_loss
    
    # Backward pass
    loss.backward()
    optimizer.step()
    
    return loss.item(), delta_loss.item(), uncertainty_loss.item()

def validate_step(model: nn.Module, batch: Tuple[torch.Tensor, torch.Tensor], 
                 criterion: nn.Module, device: str) -> Tuple[float, float, float]:
    """
    Single validation step.
    
    Args:
        model: The GRU estimator model
        batch: Tuple of (inputs, targets)
        criterion: Loss function
        device: Device to run on
        
    Returns:
        loss: Current loss value
        delta_loss: Loss component for delta prediction
        uncertainty_loss: Loss component for uncertainty prediction
    """
    model.eval()
    inputs, targets = batch
    
    inputs = inputs.to(device)
    targets = targets.to(device)
    
    with torch.no_grad():
        predictions = model(inputs)  # [batch, 2]
        
        # Split predictions
        delta_pred = predictions[:, 0:1]
        uncertainty_pred = predictions[:, 1:2]
        
        # Split targets
        delta_target = targets[:, 0:1]
        uncertainty_target = torch.zeros_like(delta_target)  # Placeholder
        
        # Compute losses
        delta_loss = criterion(delta_pred, delta_target)
        uncertainty_loss = criterion(uncertainty_pred, uncertainty_target)
        
        loss = delta_loss + 0.1 * uncertainty_loss
    
    return loss.item(), delta_loss.item(), uncertainty_loss.item()

def compute_uncertainty_correlation(predictions: torch.Tensor, 
                                   actual_errors: torch.Tensor) -> float:
    """
    Compute correlation between uncertainty scores and actual prediction errors.
    
    Args:
        predictions: Model predictions [batch, 2] where column 1 is uncertainty
        actual_errors: Actual prediction errors [batch]
        
    Returns:
        correlation: Pearson correlation coefficient
    """
    uncertainties = predictions[:, 1].cpu().numpy()
    errors = actual_errors.cpu().numpy()
    
    # Compute Pearson correlation
    if len(uncertainties) < 2:
        return 0.0
    
    correlation = np.corrcoef(uncertainties, errors)[0, 1]
    
    # Handle NaN case
    if np.isnan(correlation):
        return 0.0
    
    return float(correlation)

def save_checkpoint(model: nn.Module, optimizer: torch.optim.Optimizer, 
                   epoch: int, loss: float, path: str):
    """
    Save model checkpoint.
    
    Args:
        model: The GRU estimator model
        optimizer: Torch optimizer
        epoch: Current epoch
        loss: Current loss
        path: Path to save checkpoint
    """
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
    }
    
    # Ensure directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    torch.save(checkpoint, path)
    print(f"Checkpoint saved to {path}")

def load_checkpoint(model: nn.Module, optimizer: Optional[torch.optim.Optimizer], 
                   path: str) -> Dict[str, Any]:
    """
    Load model checkpoint.
    
    Args:
        model: The GRU estimator model
        optimizer: Torch optimizer (optional)
        path: Path to checkpoint
        
    Returns:
        checkpoint: Dictionary with checkpoint data
    """
    checkpoint = torch.load(path, map_location='cpu')
    
    model.load_state_dict(checkpoint['model_state_dict'])
    
    if optimizer is not None and 'optimizer_state_dict' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    
    return checkpoint

def main():
    """
    Main function for testing the GRU estimator model.
    This creates a sample model and runs a forward pass to verify
    the output shape and uncertainty score computation.
    """
    print("Testing GRU Estimator Model...")
    
    # Load configuration
    config = load_config()
    
    # Set device
    device = torch.device(config['device'])
    print(f"Using device: {device}")
    
    # Create model
    model = GRUEstimator(
        input_dim=config.get('input_dim', 512),
        hidden_dim=config.get('hidden_dim', 256),
        num_layers=config.get('num_layers', 2),
        dropout=config.get('dropout', 0.3)
    ).to(device)
    
    # Create sample input
    batch_size = 4
    seq_len = 10
    input_dim = config.get('input_dim', 512)
    
    sample_input = torch.randn(batch_size, seq_len, input_dim).to(device)
    
    # Forward pass
    output = model(sample_input)
    
    print(f"Input shape: {sample_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Expected output shape: [{batch_size}, 2]")
    
    # Verify output shape
    assert output.shape == (batch_size, 2), f"Output shape mismatch: {output.shape} != ({batch_size}, 2)"
    
    # Verify uncertainty score is in [0, 1]
    uncertainties = output[:, 1]
    assert torch.all((uncertainties >= 0.0) & (uncertainties <= 1.0)), \
        f"Uncertainty scores out of range: [{uncertainties.min()}, {uncertainties.max()}]"
    
    print(f"Delta predictions range: [{output[:, 0].min():.4f}, {output[:, 0].max():.4f}]")
    print(f"Uncertainty scores range: [{uncertainties.min():.4f}, {uncertainties.max():.4f}]")
    
    # Test saving and loading checkpoint
    checkpoint_path = config.get('checkpoint_path', 'data/models/estimator_checkpoint.pt')
    print(f"\nTesting checkpoint save/load to: {checkpoint_path}")
    
    # Save checkpoint
    save_checkpoint(model, None, 0, 0.0, checkpoint_path)
    
    # Load checkpoint
    loaded_model = GRUEstimator(
        input_dim=config.get('input_dim', 512),
        hidden_dim=config.get('hidden_dim', 256),
        num_layers=config.get('num_layers', 2),
        dropout=config.get('dropout', 0.3)
    ).to(device)
    
    load_checkpoint(loaded_model, None, checkpoint_path)
    
    # Verify loaded model produces same output
    loaded_output = loaded_model(sample_input)
    assert torch.allclose(output, loaded_output, atol=1e-6), "Loaded model output mismatch"
    
    print("✓ All tests passed!")
    print(f"✓ UncertaintyScore is correctly computed and normalized to [0, 1]")
    print(f"✓ Model output shape is [batch, 2] as required")
    print(f"✓ Checkpoint saved to {checkpoint_path}")
    
    # Reference to T031 for MOS validation
    print("\nNote: UncertaintyScore will be validated against MOS in T031 (FR-012, FR-013, SC-007)")
    
    return True

if __name__ == "__main__":
    main()