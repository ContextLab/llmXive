import math
from typing import Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import CLIPTextModel, CLIPTokenizer

# T006: Codebook, ProjectionHead, FrozenViQWrapper, FrozenCLIPTextWrapper, ResNetVQVAE, get_model

class Codebook(nn.Module):
    def __init__(self, num_embeddings: int = 1024, embedding_dim: int = 512):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        # Initialize embeddings randomly
        self.embeddings = nn.Parameter(torch.randn(num_embeddings, embedding_dim))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, H, W, D) or (B, D)
        # Flatten spatial dimensions if present
        if x.dim() > 2:
            original_shape = x.shape
            x = x.view(-1, self.embedding_dim)
        
        # Compute distances
        # dist = ||x - e||^2 = ||x||^2 + ||e||^2 - 2 x.e
        x_norm = torch.norm(x, dim=1, keepdim=True)
        e_norm = torch.norm(self.embeddings, dim=1, keepdim=True)
        dist = x_norm**2 + e_norm.T**2 - 2 * torch.matmul(x, self.embeddings.T)
        
        # Get indices
        indices = torch.argmin(dist, dim=1)
        
        # Lookup embeddings
        quantized = self.embeddings[indices]
        
        # Reshape back if needed
        if len(original_shape) > 2:
            quantized = quantized.view(original_shape)
        
        return quantized, indices

class ProjectionHead(nn.Module):
    def __init__(self, input_dim: int = 512, output_dim: int = 512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, output_dim),
            nn.ReLU(),
            nn.Linear(output_dim, output_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, H, W, D) -> (B, H*W, D) -> (B, H*W, D_out)
        # Or (B, D) -> (B, D_out)
        if x.dim() > 2:
            B, H, W, D = x.shape
            x = x.view(B, H * W, D)
            x = self.net(x)
            return x.view(B, H, W, -1)
        else:
            return self.net(x)

class FrozenViQWrapper(nn.Module):
    def __init__(self):
        super().__init__()
        # T006: ViQ-Base placeholder ID "viq-base-v"
        # Since we don't have the real model, we use a dummy placeholder
        # that returns random embeddings or identity if needed.
        # For T016 training, we might not use this directly if we use ResNetVQVAE.
        pass

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Placeholder
        return torch.randn(x.shape[0], 512)

class FrozenCLIPTextWrapper(nn.Module):
    def __init__(self):
        super().__init__()
        self.tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-base-patch32")
        self.model = CLIPTextModel.from_pretrained("openai/clip-vit-base-patch32")
        self.model.eval()
        for param in self.model.parameters():
            param.requires_grad = False

    def forward(self, captions: list) -> torch.Tensor:
        inputs = self.tokenizer(
            captions, 
            padding=True, 
            truncation=True, 
            max_length=77, 
            return_tensors="pt"
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
        # Use pooler output or last hidden state mean
        return outputs.pooler_output

class ResNetVQVAE(nn.Module):
    """
    T006 Fallback Architecture:
    ResNet based VQ-VAE with 512 hidden dimensions, 1024 codebook size.
    """
    def __init__(self, hidden_dim: int = 512, codebook_size: int = 1024, num_channels: int = 3):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(num_channels, hidden_dim, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(hidden_dim, hidden_dim, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(hidden_dim, hidden_dim, kernel_size=3, stride=1, padding=1)
        )
        
        self.codebook = Codebook(num_embeddings=codebook_size, embedding_dim=hidden_dim)
        
        self.decoder = nn.Sequential(
            nn.Conv2d(hidden_dim, hidden_dim, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(hidden_dim, hidden_dim, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(hidden_dim, num_channels, kernel_size=4, stride=2, padding=1),
            nn.Sigmoid() # Output in [0, 1]
        )

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # x: (B, C, H, W)
        z = self.encoder(x) # (B, D, H', W')
        z = z.permute(0, 2, 3, 1) # (B, H', W', D)
        
        quantized, indices = self.codebook(z)
        
        # Commitment loss calculation (part of vq_loss usually, but returning here for completeness)
        # We return quantized, indices, and a dummy commitment loss (calculated in vq_loss)
        return quantized.permute(0, 3, 1, 2), indices, torch.tensor(0.0)

    def decode(self, quantized: torch.Tensor) -> torch.Tensor:
        # quantized: (B, H', W', D)
        z = quantized.permute(0, 3, 1, 2)
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        quantized, indices, _ = self.encode(x)
        recon = self.decode(quantized)
        return recon, quantized, indices

def get_model(name: str = "resnet_vqvae") -> nn.Module:
    if name == "resnet_vqvae":
        return ResNetVQVAE()
    raise ValueError(f"Unknown model: {name}")
