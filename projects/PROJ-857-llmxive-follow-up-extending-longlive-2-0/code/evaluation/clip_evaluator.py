"""
CLIP-based Temporal Coherence Evaluator.

This module implements a frozen CLIP-ViT model loader for scoring the temporal
coherence of video clips. It ensures no gradients are computed and the model
remains in evaluation mode.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import CLIPModel, CLIPProcessor
from typing import List, Union, Optional, Tuple
import numpy as np
import os
import sys
from pathlib import Path

# Ensure project root is in path for imports if run as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

class ClipTemporalEvaluator:
    """
    Evaluates temporal coherence of video clips using a frozen CLIP-ViT model.
    
    The model is loaded in eval mode with gradients disabled to ensure
    efficient inference and prevent any updates.
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: Optional[str] = None):
        """
        Initialize the evaluator with a frozen CLIP model.
        
        Args:
            model_name: HuggingFace model identifier for CLIP.
            device: Device to run inference on (default: cuda if available, else cpu).
        """
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        
        # Load model and processor
        # We explicitly set torch.no_grad() context during forward passes, 
        # but also load the model in eval mode.
        self.model = CLIPModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        
        # Freeze all parameters explicitly
        for param in self.model.parameters():
            param.requires_grad = False
        
        self.processor = CLIPProcessor.from_pretrained(model_name)
        
        # Cache for processed inputs to avoid re-processing if needed (optional optimization)
        self._input_cache = {}

    def encode_video_frames(self, frames: Union[torch.Tensor, np.ndarray]) -> torch.Tensor:
        """
        Encodes a sequence of video frames into feature vectors.
        
        Args:
            frames: A tensor or numpy array of shape (T, H, W, C) where T is time (frames).
                    Values should be in range [0, 255] if uint8, or [0, 1] if float.
                    
        Returns:
            A tensor of shape (T, D) containing frame embeddings.
        """
        if isinstance(frames, np.ndarray):
            frames = torch.from_numpy(frames)
        
        # Normalize to [0, 1] if uint8
        if frames.dtype == torch.uint8:
            frames = frames.float() / 255.0
        
        # Ensure shape is (T, H, W, C) -> (T, C, H, W) for CLIP processor
        if frames.dim() == 4 and frames.shape[-1] == 3:
            frames = frames.permute(0, 3, 1, 2) # (T, C, H, W)
        
        # Process frames
        # CLIP expects a list of PIL images or a batch of tensors (B, C, H, W)
        # We process each frame individually or batch if memory allows.
        # For robustness, we process as a batch if T is small, otherwise chunk.
        
        # Convert to list of tensors for processor
        frame_list = [frames[i] for i in range(frames.shape[0])]
        
        inputs = self.processor(images=frame_list, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            # Get image embeddings
            # CLIPModel.image_model returns a BaseModelOutputWithPooling
            image_outputs = self.model.get_image_features(**inputs)
            # image_outputs shape: (T, D)
            
        return image_outputs

    def compute_temporal_coherence(self, frames: Union[torch.Tensor, np.ndarray]) -> float:
        """
        Computes a temporal coherence score for a video clip.
        
        The score is based on the cosine similarity between consecutive frame embeddings.
        Higher scores indicate more consistent motion/temporal flow.
        
        Args:
            frames: Video frames of shape (T, H, W, C).
                    
        Returns:
            A float score between -1 and 1 (typically > 0 for coherent videos).
        """
        if frames.shape[0] < 2:
            return 1.0 # Trivial case: single frame is perfectly coherent with itself
        
        embeddings = self.encode_video_frames(frames)
        
        # Compute cosine similarity between consecutive frames
        # embeddings: (T, D)
        # embeddings[1:] vs embeddings[:-1]
        
        v1 = embeddings[:-1]
        v2 = embeddings[1:]
        
        # Normalize vectors
        v1_norm = F.normalize(v1, p=2, dim=1)
        v2_norm = F.normalize(v2, p=2, dim=1)
        
        # Cosine similarity
        similarities = torch.sum(v1_norm * v2_norm, dim=1)
        
        # Average similarity
        avg_similarity = similarities.mean().item()
        
        return avg_similarity

    def score_batch(self, clips: List[Union[torch.Tensor, np.ndarray]]) -> List[float]:
        """
        Scores a batch of video clips.
        
        Args:
            clips: List of video frames, each of shape (T, H, W, C).
                    
        Returns:
            List of coherence scores.
        """
        return [self.compute_temporal_coherence(clip) for clip in clips]


def create_clip_evaluator(model_name: str = "openai/clip-vit-base-patch32", device: Optional[str] = None) -> ClipTemporalEvaluator:
    """
    Factory function to create a ClipTemporalEvaluator instance.
    
    Args:
        model_name: HuggingFace model identifier.
        device: Target device.
        
    Returns:
        Initialized ClipTemporalEvaluator.
    """
    return ClipTemporalEvaluator(model_name=model_name, device=device)


def main():
    """
    Main entry point for running the evaluator as a standalone script.
    This demonstrates loading the model and scoring a synthetic (or real) clip.
    """
    print("Initializing CLIP Temporal Evaluator...")
    evaluator = create_clip_evaluator()
    print(f"Model loaded on device: {evaluator.device}")
    
    # Create a dummy clip for testing (e.g., 4 seconds @ 15 fps = 60 frames)
    # Shape: (60, 224, 224, 3)
    num_frames = 60
    height, width = 224, 224
    dummy_clip = np.random.randint(0, 255, (num_frames, height, width, 3), dtype=np.uint8)
    
    print(f"Scoring dummy clip of shape {dummy_clip.shape}...")
    score = evaluator.compute_temporal_coherence(dummy_clip)
    print(f"Temporal Coherence Score: {score:.4f}")
    
    # Verify model is frozen
    has_grad = False
    for name, param in evaluator.model.named_parameters():
        if param.requires_grad:
            has_grad = True
            break
    
    if has_grad:
        print("ERROR: Model parameters are not frozen!")
        sys.exit(1)
    else:
        print("SUCCESS: Model is frozen (no gradients).")

if __name__ == "__main__":
    main()
