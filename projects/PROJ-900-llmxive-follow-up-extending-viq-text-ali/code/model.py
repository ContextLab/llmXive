"""
T006: Model Definitions

Defines VQ-VAE Codebook, Projection Head, and Frozen ViQ/CLIP wrappers.
Uses ViQ-Base placeholder ID "viq-base-v".
"""

import math
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import CLIPTextModel, CLIPTokenizer

class Codebook(nn.Module):
    """
    Vector Quantization Codebook.
    """
    def __init__(self, embedding_dim: int = 512, num_embeddings: int = 1024):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.num_embeddings = num_embeddings
        self.embeddings = nn.Embedding(num_embeddings, embedding_dim)
        self.embeddings.weight.data.uniform_(-1.0 / num_embeddings, 1.0 / num_embeddings)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            x: Input tensor of shape (B, C, H, W) or (B, L, C)
        Returns:
            quantized: Quantized embeddings
            encoding_indices: Indices of the nearest codebook vectors
            commitment_loss: VQ commitment loss
        """
        # Flatten input if necessary
        if x.dim() == 4:
            # (B, C, H, W) -> (B, H*W, C)
            B, C, H, W = x.shape
            x = x.permute(0, 2, 3, 1).reshape(B, -1, C)
        
        # (B, L, C)
        encoding_indices = torch.argmin(
            torch.sum((x.unsqueeze(1) - self.embeddings.weight.unsqueeze(0)) ** 2, dim=-1),
            dim=1
        )
        
        encoding_indices = encoding_indices.view(x.shape[0], -1)
        quantized = self.embeddings(encoding_indices)
        
        # Reshape back if input was 4D
        if x.dim() == 4:
            quantized = quantized.view(B, H, W, C).permute(0, 3, 1, 2)
        else:
            quantized = quantized.view_as(x)
        
        # Commitment loss
        commitment_loss = F.mse_loss(quantized.detach(), x)
        
        # Straight-through estimator
        quantized = x + (quantized - x).detach()
        
        return quantized, encoding_indices, commitment_loss

class ProjectionHead(nn.Module):
    """
    Projection head to map visual embeddings to text embedding space.
    """
    def __init__(self, input_dim: int = 512, output_dim: int = 512, hidden_dim: int = 512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
            nn.LayerNorm(output_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

class FrozenViQWrapper(nn.Module):
    """
    Wrapper for a frozen ViQ encoder.
    Since we don't have the actual ViQ weights, we simulate a resolution-invariant
    encoder using a standard CNN backbone with adaptive pooling or a transformer.
    For this validation task, we assume a ResNet-like structure that can handle
    arbitrary input sizes due to global average pooling.
    """
    def __init__(self, embedding_dim: int = 512):
        super().__init__()
        # Simulated ViQ Encoder: ResNet18 backbone + AdaptiveAvgPool + Projection
        # This is a placeholder architecture that IS resolution invariant.
        self.backbone = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1),
            # Simple residual blocks
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            # Adaptive pooling to handle any resolution
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.projection = nn.Linear(64, embedding_dim)
        self.embedding_dim = embedding_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (B, C, H, W)
        Returns:
            embeddings: Tensor of shape (B, embedding_dim)
        """
        x = self.backbone(x)
        # x shape: (B, 64, 1, 1)
        x = x.view(x.size(0), -1)
        return self.projection(x)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.forward(x)

class FrozenCLIPTextWrapper(nn.Module):
    """
    Wrapper for frozen CLIP text encoder.
    """
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        super().__init__()
        self.tokenizer = CLIPTokenizer.from_pretrained(model_name)
        self.text_encoder = CLIPTextModel.from_pretrained(model_name)
        self.text_encoder.eval()
        for param in self.text_encoder.parameters():
            param.requires_grad = False

    def forward(self, texts: list) -> torch.Tensor:
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=77)
        with torch.no_grad():
            outputs = self.text_encoder(**inputs)
        # Use pooled output (last hidden state of [EOS] token usually, or mean pooling)
        # CLIPTextModel returns BaseModelOutputWithPooling
        return outputs.pooler_output

class ResNetVQVAE(nn.Module):
    """
    Simple VQ-VAE with ResNet-like encoder and decoder.
    """
    def __init__(self, codebook_dim: int = 512, num_codebooks: int = 1024):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(256, codebook_dim, kernel_size=3, stride=1, padding=1)
        )
        self.codebook = Codebook(embedding_dim=codebook_dim, num_embeddings=num_codebooks)
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(codebook_dim, 256, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 3, kernel_size=4, stride=2, padding=1),
            nn.Tanh()
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        z = self.encoder(x)
        quantized, indices, commitment_loss = self.codebook(z)
        recon = self.decoder(quantized)
        return recon, indices, commitment_loss

def get_model(model_id: str = "viq-base-v") -> nn.Module:
    """
    Factory function to get models.
    """
    if model_id == "viq-base-v":
        return FrozenViQWrapper(embedding_dim=512)
    elif model_id == "clip-text":
        return FrozenCLIPTextWrapper()
    elif model_id == "vq-vae":
        return ResNetVQVAE(codebook_dim=512, num_codebooks=1024)
    else:
        raise ValueError(f"Unknown model_id: {model_id}")