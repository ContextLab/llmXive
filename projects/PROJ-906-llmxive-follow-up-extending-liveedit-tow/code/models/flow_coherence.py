import os
import logging
import torch
import numpy as np
import cv2
from typing import Dict, Any, Optional, List, Tuple, Generator
from dataclasses import dataclass, field
from config import ensure_directories, get_default_config
from utils.logger import get_logger
from data.flow import compute_farneback_flow, compute_flow_magnitude
from metrics.resource import MemoryProfiler

logger = get_logger(__name__)

@dataclass
class FlowCoherenceResult:
    clip_id: str
    frames: List[np.ndarray]
    invalid_flow_mask: List[bool]
    peak_memory_mb: float
    inference_time_seconds: float

class FlowCoherenceModule:
    """
    Flow-Coherence module: replaces Mask Cache, warps latents using pre-computed flow,
    removes attention layers. Implements invalid flow handling (T021a).
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_default_config()
        self.device = torch.device("cpu")
        self.invalid_flow_count = 0
        self.total_frames = 0

    def _handle_invalid_flow(self, flow_field: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        T021a Implementation: Detect NaN/Infinity vectors in flow field.
        Fallback to identity warp (zero displacement) and set invalid_flow flag.
        
        Args:
            flow_field: numpy array of shape (H, W, 2) containing flow vectors (u, v)
        
        Returns:
            Tuple of (cleaned_flow_field, is_invalid)
        """
        is_invalid = False
        
        # Check for NaN or Infinity in the flow field
        if np.any(np.isnan(flow_field)) or np.any(np.isinf(flow_field)):
            logger.warning(f"Detected invalid flow vectors (NaN/Inf). Fallback to identity warp.")
            is_invalid = True
            self.invalid_flow_count += 1
            
            # Create identity flow (zero displacement)
            # Identity warp means no movement: u=0, v=0 everywhere
            h, w = flow_field.shape[0], flow_field.shape[1]
            flow_field = np.zeros((h, w, 2), dtype=np.float32)
        
        return flow_field, is_invalid

    def _warp_latents(self, latents: torch.Tensor, flow_field: np.ndarray) -> torch.Tensor:
        """
        Warp latents using the provided flow field with bilinear interpolation.
        Handles invalid flow by falling back to identity warp.
        
        Args:
            latents: Tensor of shape (B, C, H, W)
            flow_field: numpy array of shape (H, W, 2)
        
        Returns:
            Warped latents tensor of shape (B, C, H, W)
        """
        self.total_frames += 1
        
        # Validate and clean flow field (T021a)
        cleaned_flow, is_invalid = self._handle_invalid_flow(flow_field)
        
        if is_invalid:
            # Identity warp: return latents unchanged
            logger.debug(f"Frame {self.total_frames}: Identity warp applied due to invalid flow.")
            return latents
        
        # Convert flow to sampling grid format for cv2.remap
        # flow_field is (H, W, 2) with (u, v) displacements
        # cv2.remap expects map1 and map2 as (H, W) or (H, W, 2) for float32
        
        h, w = latents.shape[2], latents.shape[3]
        
        # Ensure flow is float32 and within valid range
        cleaned_flow = cleaned_flow.astype(np.float32)
        
        # Create grid for remap: x = u + x, y = v + y
        # We need to convert displacement to absolute coordinates
        x_coords, y_coords = np.meshgrid(np.arange(w), np.arange(h))
        map_x = (x_coords + cleaned_flow[:, :, 0]).astype(np.float32)
        map_y = (y_coords + cleaned_flow[:, :, 1]).astype(np.float32)
        
        warped_latents_list = []
        
        for b in range(latents.shape[0]):
            # Process each channel
            warped_channels = []
            for c in range(latents.shape[1]):
                # Extract single channel
                channel = latents[b, c].cpu().numpy()
                
                # Apply remap with bilinear interpolation
                # Border mode: constant with 0 value
                warped_channel = cv2.remap(
                    channel,
                    map_x,
                    map_y,
                    interpolation=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=0.0
                )
                warped_channels.append(warped_channel)
            
            # Stack channels back
            warped_channel_tensor = np.stack(warped_channels, axis=0)
            warped_latents_list.append(warped_channel_tensor)
        
        # Stack batch dimension
        warped_latents = torch.from_numpy(np.stack(warped_latents_list, axis=0)).to(latents.dtype)
        
        return warped_latents

    def compute_flow_coherence(
        self,
        latents: torch.Tensor,
        flow_path: str,
        clip_id: str
    ) -> FlowCoherenceResult:
        """
        Main inference method for Flow-Coherence.
        
        Args:
            latents: Input latent tensor
            flow_path: Path to pre-computed flow file
            clip_id: Identifier for the current clip
        
        Returns:
            FlowCoherenceResult with warped frames and metadata
        """
        profiler = MemoryProfiler()
        profiler.start()
        
        start_time = time.time()
        
        # Load flow field
        if not os.path.exists(flow_path):
            raise FileNotFoundError(f"Flow file not found: {flow_path}")
        
        flow_data = np.load(flow_path)
        # Assuming flow_data contains 'flow' key with (T, H, W, 2) or similar structure
        # Adjust based on actual storage format from T009
        if isinstance(flow_data, dict):
            flow_field = flow_data.get('flow', None)
        else:
            flow_field = flow_data
        
        if flow_field is None:
            raise ValueError(f"Could not extract flow field from {flow_path}")
        
        # Process each frame in the flow sequence
        warped_frames = []
        invalid_flags = []
        
        # Handle both 4D (T, H, W, 2) and 3D (H, W, 2) flow fields
        if flow_field.ndim == 4:
            # Multiple frames
            for t in range(flow_field.shape[0]):
                flow_t = flow_field[t]
                warped_latent = self._warp_latents(latents, flow_t)
                
                # Convert latent to frame representation (simplified)
                # In real implementation, this would involve VAE decoding
                frame = warped_latent[0].cpu().numpy()
                warped_frames.append(frame)
                
                # Record invalid flag for this frame
                is_invalid = self.invalid_flow_count > 0 and (t == 0 or 
                       (np.any(np.isnan(flow_t)) or np.any(np.isinf(flow_t))))
                invalid_flags.append(is_invalid)
        else:
            # Single frame flow
            warped_latent = self._warp_latents(latents, flow_field)
            frame = warped_latent[0].cpu().numpy()
            warped_frames.append(frame)
            invalid_flags.append(self.invalid_flow_count > 0)
        
        end_time = time.time()
        profiler.stop()
        
        peak_memory = profiler.get_peak_memory_mb()
        
        return FlowCoherenceResult(
            clip_id=clip_id,
            frames=warped_frames,
            invalid_flow_mask=invalid_flags,
            peak_memory_mb=peak_memory,
            inference_time_seconds=end_time - start_time
        )

def run_flow_coherence_inference(
    input_dir: str,
    output_dir: str,
    flow_dir: str,
    clip_ids: Optional[List[str]] = None
) -> List[FlowCoherenceResult]:
    """
    Runner for Flow-Coherence inference pipeline.
    Processes clips one-by-one to manage RAM.
    
    Args:
        input_dir: Directory containing input latents
        output_dir: Directory to save results
        flow_dir: Directory containing pre-computed flow fields
        clip_ids: Optional list of clip IDs to process
    
    Returns:
        List of FlowCoherenceResult objects
    """
    ensure_directories(output_dir)
    
    config = get_default_config()
    module = FlowCoherenceModule(config)
    
    results = []
    
    # Get clip IDs if not provided
    if clip_ids is None:
        clip_ids = [f[:-4] for f in os.listdir(input_dir) if f.endswith('.npz')]
    
    for clip_id in clip_ids:
        logger.info(f"Processing clip: {clip_id}")
        
        try:
            # Load latents (simplified - in real impl, load from file)
            latent_path = os.path.join(input_dir, f"{clip_id}.npz")
            if not os.path.exists(latent_path):
                logger.warning(f"Latent file not found: {latent_path}, skipping.")
                continue
            
            latent_data = np.load(latent_path)
            latents = torch.from_numpy(latent_data.get('latents', np.zeros((1, 4, 64, 64))))
            
            # Load flow
            flow_path = os.path.join(flow_dir, f"{clip_id}_flow.npz")
            
            # Run inference
            result = module.compute_flow_coherence(latents, flow_path, clip_id)
            
            # Save result
            result_path = os.path.join(output_dir, f"{clip_id}_flow_result.json")
            with open(result_path, 'w') as f:
                json.dump({
                    'clip_id': result.clip_id,
                    'invalid_flow_count': sum(result.invalid_flow_mask),
                    'total_frames': len(result.frames),
                    'peak_memory_mb': result.peak_memory_mb,
                    'inference_time_seconds': result.inference_time_seconds
                }, f, indent=2)
            
            results.append(result)
            
            # Cleanup
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            gc.collect()
            
        except Exception as e:
            logger.error(f"Error processing clip {clip_id}: {e}")
            raise
    
    return results

def main():
    """CLI entry point for flow-coherence inference."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Flow-Coherence Inference")
    parser.add_argument("--input-dir", type=str, required=True, help="Input latents directory")
    parser.add_argument("--output-dir", type=str, required=True, help="Output results directory")
    parser.add_argument("--flow-dir", type=str, required=True, help="Flow fields directory")
    parser.add_argument("--clip-ids", type=str, nargs="+", default=None, help="Specific clip IDs to process")
    
    args = parser.parse_args()
    
    results = run_flow_coherence_inference(
        args.input_dir,
        args.output_dir,
        args.flow_dir,
        args.clip_ids
    )
    
    logger.info(f"Processed {len(results)} clips successfully.")
    logger.info(f"Total invalid flow frames: {sum(r.invalid_flow_count for r in results)}")

if __name__ == "__main__":
    main()
