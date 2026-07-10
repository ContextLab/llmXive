"""
CTCF Binding Predictor Model.

This module defines the predictive model for CTCF binding, including
sequence and chromatin feature processing.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import numpy as np

class SequenceCNN(nn.Module):
    """
    Convolutional Neural Network for processing DNA sequences.
    
    Input: One-hot encoded sequence (batch_size, 4, sequence_length)
    Output: Sequence features (batch_size, hidden_dim)
    """

    def __init__(self, input_channels: int = 4, hidden_dim: int = 128):
        super(SequenceCNN, self).__init__()
        
        self.conv1 = nn.Conv1d(input_channels, 64, kernel_size=15, padding=7)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=15, padding=7)
        self.conv3 = nn.Conv1d(128, hidden_dim, kernel_size=15, padding=7)
        
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(128)
        self.bn3 = nn.BatchNorm1d(hidden_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for sequence data.
        
        Args:
            x: Input tensor of shape (batch_size, 4, sequence_length)
            
        Returns:
            features: Sequence features of shape (batch_size, hidden_dim)
        """
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.pool(x).squeeze(-1)
        return x

class ChromatinMLP(nn.Module):
    """
    Multi-Layer Perceptron for processing chromatin accessibility and histone marks.
    
    Input: Chromatin features (batch_size, num_features)
    Output: Chromatin features (batch_size, hidden_dim)
    """

    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super(ChromatinMLP, self).__init__()
        
        self.fc1 = nn.Linear(input_dim, 64)
        self.fc2 = nn.Linear(64, hidden_dim)
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(hidden_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for chromatin data.
        
        Args:
            x: Input tensor of shape (batch_size, num_features)
            
        Returns:
            features: Chromatin features of shape (batch_size, hidden_dim)
        """
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.bn2(self.fc2(x))
        return x

class LightweightTransformer(nn.Module):
    """
    Lightweight Transformer encoder for sequence modeling.
    
    Input: Sequence embeddings (batch_size, sequence_length, hidden_dim)
    Output: Sequence features (batch_size, hidden_dim)
    """

    def __init__(self, d_model: int = 128, nhead: int = 4, num_layers: int = 2):
        super(LightweightTransformer, self).__init__()
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=256, dropout=0.1
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.pool = nn.AdaptiveAvgPool1d(1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, d_model)
            
        Returns:
            features: Sequence features of shape (batch_size, d_model)
        """
        # Transpose to (sequence_length, batch_size, d_model) for transformer
        x = x.transpose(0, 1)
        x = self.transformer(x)
        x = x.transpose(0, 1)
        x = self.pool(x.transpose(1, 2)).squeeze(-1)
        return x

class CTCFPredictor(nn.Module):
    """
    Main predictor model combining sequence and chromatin features.
    
    Architecture:
    1. SequenceCNN processes DNA sequence
    2. ChromatinMLP processes chromatin accessibility/histone marks
    3. Features are concatenated and passed through a final MLP
    4. Output is binding probability
    """

    def __init__(
        self,
        sequence_hidden_dim: int = 128,
        chromatin_hidden_dim: int = 128,
        num_chromatin_features: int = 4,
        transformer_hidden_dim: int = 128
    ):
        super(CTCFPredictor, self).__init__()
        
        self.sequence_cnn = SequenceCNN(hidden_dim=sequence_hidden_dim)
        self.chromatin_mlp = ChromatinMLP(
            input_dim=num_chromatin_features, hidden_dim=chromatin_hidden_dim
        )
        
        # Combined feature dimension
        combined_dim = sequence_hidden_dim + chromatin_hidden_dim
        
        self.combined_mlp = nn.Sequential(
            nn.Linear(combined_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

        # Store intermediate activations for interpretability
        self._hidden_activations = None

    def forward(
        self,
        sequence: torch.Tensor,
        chromatin: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            sequence: One-hot encoded sequence (batch_size, 4, sequence_length)
            chromatin: Chromatin features (batch_size, num_features)
            
        Returns:
            logits: Binding probability logits (batch_size, 1)
        """
        seq_features = self.sequence_cnn(sequence)
        chrom_features = self.chromatin_mlp(chromatin)
        
        combined = torch.cat([seq_features, chrom_features], dim=1)
        logits = self.combined_mlp(combined)
        
        return logits

    def get_hidden_activations(
        self,
        sequence: torch.Tensor,
        chromatin: torch.Tensor
    ) -> torch.Tensor:
        """
        Extract hidden layer activations before the final prediction layer.
        
        This method is used by the SAE to decompose the learned representations.
        
        Args:
            sequence: One-hot encoded sequence (batch_size, 4, sequence_length)
            chromatin: Chromatin features (batch_size, num_features)
            
        Returns:
            hidden: Concatenated hidden features (batch_size, combined_dim)
        """
        seq_features = self.sequence_cnn(sequence)
        chrom_features = self.chromatin_mlp(chromatin)
        
        hidden = torch.cat([seq_features, chrom_features], dim=1)
        self._hidden_activations = hidden
        
        return hidden

    def predict(
        self,
        sequence: torch.Tensor,
        chromatin: torch.Tensor
    ) -> torch.Tensor:
        """
        Predict binding probability.
        
        Args:
            sequence: One-hot encoded sequence
            chromatin: Chromatin features
            
        Returns:
            probabilities: Binding probabilities (batch_size, 1)
        """
        logits = self.forward(sequence, chromatin)
        return torch.sigmoid(logits)

def load_model(model_path: str) -> CTCFPredictor:
    """
    Load a trained CTCFPredictor model.
    
    Args:
        model_path: Path to the saved model weights
        
    Returns:
        model: Loaded CTCFPredictor model
    """
    # Load checkpoint
    checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
    
    # Extract model parameters from checkpoint if saved
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    else:
        state_dict = checkpoint
    
    # Create model (assume default dimensions for now)
    model = CTCFPredictor(
        sequence_hidden_dim=128,
        chromatin_hidden_dim=128,
        num_chromatin_features=4,
        transformer_hidden_dim=128
    )
    
    model.load_state_dict(state_dict)
    model.eval()
    
    return model

# For backward compatibility with existing imports
__all__ = ['SequenceCNN', 'ChromatinMLP', 'LightweightTransformer', 'CTCFPredictor', 'load_model']
