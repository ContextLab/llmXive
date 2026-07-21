"""
CLIP-based temporal coherence evaluator for video generation.

This module provides a frozen CLIP-ViT model to score the temporal coherence
of generated video clips. It operates in CPU-only mode with gradients disabled.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import CLIPModel, CLIPProcessor
from typing import List, Union, Optional, Tuple
import numpy as np
import os
from pathlib import Path

# Ensure we can import from project root if needed
try:
    from config import get_path_str, ensure_dirs_exist
except ImportError:
    # Fallback for standalone execution
    def get_path_str(key: str) -> str:
        return str(Path.cwd() / key)
    
    def ensure_dirs_exist(path_str: str) -> None:
        Path(path_str).mkdir(parents=True, exist_ok=True)


class ClipTemporalEvaluator(nn.Module):
    """
    A wrapper around a frozen CLIP-ViT model for temporal coherence scoring.
    
    This evaluator:
    1. Loads a pre-trained CLIP model (ViT-B/32 or similar)
    2. Freezes all parameters (no gradients)
    3. Processes video clips as sequences of frames
    4. Computes a coherence score based on frame-to-frame similarity
    
    Attributes:
        model (CLIPModel): The frozen CLIP model
        processor (CLIPProcessor): The processor for input normalization
        device (torch.device): The device to run inference on (CPU)
    """
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str = "cpu"):
        """
        Initialize the CLIP temporal evaluator.
        
        Args:
            model_name: Name of the CLIP model to load from HuggingFace
            device: Device to run inference on (default: "cpu")
        """
        super().__init__()
        self.device = torch.device(device)
        self.model_name = model_name
        
        # Load model and processor
        try:
            self.model = CLIPModel.from_pretrained(model_name)
            self.processor = CLIPProcessor.from_pretrained(model_name)
        except Exception as e:
            raise RuntimeError(f"Failed to load CLIP model '{model_name}': {e}")
        
        # Freeze all parameters
        self.model.eval()
        for param in self.model.parameters():
            param.requires_grad = False
        
        # Move to device
        self.model.to(self.device)
        
    @torch.inference_mode()
    def encode_frames(self, frames: Union[torch.Tensor, np.ndarray]) -> torch.Tensor:
        """
        Encode a batch of video frames into feature vectors.
        
        Args:
            frames: Input frames. Can be:
                - torch.Tensor of shape (N, H, W, C) or (N, C, H, W)
                - np.ndarray of shape (N, H, W, C)
                N is the number of frames, H/W are height/width, C is channels (3)
                
        Returns:
            torch.Tensor of shape (N, feature_dim) containing frame embeddings
        """
        # Convert to tensor if numpy array
        if isinstance(frames, np.ndarray):
            frames = torch.from_numpy(frames)
        
        # Ensure correct shape: (N, H, W, C) -> (N, C, H, W) for CLIP
        if frames.dim() == 4:
            if frames.shape[-1] == 3 and frames.shape[1] != 3:
                # Assume (N, H, W, C) format
                frames = frames.permute(0, 3, 1, 2)
            elif frames.shape[1] == 3:
                # Already (N, C, H, W)
                pass
            else:
                raise ValueError(f"Expected 4-channel or 3-channel frames, got shape {frames.shape}")
        
        # Normalize to [0, 1] if values are in [0, 255]
        if frames.max() > 1.0:
            frames = frames.float() / 255.0
        
        # Process through CLIP
        inputs = self.processor(
            images=frames,
            return_tensors="pt",
            padding=True,
            truncation=True
        ).to(self.device)
        
        with torch.no_grad():
            # Get image embeddings (visual encoder output)
            image_features = self.model.get_image_features(**inputs)
            # Normalize embeddings
            image_features = F.normalize(image_features, dim=-1)
        
        return image_features
    
    @torch.inference_mode()
    def compute_temporal_coherence(self, frames: Union[torch.Tensor, np.ndarray]) -> float:
        """
        Compute a temporal coherence score for a video clip.
        
        The score is based on the average cosine similarity between consecutive
        frame embeddings. Higher scores indicate smoother temporal transitions.
        
        Args:
            frames: Input frames (N, H, W, C) or (N, C, H, W)
            
        Returns:
            float: Temporal coherence score in range [-1, 1]
        """
        if len(frames) < 2:
            # Not enough frames for coherence calculation
            return 0.0
        
        # Encode all frames
        embeddings = self.encode_frames(frames)
        
        # Compute pairwise similarities between consecutive frames
        # embeddings shape: (N, D)
        # We want similarity between frame i and frame i+1
        
        # Shift embeddings to compare consecutive frames
        embeddings_prev = embeddings[:-1]
        embeddings_next = embeddings[1:]
        
        # Compute cosine similarity (embeddings are already normalized)
        similarities = torch.sum(embeddings_prev * embeddings_next, dim=1)
        
        # Average similarity
        avg_similarity = torch.mean(similarities).item()
        
        return avg_similarity
    
    @torch.inference_mode()
    def score_clip(self, frames: Union[torch.Tensor, np.ndarray]) -> Dict[str, float]:
        """
        Score a video clip with detailed metrics.
        
        Args:
            frames: Input frames
            
        Returns:
            dict: Dictionary containing:
                - 'coherence': Temporal coherence score
                - 'mean_frame_embedding': Mean of all frame embeddings (for debugging)
        """
        coherence = self.compute_temporal_coherence(frames)
        
        # Compute mean embedding for reference
        embeddings = self.encode_frames(frames)
        mean_embedding = torch.mean(embeddings, dim=0).tolist()
        
        return {
            'coherence': coherence,
            'mean_frame_embedding': mean_embedding
        }


def create_clip_evaluator(
    model_name: str = "openai/clip-vit-base-patch32",
    device: str = "cpu"
) -> ClipTemporalEvaluator:
    """
    Factory function to create a CLIP temporal evaluator.
    
    Args:
        model_name: Name of the CLIP model to load
        device: Device to run inference on
        
    Returns:
        ClipTemporalEvaluator: Initialized evaluator instance
    """
    return ClipTemporalEvaluator(model_name=model_name, device=device)


def main():
    """
    Main function to demonstrate the CLIP evaluator.
    
    This function:
    1. Creates a CLIP evaluator
    2. Generates synthetic test frames (for demonstration only)
    3. Computes and prints the temporal coherence score
    
    Note: In production, this would load real video frames from disk.
    """
    print("Initializing CLIP Temporal Evaluator...")
    
    # Create evaluator
    evaluator = create_clip_evaluator(device="cpu")
    print(f"Model loaded: {evaluator.model_name}")
    print(f"Device: {evaluator.device}")
    
    # Generate synthetic test frames for demonstration
    # In real usage, load frames from data/derived or data/external
    print("\nGenerating synthetic test frames for demonstration...")
    num_frames = 10
    height, width = 224, 224
    channels = 3
    
    # Create smooth transitioning frames (high coherence)
    frames_smooth = []
    for i in range(num_frames):
        # Create a frame with a moving gradient
        frame = np.zeros((height, width, channels), dtype=np.float32)
        for c in range(channels):
            frame[:, :, c] = np.linspace(
                0.0, 1.0, height
            ).reshape(-1, 1) * np.cos(i * 0.5 + c * 0.3)
        frames_smooth.append(frame)
    frames_smooth = np.stack(frames_smooth)
    
    # Create abrupt transitioning frames (low coherence)
    frames_abrupt = []
    for i in range(num_frames):
        # Random frame with abrupt changes
        frame = np.random.rand(height, width, channels).astype(np.float32)
        frames_abrupt.append(frame)
    frames_abrupt = np.stack(frames_abrupt)
    
    # Score smooth frames
    print("\n--- Testing Smooth Transitions ---")
    result_smooth = evaluator.score_clip(frames_smooth)
    print(f"Temporal Coherence Score: {result_smooth['coherence']:.4f}")
    
    # Score abrupt frames
    print("\n--- Testing Abrupt Transitions ---")
    result_abrupt = evaluator.score_clip(frames_abrupt)
    print(f"Temporal Coherence Score: {result_abrupt['coherence']:.4f}")
    
    # Verify expected behavior
    print("\n--- Verification ---")
    if result_smooth['coherence'] > result_abrupt['coherence']:
        print("✓ PASS: Smooth frames have higher coherence than abrupt frames")
    else:
        print("✗ FAIL: Expected smooth frames to have higher coherence")
    
    print("\nCLIP Temporal Evaluator test completed.")


if __name__ == "__main__":
    main()