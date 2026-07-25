"""
Baseline models for predicting normalized DFT total molecular energy.

Implements Fingerprint-only, Spectrum-only, and Condition-only baselines
as required by User Story 2.
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Tuple, Dict, Any


class FingerprintBaseline(nn.Module):
    """
    Baseline model using only molecular fingerprints (ECFP4) to predict
    normalized DFT total molecular energy.
    
    Architecture:
    - Input: ECFP4 vector (size 2048 typically)
    - Hidden layers: 2 fully connected layers with ReLU
    - Output: Single scalar (energy prediction)
    """
    def __init__(
        self, 
        fingerprint_size: int = 2048, 
        hidden_size: int = 512,
        dropout: float = 0.1
    ):
        super().__init__()
        self.fingerprint_size = fingerprint_size
        self.hidden_size = hidden_size
        
        self.network = nn.Sequential(
            nn.Linear(fingerprint_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, 1)
        )
    
    def forward(self, fingerprints: torch.Tensor) -> torch.Tensor:
        """
        Args:
            fingerprints: Tensor of shape (batch_size, fingerprint_size)
        
        Returns:
            Tensor of shape (batch_size, 1) containing energy predictions
        """
        return self.network(fingerprints)


class SpectrumBaseline(nn.Module):
    """
    Baseline model using only spectral data (IR/Raman/NMR) to predict
    normalized DFT total molecular energy.
    
    Architecture:
    - Input: Concatenated spectral vectors
    - Processing: 1D Convolutional layers followed by global pooling
    - Output: Single scalar (energy prediction)
    """
    def __init__(
        self,
        spectrum_length: int = 2000,
        num_channels: int = 3,  # IR, Raman, NMR
        hidden_channels: int = 32,
        dropout: float = 0.1
    ):
        super().__init__()
        self.spectrum_length = spectrum_length
        self.num_channels = num_channels
        
        # Reshape input to (batch, channels, length) for Conv1D
        self.conv1 = nn.Conv1d(
            in_channels=num_channels,
            out_channels=hidden_channels,
            kernel_size=5,
            stride=1,
            padding=2
        )
        self.pool1 = nn.MaxPool1d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv1d(
            in_channels=hidden_channels,
            out_channels=hidden_channels * 2,
            kernel_size=5,
            stride=1,
            padding=2
        )
        self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)
        
        # Calculate output size after pooling
        # After conv1: length stays same (padding=2, kernel=5)
        # After pool1: length // 2
        # After conv2: length stays same
        # After pool2: (length // 2) // 2 = length // 4
        self.feature_dim = (spectrum_length // 4) * (hidden_channels * 2)
        
        self.fc = nn.Sequential(
            nn.Linear(self.feature_dim, hidden_channels * 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels * 4, 1)
        )
    
    def forward(self, spectra: torch.Tensor) -> torch.Tensor:
        """
        Args:
            spectra: Tensor of shape (batch_size, num_channels, spectrum_length)
        
        Returns:
            Tensor of shape (batch_size, 1) containing energy predictions
        """
        # Convolutional feature extraction
        x = self.conv1(spectra)
        x = nn.functional.relu(x)
        x = self.pool1(x)
        
        x = self.conv2(x)
        x = nn.functional.relu(x)
        x = self.pool2(x)
        
        # Global average pooling (flatten)
        x = x.view(x.size(0), -1)
        
        return self.fc(x)


class ConditionBaseline(nn.Module):
    """
    Baseline model using only reaction conditions (solvent, catalyst, temperature)
    to predict normalized DFT total molecular energy.
    
    Architecture:
    - Input: One-hot or embedding encoded conditions
    - Processing: Fully connected layers
    - Output: Single scalar (energy prediction)
    """
    def __init__(
        self,
        condition_dim: int = 64,
        hidden_size: int = 128,
        dropout: float = 0.1
    ):
        super().__init__()
        self.condition_dim = condition_dim
        
        self.network = nn.Sequential(
            nn.Linear(condition_dim, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, 1)
        )
    
    def forward(self, conditions: torch.Tensor) -> torch.Tensor:
        """
        Args:
            conditions: Tensor of shape (batch_size, condition_dim)
        
        Returns:
            Tensor of shape (batch_size, 1) containing energy predictions
        """
        return self.network(conditions)


def create_baseline_model(
    model_type: str,
    fingerprint_size: int = 2048,
    spectrum_length: int = 2000,
    num_channels: int = 3,
    condition_dim: int = 64,
    **kwargs
) -> nn.Module:
    """
    Factory function to create the appropriate baseline model.
    
    Args:
        model_type: One of 'fingerprint', 'spectrum', or 'condition'
        fingerprint_size: Size of ECFP4 fingerprint vector
        spectrum_length: Length of spectral grid
        num_channels: Number of spectral channels (IR, Raman, NMR)
        condition_dim: Dimension of encoded condition vector
        **kwargs: Additional keyword arguments passed to model constructors
    
    Returns:
        Initialized nn.Module baseline model
    
    Raises:
        ValueError: If model_type is not recognized
    """
    model_type = model_type.lower()
    
    if model_type == 'fingerprint':
        return FingerprintBaseline(
            fingerprint_size=fingerprint_size,
            **kwargs
        )
    elif model_type == 'spectrum':
        return SpectrumBaseline(
            spectrum_length=spectrum_length,
            num_channels=num_channels,
            **kwargs
        )
    elif model_type == 'condition':
        return ConditionBaseline(
            condition_dim=condition_dim,
            **kwargs
        )
    else:
        raise ValueError(
            f"Unknown model_type '{model_type}'. "
            "Expected one of: 'fingerprint', 'spectrum', 'condition'"
        )