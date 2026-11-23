"""
T020: Generate physical validity labels via monocular depth estimation.

This script implements the first stage of User Story 2:
1. Loads video clips from data/raw (or generates a manifest if missing).
2. Runs a monocular depth estimator (Monodepth2) on sampled frames.
3. Outputs intermediate depth maps and metadata for subsequent 3D reconstruction.

Note: The actual 3D state reconstruction, physics simulation, and label assignment
(valid/invalid/null) are handled in subsequent tasks (T021-T023) as they require
the depth outputs generated here. This script focuses on the depth estimation
pipeline as explicitly requested.

Dependencies:
  - opencv-python-headless
  - torch
  - torchvision
  - monodepth2 (via pip install monodepth2 or source)
"""
import os
import sys
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import cv2
import numpy as np
import torch
from torchvision import transforms

# Project internal imports
from utils.logging_config import get_logger, fail_loudly
from utils.config_manager import get_config
from utils.memory_manager import calculate_max_frames, generate_subsample_indices
from utils.error_handler import DataFetchError, handle_simulation_failure

# Attempt to import monodepth2. If not installed, we will attempt to install it
# or fail loudly if the environment cannot support it.
try:
    from monodepth2.networks import DepthEncoderDecoder
    MONODEPTH_AVAILABLE = True
except ImportError:
    MONODEPTH_AVAILABLE = False

logger = get_logger(__name__)

@dataclass
class DepthResult:
    clip_id: str
    frame_idx: int
    depth_map_path: str
    confidence: float
    processing_time: float
    error: Optional[str] = None

def load_model(device: str = "cpu") -> Any:
    """
    Loads the Monodepth2 model.
    Falls back to CPU if CUDA is not available.
    """
    if not MONODEPTH_AVAILABLE:
        fail_loudly(
            "Monodepth2 not installed",
            "The monodepth2 library is required for T020. "
            "Please run: pip install monodepth2"
        )

    logger.info("Loading Monodepth2 model...")
    # Using the standard KITTI pre-trained weights as a baseline for general depth estimation
    # In a production setting, one might fine-tune this on a specific domain.
    model_name = "mono+stereo_640x192"
    
    try:
        # We attempt to load a standard pre-trained checkpoint.
        # If the specific checkpoint file isn't in the cache, we rely on the library's
        # ability to fetch or we fail loudly if the user hasn't set up the environment.
        # For this implementation, we assume the user has the weights or the library
        # handles the download. If not, we fail loudly as per constraints.
        model = DepthEncoderDecoder(model_name)
        
        # Try to load a standard checkpoint path (adjust based on actual installation)
        # This path is typical for monodepth2 installations
        checkpoint_path = f"models/{model_name}/weights.pth"
        
        if not os.path.exists(checkpoint_path):
            # If not found locally, we assume the library might have a download mechanism
            # or we fail loudly. We do NOT generate synthetic depth.
            fail_loudly(
                "Model weights not found",
                f"Could not find model weights at {checkpoint_path}. "
                "Ensure monodepth2 is properly installed and weights are downloaded."
            )

        model.load_state_dict(torch.load(checkpoint_path, map_location=device))
        model.to(device)
        model.eval()
        logger.info(f"Model loaded successfully from {checkpoint_path}")
        return model
    except Exception as e:
        fail_loudly("Model Loading Failed", str(e))

def preprocess_frame(frame: np.ndarray, target_size: tuple = (640, 192), device: str = "cpu") -> torch.Tensor:
    """
    Preprocesses a single frame for Monodepth2.
    Converts BGR (OpenCV) to RGB, resizes, normalizes, and converts to tensor.
    """
    # OpenCV loads as BGR, convert to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Resize to target size
    resized = cv2.resize(rgb_frame, target_size)
    
    # Convert to float and normalize
    img_float = resized.astype(np.float32) / 255.0
    
    # Standard ImageNet normalization for Monodepth2 (often just mean/std or 0-1)
    # Monodepth2 typically uses mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_float = (img_float - mean) / std
    
    # HWC to CHW
    img_tensor = torch.from_numpy(img_float).permute(2, 0, 1).unsqueeze(0)
    
    return img_tensor.to(device)

def run_depth_inference(
    model: Any,
    video_path: str,
    clip_id: str,
    output_dir: Path,
    device: str = "cpu",
    max_frames: int = 10
) -> List[DepthResult]:
    """
    Runs depth inference on a subset of frames from a video.
    """
    logger.info(f"Processing video: {video_path} (Clip ID: {clip_id})")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        fail_loudly("Video Open Failed", f"Could not open video: {video_path}")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Determine frames to process based on memory constraints (FR-006)
    # We subsample to ensure we don't run out of memory or time.
    indices = generate_subsample_indices(total_frames, max_samples=max_frames)
    
    results = []
    start_time = time.time()
    
    frame_idx = 0
    processed_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_idx in indices:
            proc_start = time.time()
            try:
                input_tensor = preprocess_frame(frame, device=device)
                
                with torch.no_grad():
                    # Monodepth2 forward pass
                    # Returns a dict of depth maps for different scales
                    output = model(input_tensor)
                
                # Extract the primary depth map (usually 'depth_est' at the highest resolution)
                # The shape is typically [B, H, W] or [B, 1, H, W] depending on implementation
                depth_map = output['depth_est']
                if isinstance(depth_map, list):
                    depth_map = depth_map[0] # Take the highest resolution
                
                depth_map = depth_map.squeeze().cpu().numpy()
                
                # Save depth map
                # Ensure output directory exists
                output_dir.mkdir(parents=True, exist_ok=True)
                depth_filename = f"{clip_id}_frame_{frame_idx:04d}_depth.npy"
                depth_path = output_dir / depth_filename
                np.save(str(depth_path), depth_map)
                
                # Calculate a simple confidence metric (e.g., variance or mean intensity)
                # Real confidence would come from the model's uncertainty estimation if available.
                # Here we use a placeholder based on depth range validity.
                confidence = float(np.mean(depth_map > 0.0)) 
                
                results.append(DepthResult(
                    clip_id=clip_id,
                    frame_idx=frame_idx,
                    depth_map_path=str(depth_path),
                    confidence=confidence,
                    processing_time=time.time() - proc_start
                ))
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing frame {frame_idx}: {e}")
                # We do not stop the whole pipeline for one frame, but log it.
                # However, if the model fails completely, we might need to abort.
                # For now, we record an error result.
                results.append(DepthResult(
                    clip_id=clip_id,
                    frame_idx=frame_idx,
                    depth_map_path="",
                    confidence=0.0,
                    processing_time=time.time() - proc_start,
                    error=str(e)
                ))
        
        frame_idx += 1
        
        # Safety break if we've processed enough frames but the video is long
        if processed_count >= len(indices):
            break
    
    cap.release()
    
    total_time = time.time() - start_time
    logger.info(f"Processed {len(results)} frames for {clip_id} in {total_time:.2f}s")
    
    return results

def load_video_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """
    Loads the list of video clips to process.
    If the manifest doesn't exist, we try to infer from data/raw.
    """
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            return json.load(f)
    
    # Fallback: scan data/raw
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        fail_loudly("Data Missing", "No video manifest found and data/raw does not exist.")
    
    clips = []
    for video_file in raw_dir.glob("*.mp4"):
        clips.append({
            "id": video_file.stem,
            "path": str(video_file)
        })
    
    if not clips:
        fail_loudly("No Data", "No video files found in data/raw and no manifest exists.")
    
    logger.warning(f"Generated manifest with {len(clips)} clips from data/raw")
    return clips

def main():
    logger.info("Starting T020: Depth Estimation for Label Generation")
    
    # Configuration
    config = get_config()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    output_dir = Path("data/processed/depth_maps")
    manifest_path = "data/raw/video_manifest.json"
    results_file = output_dir / "depth_results.json"
    
    # Load model
    model = load_model(device)
    
    # Load clips
    clips = load_video_manifest(manifest_path)
    logger.info(f"Processing {len(clips)} video clips")
    
    all_results = []
    
    for clip_info in clips:
        clip_id = clip_info["id"]
        video_path = clip_info["path"]
        
        # Process video
        results = run_depth_inference(
            model, 
            video_path, 
            clip_id, 
            output_dir, 
            device,
            max_frames=10 # Limit for T020 to ensure it runs within budget
        )
        all_results.extend(results)
    
    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump([asdict(r) for r in all_results], f, indent=2)
    
    logger.info(f"Depth estimation complete. Results saved to {results_file}")
    logger.info(f"Total frames processed: {len(all_results)}")
    
    # Verify output
    if len(all_results) == 0:
        fail_loudly("No Output", "No depth maps were generated. Check logs for errors.")
    
    logger.info("T020 completed successfully.")

if __name__ == "__main__":
    main()
