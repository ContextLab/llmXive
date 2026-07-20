"""
Wrapper for the frozen Geometric Action Model (GFM) weights.
Handles loading, encoding, and decoding in CPU-only eval mode.
"""
import logging
import os
from typing import Any, Dict, Optional, Union
import numpy as np
import torch
from .utils import setup_logging, set_deterministic_seed, compute_sha256

class GFMWrapper:
    """
    Wrapper for the frozen GFM encoder/decoder.
    Operates in CPU-only eval mode with no gradient tracking.
    """
    
    def __init__(self, model_path: str, device: str = "cpu"):
        """
        Initialize the GFM wrapper.
        
        Args:
            model_path: Path to the frozen GFM weights (.pt file)
            device: Device to run inference on (default: "cpu")
        """
        self.logger = setup_logging()
        self.device = device
        self.model_path = model_path
        self.model = None
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"GFM model file not found: {model_path}")
            
        self._load_model()
        
    def _load_model(self) -> None:
        """Load the frozen GFM model weights."""
        self.logger.info(f"Loading GFM model from {self.model_path}")
        
        # Initialize a placeholder model structure
        # In a real implementation, this would define the actual network architecture
        # For now, we simulate the structure required for the wrapper
        class DummyGFMModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = torch.nn.Linear(100, 64)
                self.decoder = torch.nn.Linear(64, 100)
                
            def forward(self, x):
                latent = self.encoder(x)
                action = self.decoder(latent)
                return latent, action
        
        self.model = DummyGFMModel()
        
        # Load weights
        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(checkpoint)
        
        # Set to eval mode and disable gradients
        self.model.eval()
        for param in self.model.parameters():
            param.requires_grad = False
            
        self.logger.info(f"Loaded GFM model successfully. Model hash: {compute_sha256(str(self.model.state_dict()))}")
        
    def encode(self, observation: Union[np.ndarray, torch.Tensor]) -> np.ndarray:
        """
        Encode an observation into latent space.
        
        Args:
            observation: Input observation array
            
        Returns:
            Latent vector as numpy array
        """
        if isinstance(observation, np.ndarray):
            observation = torch.from_numpy(observation).float()
            
        observation = observation.to(self.device)
        
        with torch.no_grad():
            latent, _ = self.model(observation)
            
        return latent.cpu().numpy()
        
    def decode(self, latent: Union[np.ndarray, torch.Tensor]) -> np.ndarray:
        """
        Decode a latent vector into an action.
        
        Args:
            latent: Latent vector input
            
        Returns:
            Action vector as numpy array
        """
        if isinstance(latent, np.ndarray):
            latent = torch.from_numpy(latent).float()
            
        latent = latent.to(self.device)
        
        with torch.no_grad():
            _, action = self.model(latent)
            
        return action.cpu().numpy()
