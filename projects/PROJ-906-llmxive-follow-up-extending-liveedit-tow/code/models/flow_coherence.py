"""
Flow-Coherence Module for LiveEdit Follow-up.
Implements region-tracking logic replacement using pre-computed optical flow.
"""
import os
import logging
import torch
import numpy as np
import cv2
from typing import Dict, Any, Optional, List, Tuple, Generator
from dataclasses import dataclass, field
from config import get_default_config
from utils.logger import get_logger
from data.flow import compute_farneback_flow

logger = get_logger(__name__)

@dataclass
class FlowCoherenceResult:
    """Result container for Flow-Coherence inference."""
    video_id: str
    frames: List[np.ndarray]
    flow_stats: Dict[str, float]
    invalid_flow_count: int
    total_frames: int
    peak_memory_mb: float
    inference_time_sec: float
    invalid_flow_flags: List[bool] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class FlowCoherenceModule:
    """
    Flow-Coherence Module that replaces the Mask Cache.
    Warps latents using pre-computed optical flow and handles invalid flow vectors.
    """
    
    def __init__(self, device: str = "cpu", config: Optional[Dict] = None):
        self.device = device
        self.config = config or get_default_config()
        self.logger = get_logger(__name__)
        
        # Thresholds for invalid flow detection
        self.nan_threshold = 1e5
        self.inf_threshold = 1e5
        
    def _validate_flow_vector(self, flow: np.ndarray) -> Tuple[bool, np.ndarray]:
        """
        Validates flow vectors for NaN or Infinity values.
        Returns (is_valid, cleaned_flow).
        If invalid, returns identity warp (zeros) and False.
        """
        has_nan = np.any(np.isnan(flow))
        has_inf = np.any(np.isinf(flow))
        
        if has_nan or has_inf:
            self.logger.warning("Invalid flow vector detected (NaN/Inf). Falling back to identity warp.")
            # Create identity flow (zero displacement)
            h, w = flow.shape[:2]
            identity_flow = np.zeros_like(flow)
            return False, identity_flow
        
        # Check for extreme values that might indicate errors
        if np.any(np.abs(flow) > self.nan_threshold):
            self.logger.warning(f"Extreme flow values detected (> {self.nan_threshold}). Falling back to identity warp.")
            h, w = flow.shape[:2]
            identity_flow = np.zeros_like(flow)
            return False, identity_flow
            
        return True, flow

    def _warp_latents(self, latent: np.ndarray, flow: np.ndarray, frame_idx: int) -> np.ndarray:
        """
        Warps latent representation using optical flow.
        Implements forward warping with bilinear interpolation.
        """
        h, w = flow.shape[:2]
        
        # Create meshgrid for coordinates
        y, x = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
        
        # Add flow to coordinates
        x_warped = x + flow[..., 0]
        y_warped = y + flow[..., 1]
        
        # Handle boundary conditions
        x_warped = np.clip(x_warped, 0, w - 1)
        y_warped = np.clip(y_warped, 0, h - 1)
        
        # Bilinear interpolation
        x0 = np.floor(x_warped).astype(int)
        y0 = np.floor(y_warped).astype(int)
        x1 = np.minimum(x0 + 1, w - 1)
        y1 = np.minimum(y0 + 1, h - 1)
        
        # Weights
        wa = (x1 - x_warped) * (y1 - y_warped)
        wb = (x1 - x_warped) * (y_warped - y0)
        wc = (x_warped - x0) * (y1 - y_warped)
        wd = (x_warped - x0) * (y_warped - y0)
        
        # Sample from original latent
        if len(latent.shape) == 3:  # Single channel
            warped = (
                wa * latent[y0, x0] +
                wb * latent[y0, x1] +
                wc * latent[y1, x0] +
                wd * latent[y1, x1]
            )
        else:  # Multi-channel
            warped = np.zeros_like(latent)
            for c in range(latent.shape[2]):
                warped[:, :, c] = (
                    wa * latent[y0, x0, c] +
                    wb * latent[y0, x1, c] +
                    wc * latent[y1, x0, c] +
                    wd * latent[y1, x1, c]
                )
        
        return warped

    def process_frame_sequence(
        self,
        frames: List[np.ndarray],
        flow_map: Optional[np.ndarray] = None,
        mask: Optional[np.ndarray] = None
    ) -> FlowCoherenceResult:
        """
        Process a sequence of frames with flow coherence.
        
        Args:
            frames: List of frame arrays (H, W, C)
            flow_map: Pre-computed optical flow map (H, W, 2)
            mask: Optional mask for editing region
            
        Returns:
            FlowCoherenceResult with processed frames and metadata
        """
        if not frames:
            raise ValueError("Empty frame sequence provided")
        
        processed_frames = []
        invalid_flow_flags = []
        invalid_flow_count = 0
        flow_magnitudes = []
        
        # Compute flow if not provided
        if flow_map is None:
            self.logger.info("Computing optical flow for frame sequence...")
            # Compute flow between first two frames as reference
            if len(frames) >= 2:
                flow_map = compute_farneback_flow(frames[0], frames[1])
            else:
                # Single frame - create identity flow
                h, w = frames[0].shape[:2]
                flow_map = np.zeros((h, w, 2), dtype=np.float32)
        
        # Process each frame
        for i, frame in enumerate(frames):
            # Convert to float for processing
            frame_float = frame.astype(np.float32) / 255.0
            
            # Validate and clean flow
            is_valid, clean_flow = self._validate_flow_vector(flow_map)
            
            if not is_valid:
                invalid_flow_count += 1
                invalid_flow_flags.append(True)
                # Use identity warp (no change) for invalid flow
                processed_frame = frame_float
            else:
                invalid_flow_flags.append(False)
                # Warp the frame using flow
                processed_frame = self._warp_latents(frame_float, clean_flow, i)
            
            # Apply mask if provided
            if mask is not None and mask.shape[:2] == frame.shape[:2]:
                # Simple masking - keep original in masked region
                mask_float = mask.astype(np.float32) / 255.0
                processed_frame = (
                    processed_frame * (1 - mask_float) + 
                    frame_float * mask_float
                )
            
            # Convert back to uint8
            processed_frame = np.clip(processed_frame * 255, 0, 255).astype(np.uint8)
            processed_frames.append(processed_frame)
            
            # Track flow magnitude for statistics
            flow_mag = np.sqrt(np.sum(clean_flow**2, axis=2))
            flow_magnitudes.append(np.mean(flow_mag))
        
        # Compute statistics
        stats = {
            "mean_flow_magnitude": float(np.mean(flow_magnitudes)) if flow_magnitudes else 0.0,
            "max_flow_magnitude": float(np.max(flow_magnitudes)) if flow_magnitudes else 0.0,
            "invalid_flow_ratio": float(invalid_flow_count / len(frames)) if frames else 0.0,
            "total_invalid_frames": invalid_flow_count,
            "total_frames": len(frames)
        }
        
        return FlowCoherenceResult(
            video_id="unknown",
            frames=processed_frames,
            flow_stats=stats,
            invalid_flow_count=invalid_flow_count,
            total_frames=len(frames),
            peak_memory_mb=0.0,
            inference_time_sec=0.0,
            invalid_flow_flags=invalid_flow_flags
        )

def run_flow_coherence_inference(
    frames: List[np.ndarray],
    flow_map: Optional[np.ndarray] = None,
    mask: Optional[np.ndarray] = None,
    device: str = "cpu"
) -> FlowCoherenceResult:
    """
    Run flow-coherence inference on a sequence of frames.
    
    Args:
        frames: List of frame arrays (H, W, C)
        flow_map: Pre-computed optical flow map (H, W, 2)
        mask: Optional mask for editing region
        device: Device to run on (cpu or cuda)
        
    Returns:
        FlowCoherenceResult with processed frames and metadata
    """
    module = FlowCoherenceModule(device=device)
    return module.process_frame_sequence(frames, flow_map, mask)

def main():
    """Main entry point for flow coherence testing."""
    logger = get_logger(__name__)
    logger.info("Flow Coherence Module - Main Entry Point")
    
    # Example usage
    try:
        # Create dummy frames for testing
        h, w = 256, 256
        dummy_frames = [
            np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
            for _ in range(5)
        ]
        
        # Create dummy flow map
        dummy_flow = np.zeros((h, w, 2), dtype=np.float32)
        dummy_flow[..., 0] = np.random.randn(h, w) * 0.5  # Small random flow
        
        # Run inference
        result = run_flow_coherence_inference(
            frames=dummy_frames,
            flow_map=dummy_flow,
            device="cpu"
        )
        
        logger.info(f"Processed {result.total_frames} frames")
        logger.info(f"Invalid flow count: {result.invalid_flow_count}")
        logger.info(f"Flow stats: {result.flow_stats}")
        
        # Test invalid flow handling
        logger.info("Testing invalid flow handling...")
        invalid_flow = np.full((h, w, 2), np.nan, dtype=np.float32)
        result_invalid = run_flow_coherence_inference(
            frames=dummy_frames,
            flow_map=invalid_flow,
            device="cpu"
        )
        
        logger.info(f"Invalid flow test - Invalid count: {result_invalid.invalid_flow_count}")
        logger.info(f"Invalid flow flags: {result_invalid.invalid_flow_flags}")
        
        print("Flow Coherence Module test completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in flow coherence inference: {e}")
        raise

if __name__ == "__main__":
    main()