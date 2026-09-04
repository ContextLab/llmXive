"""
Vision Encoder module for RoboDojo Symbolic Abstractions.

This module provides a frozen MobileViT-based encoder to generate
semantic embeddings from video frames for downstream symbolic state mapping.
"""

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from typing import List, Optional, Union, Dict, Any
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionEncoder(nn.Module):
    """
    Frozen MobileViT Vision Encoder.

    This class wraps a pre-trained MobileViT model, freezing all parameters
    to ensure the feature extractor remains static during adapter training.
    It outputs a fixed-size semantic embedding vector.
    """

    def __init__(self, embedding_dim: int = 512, device: Optional[str] = None):
        """
        Initialize the Vision Encoder.

        Args:
            embedding_dim: The dimension of the output embedding vector.
            device: The device to run the model on (cpu, cuda, mps).
        """
        super().__init__()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.embedding_dim = embedding_dim

        logger.info(f"Initializing VisionEncoder on device: {self.device}")

        # Load MobileViT (small variant for CPU tractability)
        # Using torchvision's mobilevit_xs which is lightweight and CPU-friendly
        try:
            weights = torchvision.models.MobileViT_XS_Weights.IMAGENET1K_V1
            self.backbone = torchvision.models.mobilenet_vit_x(weights=weights)
        except AttributeError:
            # Fallback for older torchvision versions or specific model names
            # Attempting to load a generic MobileViT or raising error if not found
            logger.warning("Standard MobileViT XS not found in torchvision. Attempting alternative load or failing.")
            raise ImportError(
                "MobileViT model not found. Please ensure torchvision>=0.13 is installed "
                "or adjust the model loading strategy in vision_encoder.py."
            )

        # Freeze all backbone parameters
        for param in self.backbone.parameters():
            param.requires_grad = False

        self.backbone.to(self.device)
        self.backbone.eval()

        # Projection head to map backbone output to desired embedding dimension
        # MobileViT XS output feature size is typically 320 or similar before pooling
        # We use a simple linear projection after global average pooling
        self.input_features = 320  # Approximate for MobileViT-XS
        self.projection = nn.Sequential(
            nn.Linear(self.input_features, self.embedding_dim),
            nn.ReLU(),
            nn.LayerNorm(self.embedding_dim)
        )
        self.projection.to(self.device)

        # Preprocessing transforms
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def forward(self, frames: Union[torch.Tensor, np.ndarray]) -> torch.Tensor:
        """
        Process input frames and return semantic embeddings.

        Args:
            frames: Input frames. Can be:
                    - A single numpy array (H, W, C)
                    - A list of numpy arrays
                    - A torch tensor (B, C, H, W) or (C, H, W)

        Returns:
            torch.Tensor: Semantic embeddings of shape (B, embedding_dim)
        """
        # Normalize input handling
        if isinstance(frames, np.ndarray):
            if frames.ndim == 3:
                # Single frame (H, W, C)
                frames = [frames]
            elif frames.ndim == 4:
                # Batch (B, H, W, C) -> list of frames
                frames = [frames[i] for i in range(frames.shape[0])]
            else:
                raise ValueError(f"Unsupported numpy shape: {frames.shape}")

            # Convert list of numpy frames to tensor (B, C, H, W)
            processed_frames = []
            for f in frames:
                # Ensure float32 and range [0, 1] if uint8
                if f.dtype == np.uint8:
                    f = f.astype(np.float32) / 255.0
                processed_frames.append(self.transform(f))
            tensor_input = torch.stack(processed_frames).to(self.device)
        elif isinstance(frames, torch.Tensor):
            if frames.ndim == 3:
                frames = frames.unsqueeze(0)
            if frames.device != self.device:
                frames = frames.to(self.device)
            tensor_input = frames
        else:
            raise TypeError(f"Unsupported input type: {type(frames)}")

        # Ensure input is (B, C, H, W) and normalized
        if tensor_input.shape[1] == 3:
            pass # Already normalized by transform
        else:
            # If not normalized, apply normalization
            mean = torch.tensor([0.485, 0.456, 0.406], device=self.device).view(1, 3, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225], device=self.device).view(1, 3, 1, 1)
            tensor_input = (tensor_input - mean) / std

        with torch.no_grad():
            # Extract features from backbone
            # MobileViT returns a dict or tensor depending on version, handling common output
            features = self.backbone(tensor_input)

            # Handle potential dict output or specific feature map extraction
            # Assuming standard return of feature map (B, C, H, W)
            if isinstance(features, dict):
                # Take the last stage feature map
                feature_map = list(features.values())[-1]
            else:
                feature_map = features

            # Global Average Pooling to get (B, C)
            pooled = torch.nn.functional.adaptive_avg_pool2d(feature_map, 1).squeeze(-1).squeeze(-1)

            # Project to embedding dimension
            embeddings = self.projection(pooled)

        return embeddings

    def encode_video(self, video_frames: List[np.ndarray]) -> torch.Tensor:
        """
        Encode a sequence of video frames into a single semantic embedding.

        This method aggregates embeddings from multiple frames (e.g., by averaging)
        to represent the entire video clip.

        Args:
            video_frames: List of numpy arrays (H, W, C) representing video frames.

        Returns:
            torch.Tensor: Aggregated semantic embedding (embedding_dim,).
        """
        if not video_frames:
            raise ValueError("Video frames list cannot be empty")

        # Encode each frame
        frame_embeddings = self.forward(torch.stack([self.transform(f) for f in video_frames]).to(self.device))

        # Average pooling over time
        aggregated_embedding = frame_embeddings.mean(dim=0, keepdim=False)

        return aggregated_embedding


def create_vision_encoder(embedding_dim: int = 512, device: Optional[str] = None) -> VisionEncoder:
    """
    Factory function to create a VisionEncoder instance.

    Args:
        embedding_dim: Dimension of the output embedding.
        device: Target device.

    Returns:
        VisionEncoder: Initialized and ready-to-use encoder.
    """
    logger.info("Creating VisionEncoder via factory function")
    encoder = VisionEncoder(embedding_dim=embedding_dim, device=device)
    return encoder

# Note: torchvision import is implicit in the class definition but added here for clarity
# The class definition above uses `torchvision.models` which requires:
# import torchvision
# This is handled by the `import torchvision.transforms` and `torchvision.models` usage.
# To ensure valid import, we explicitly import torchvision at the top if not already.
import torchvision