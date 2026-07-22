"""
Model Definitions (T006).

Defines VQ-VAE Codebook, Projection Head, and Frozen ViQ/CLIP wrappers.
Includes fallback ResNetVQVAE if ViQ weights are missing.
"""
import math
from typing import Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import CLIPTextModel, CLIPTokenizer

class Codebook(nn.Module):
    """Vector Quantization Codebook."""
    def __init__(self, embedding_dim=512, codebook_size=1024):
        super().__init__()
        self.codebook_size = codebook_size
        self.embedding_dim = embedding_dim
        
        self.codebook = nn.Embedding(codebook_size, embedding_dim)
        self.codebook.weight.data.uniform_(-1.0 / codebook_size, 1.0 / codebook_size)
    
    def forward(self, z_e: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Quantize input tensor z_e.
        Args:
            z_e: [B, H*W, C]
        Returns:
            z_q: Quantized tensor [B, H*W, C]
            loss: Commitment loss
            indices: Codebook indices
        """
        # Flatten spatial dims if not already
        # Input expected: [B, L, C]
        z_e_flat = z_e
        
        # Calculate distances
        # z_e: [B, L, C], codebook: [C, K] -> [B, L, K]
        dist = torch.sum(z_e_flat ** 2, dim=-1, keepdim=True) - \
               2 * torch.matmul(z_e_flat, self.codebook.weight.T) + \
               torch.sum(self.codebook.weight ** 2, dim=-1)
        
        indices = torch.argmin(dist, dim=-1)
        z_q = self.codebook(indices)
        
        # Commitment loss: ||sg(z_e) - z_q||^2
        loss_commit = F.mse_loss(z_q.detach(), z_e_flat)
        
        # Straight-through estimator
        z_q = z_e_flat + (z_q - z_e_flat).detach()
        
        return z_q, loss_commit, indices

class ProjectionHead(nn.Module):
    """Projection head to map codebook embeddings to text embedding space."""
    def __init__(self, input_dim=512, output_dim=512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, input_dim),
            nn.ReLU(),
            nn.Linear(input_dim, output_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

class FrozenViQWrapper(nn.Module):
    """Wrapper for a frozen ViQ encoder."""
    def __init__(self, embedding_dim=512):
        super().__init__()
        self.embedding_dim = embedding_dim
        # Placeholder for actual ViQ weights
        # In a real scenario, this would load specific ViQ weights
        # For now, we define a simple convolutional encoder that supports arbitrary resolution
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(256, embedding_dim, kernel_size=3, stride=2, padding=1),
            nn.ReLU()
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)

class FrozenCLIPTextWrapper(nn.Module):
    """Wrapper for frozen CLIP text encoder."""
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        super().__init__()
        self.tokenizer = CLIPTokenizer.from_pretrained(model_name)
        self.text_model = CLIPTextModel.from_pretrained(model_name)
        self.text_model.eval()
        for param in self.text_model.parameters():
            param.requires_grad = False
    
    def forward(self, texts: list) -> torch.Tensor:
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=77)
        with torch.no_grad():
            outputs = self.text_model(**inputs)
        return outputs.last_hidden_state[:, 0, :]  # CLS token

class ResNetVQVAE(nn.Module):
    """Fallback ResNet-based VQ-VAE encoder if ViQ weights missing."""
    def __init__(self, hidden_dim=512, codebook_size=1024):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 64, 7, stride=2, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, hidden_dim, 3, stride=2, padding=1),
            nn.BatchNorm2d(hidden_dim),
            nn.ReLU()
        )
        self.codebook = Codebook(embedding_dim=hidden_dim, codebook_size=codebook_size)
        self.projection = ProjectionHead(input_dim=hidden_dim, output_dim=hidden_dim)
    
    def forward(self, x: torch.Tensor):
        z_e = self.encoder(x)
        b, c, h, w = z_e.shape
        z_e_flat = z_e.flatten(2).transpose(1, 2)
        z_q, loss, indices = self.codebook(z_e_flat)
        z_q = z_q.transpose(1, 2).reshape(b, c, h, w)
        proj = self.projection(z_q)
        return z_q, proj, loss

def get_model():
    """
    Factory function to get the model components.
    Returns a dictionary of components: encoder, codebook, projection.
    """
    # Try to load ViQ weights if available, otherwise use fallback
    # For T006, we define the structure. T012 will train the codebook.
    
    encoder = FrozenViQWrapper()
    codebook = Codebook(embedding_dim=512, codebook_size=1024)
    projection = ProjectionHead(input_dim=512, output_dim=512)
    
    return {
        'encoder': encoder,
        'codebook': codebook,
        'projection': projection
    }
