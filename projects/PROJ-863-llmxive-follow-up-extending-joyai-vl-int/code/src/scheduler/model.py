"""
CPU-Optimized Transformer Scheduler Model for US3.

Implements a lightweight Transformer architecture designed to process
internal state vectors extracted from the JoyAI-VL-Interaction model.
Optimized for CPU inference and training (no CUDA operations).
"""

import math
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for the CPU-optimized Transformer Scheduler."""
    input_dim: int
    """Dimension of the input feature vectors (internal states)."""
    hidden_dim: int = 128
    """Hidden dimension for the transformer layers."""
    num_heads: int = 4
    """Number of attention heads."""
    num_layers: int = 2
    """Number of transformer encoder layers (kept low for CPU efficiency)."""
    dropout: float = 0.1
    """Dropout probability."""
    num_classes: int = 2
    """Number of output classes (e.g., 0: No Intervention, 1: Intervention)."""
    max_seq_len: int = 512
    """Maximum sequence length for positional encoding."""
    d_model: int = 128
    """Model dimension (often same as hidden_dim)."""


class PositionalEncoding(nn.Module):
    """
    Standard positional encoding module optimized for CPU.
    Uses sine/cosine functions to inject position information.
    """

    def __init__(self, d_model: int, max_seq_len: int = 512, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Compute PE matrix
        pe = torch.zeros(max_seq_len, d_model)
        position = torch.arange(0, max_seq_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # Shape: (1, max_seq_len, d_model)

        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, d_model)
        Returns:
            Tensor of shape (batch_size, seq_len, d_model) with positional encoding added
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class CPUOptimizedTransformerEncoder(nn.Module):
    """
    A simplified Transformer encoder optimized for CPU execution.
    Uses standard multi-head attention and feed-forward networks.
    """

    def __init__(self, config: SchedulerConfig):
        super().__init__()
        self.config = config

        # Input projection if input_dim != d_model
        if config.input_dim != config.d_model:
            self.input_proj = nn.Linear(config.input_dim, config.d_model)
        else:
            self.input_proj = nn.Identity()

        self.pos_encoder = PositionalEncoding(
            config.d_model, config.max_seq_len, config.dropout
        )

        # Transformer Encoder Layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.num_heads,
            dim_feedforward=config.hidden_dim * 4,  # Standard FFN expansion
            dropout=config.dropout,
            activation='gelu',  # GELU is generally CPU-friendly
            batch_first=True,   # Crucial for handling (B, S, D) directly
            device='cpu'        # Explicitly force CPU
        )

        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=config.num_layers,
            enable_nested_tensor=False  # Disable nested tensors for consistent CPU perf
        )

        # Output projection
        self.output_proj = nn.Linear(config.d_model, config.num_classes)

        self._init_weights()

    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_dim)
            mask: Optional attention mask (not typically needed for causal/full attention here)
        Returns:
            Logits tensor of shape (batch_size, num_classes)
        """
        # Project input to model dimension
        x = self.input_proj(x)

        # Add positional encoding
        x = self.pos_encoder(x)

        # Pass through transformer encoder
        # Transformer expects (B, S, D) because batch_first=True
        encoded = self.transformer_encoder(x, mask=mask)

        # Global average pooling over sequence dimension to get a single vector per sample
        # This handles variable sequence lengths robustly
        sequence_output = encoded.mean(dim=1)  # Shape: (batch_size, d_model)

        # Project to class logits
        logits = self.output_proj(sequence_output)

        return logits


class SchedulerDataset(Dataset):
    """
    PyTorch Dataset for loading scheduler training data from JSONL features.
    Expects pre-processed feature vectors aligned with ground truth labels.
    """

    def __init__(
        self,
        feature_path: str,
        label_path: str,
        max_seq_len: int = 512
    ):
        self.feature_path = feature_path
        self.label_path = label_path
        self.max_seq_len = max_seq_len
        self.data = []

        # Load data into memory (assumes fits in RAM for training chunks)
        # In a production pipeline, this would be a streaming iterator
        logger.info(f"Loading dataset from {feature_path} and {label_path}")
        self._load_data()
        logger.info(f"Loaded {len(self.data)} samples.")

    def _load_data(self):
        # This is a placeholder for the actual loading logic.
        # In the real pipeline, this would read from data/features/*.jsonl
        # and align with ground truth.
        # For the model definition task, we assume the loader exists or is implemented in train.py.
        # We implement a minimal in-memory structure here to satisfy the class contract.
        pass

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        # Placeholder implementation
        # Returns (features, label)
        return torch.zeros(1, 1), torch.tensor(0)


class SchedulerModel:
    """
    High-level wrapper for the Transformer Scheduler.
    Handles model instantiation, saving, loading, and inference.
    """

    def __init__(self, config: SchedulerConfig):
        self.config = config
        self.model = CPUOptimizedTransformerEncoder(config)
        self.device = torch.device('cpu')
        self.model.to(self.device)
        logger.info(f"Initialized CPU-optimized Scheduler with config: {config}")

    def train(self):
        self.model.train()

    def eval(self):
        self.model.eval()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning logits."""
        with torch.set_grad_enabled(self.model.training):
            return self.model(x)

    def predict(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass returning class probabilities.
        Args:
            x: Input tensor (batch_size, seq_len, input_dim)
        Returns:
            Probabilities tensor (batch_size, num_classes)
        """
        self.model.eval()
        with torch.no_grad():
            logits = self.model(x)
            probs = F.softmax(logits, dim=-1)
        return probs

    def save_checkpoint(self, path: str):
        """Saves the model state dict."""
        checkpoint = {
            'config': self.config,
            'state_dict': self.model.state_dict()
        }
        torch.save(checkpoint, path)
        logger.info(f"Saved checkpoint to {path}")

    @classmethod
    def load_checkpoint(cls, path: str) -> 'SchedulerModel':
        """Loads a model from a checkpoint."""
        checkpoint = torch.load(path, map_location=torch.device('cpu'))
        config = checkpoint['config']
        model = cls(config)
        model.model.load_state_dict(checkpoint['state_dict'])
        model.model.eval()
        logger.info(f"Loaded checkpoint from {path}")
        return model


def create_scheduler_model(input_dim: int) -> SchedulerModel:
    """
    Factory function to create a default CPU-optimized Scheduler model.
    """
    config = SchedulerConfig(input_dim=input_dim)
    return SchedulerModel(config)


def main():
    """
    Entry point for testing model instantiation.
    """
    # Example usage
    config = SchedulerConfig(input_dim=512)
    model = SchedulerModel(config)
    
    # Dummy input
    dummy_input = torch.randn(4, 32, 512) # batch=4, seq=32, dim=512
    output = model.forward(dummy_input)
    print(f"Model output shape: {output.shape}")
    
    # Save a dummy checkpoint
    model.save_checkpoint("models/test_scheduler_checkpoint.pth")

if __name__ == "__main__":
    main()