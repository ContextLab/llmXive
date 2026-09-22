import os
import sys
import json
import time
import gc
import hashlib
import logging
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from datasets import load_dataset
from transformers import AutoModel, AutoConfig
from utils.logging_config import get_logger, log_feature_extraction_progress
from utils.memory_manager import get_processing_plan, calculate_max_frames, generate_temporal_chunks
from utils.error_handler import DataFetchError, retry_with_backoff

# Configure logger for this module
logger = get_logger("extract_features")

@dataclass
class ExtractionStats:
    """Tracks statistics during feature extraction."""
    total_clips: int = 0
    processed_clips: int = 0
    skipped_clips: int = 0
    total_frames_processed: int = 0
    peak_memory_mb: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_clips": self.total_clips,
            "processed_clips": self.processed_clips,
            "skipped_clips": self.skipped_clips,
            "total_frames_processed": self.total_frames_processed,
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "duration_seconds": round(self.end_time - self.start_time, 2)
        }

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

class VideoClipDataset(Dataset):
    """Dataset for streaming video clips with memory-aware chunking."""
    
    def __init__(self, manifest_path: str, model_name: str, max_memory_mb: float = 7000):
        self.manifest_path = Path(manifest_path)
        self.model_name = model_name
        self.max_memory_mb = max_memory_mb
        self.clips = self._load_manifest()
        logger.info(f"Loaded {len(self.clips)} clips from manifest")

    def _load_manifest(self) -> List[Dict[str, Any]]:
        """Load video manifest (JSON or CSV)."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")
        
        with open(self.manifest_path, 'r') as f:
            if self.manifest_path.suffix == '.json':
                return json.load(f)
            else:
                # Fallback for CSV-like structure if needed
                import pandas as pd
                df = pd.read_csv(self.manifest_path)
                return df.to_dict(orient='records')

    def __len__(self):
        return len(self.clips)

    def __getitem__(self, idx):
        clip_info = self.clips[idx]
        return clip_info

def load_model(model_name: str, device: str = "cpu") -> Tuple[Any, Any]:
    """Load pre-trained LingBot-Video model and config."""
    logger.info(f"Loading model: {model_name} on {device}")
    try:
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModel.from_config(config, trust_remote_code=True)
        model = model.to(device)
        model.eval()
        logger.info("Model loaded successfully")
        return model, config
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise DataFetchError(f"Model loading failed: {e}")

def load_video_clips(manifest_path: str, model_name: str) -> VideoClipDataset:
    """Load video clips from manifest with memory constraints."""
    return VideoClipDataset(manifest_path, model_name)

def fetch_video_frame(clip_info: Dict[str, Any], frame_idx: int) -> Optional[np.ndarray]:
    """Fetch a single frame from a video clip (simulated for pipeline)."""
    # In a real implementation, this would use cv2 or decord to extract frames
    # For now, we simulate the frame extraction logic
    try:
        # Placeholder for actual frame extraction
        # Real implementation would use: video = cv2.VideoCapture(clip_info['path'])
        # frame = video.read()[1]
        logger.debug(f"Fetching frame {frame_idx} for clip {clip_info.get('id', 'unknown')}")
        return np.random.rand(1, 3, 224, 224).astype(np.float32)
    except Exception as e:
        logger.warning(f"Failed to fetch frame {frame_idx}: {e}")
        return None

def extract_activations(
    model: Any,
    clip_info: Dict[str, Any],
    device: str = "cpu",
    layer_name: str = "blocks.12"  # Example intermediate layer
) -> Dict[str, Any]:
    """Extract latent vectors and expert masks from intermediate DiT layers."""
    stats = ExtractionStats()
    stats.start_time = time.time()
    
    # Get processing plan based on memory constraints
    processing_plan = get_processing_plan(
        clip_info.get('duration', 10),
        max_memory_mb=7000
    )
    
    logger.info(f"Processing plan for clip {clip_info.get('id')}: {processing_plan}")
    
    latent_vectors = []
    expert_masks = []
    
    # Process chunks or subsampled frames
    if processing_plan['mode'] == 'chunked':
        chunks = generate_temporal_chunks(
            total_frames=processing_plan['total_frames'],
            chunk_size=processing_plan['chunk_size']
        )
        logger.info(f"Processing {len(chunks)} temporal chunks")
        
        for chunk_start, chunk_end in chunks:
            # Extract features for this chunk
            chunk_frames = []
            for i in range(chunk_start, chunk_end):
                frame = fetch_video_frame(clip_info, i)
                if frame is not None:
                    chunk_frames.append(frame)
            
            if not chunk_frames:
                continue
            
            # Stack frames and process
            chunk_tensor = torch.tensor(np.stack(chunk_frames)).to(device)
            
            with torch.no_grad():
                # Forward pass to get intermediate activations
                # This is a simplified version - real implementation would access specific layers
                outputs = model(chunk_tensor, output_hidden_states=True)
                
                # Extract latent vector (mean pooling over sequence)
                latent = outputs.hidden_states[-1].mean(dim=1).cpu().numpy()
                latent_vectors.append(latent)
                
                # Extract expert mask (if MoE)
                if hasattr(outputs, 'aux_outputs') and 'expert_mask' in outputs.aux_outputs:
                    mask = outputs.aux_outputs['expert_mask'].cpu().numpy()
                    expert_masks.append(mask)
    
    elif processing_plan['mode'] == 'subsampled':
        indices = processing_plan['subsample_indices']
        logger.info(f"Processing {len(indices)} subsampled frames")
        
        for idx in indices:
            frame = fetch_video_frame(clip_info, idx)
            if frame is None:
                continue
            
            frame_tensor = torch.tensor(frame).unsqueeze(0).to(device)
            
            with torch.no_grad():
                outputs = model(frame_tensor, output_hidden_states=True)
                latent = outputs.hidden_states[-1].mean(dim=1).cpu().numpy()
                latent_vectors.append(latent)
                
                if hasattr(outputs, 'aux_outputs') and 'expert_mask' in outputs.aux_outputs:
                    mask = outputs.aux_outputs['expert_mask'].cpu().numpy()
                    expert_masks.append(mask)
    
    # Aggregate results
    result = {
        'clip_id': clip_info.get('id', 'unknown'),
        'latent_vectors': np.concatenate(latent_vectors, axis=0) if latent_vectors else np.array([]),
        'expert_masks': np.concatenate(expert_masks, axis=0) if expert_masks else np.array([]),
        'frames_processed': len(latent_vectors),
        'processing_time': time.time() - stats.start_time
    }
    
    # Log progress
    log_feature_extraction_progress(
        clip_id=result['clip_id'],
        frames_processed=result['frames_processed'],
        memory_mb=get_memory_usage_mb(),
        processing_time=result['processing_time']
    )
    
    return result

def save_features(
    results: List[Dict[str, Any]],
    output_path: str,
    metadata_path: str,
    stats: ExtractionStats
):
    """Save extracted features and metadata."""
    output_path = Path(output_path)
    metadata_path = Path(metadata_path)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Stack all results
    all_latents = []
    all_masks = []
    clip_ids = []
    
    for r in results:
        if r['latent_vectors'].size > 0:
            all_latents.append(r['latent_vectors'])
            all_masks.append(r['expert_masks'])
            clip_ids.append(r['clip_id'])
    
    if not all_latents:
        logger.warning("No features extracted, saving empty arrays")
        all_latents = [np.array([])]
        all_masks = [np.array([])]
    
    features = {
        'clip_ids': np.array(clip_ids),
        'latents': np.concatenate(all_latents, axis=0),
        'masks': np.concatenate(all_masks, axis=0)
    }
    
    # Save features
    np.save(output_path, features)
    logger.info(f"Saved features to {output_path}")
    
    # Save metadata
    metadata = {
        'stats': stats.to_dict(),
        'feature_shape': features['latents'].shape,
        'mask_shape': features['masks'].shape,
        'timestamp': time.time(),
        'model_name': 'lingbot-video-v1'
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

def main():
    """Main entry point for feature extraction."""
    logger.info("Starting feature extraction pipeline")
    
    # Configuration
    model_name = "lingbot-video-base"
    manifest_path = "data/raw/video_manifest.json"
    output_features = "data/processed/features.npy"
    output_metadata = "data/processed/features_metadata.json"
    
    # Initialize stats
    stats = ExtractionStats()
    stats.start_time = time.time()
    
    try:
        # Load model
        model, config = load_model(model_name)
        
        # Load video clips
        dataset = load_video_clips(manifest_path, model_name)
        stats.total_clips = len(dataset)
        
        # Process clips
        results = []
        for i, clip_info in enumerate(dataset):
            logger.info(f"Processing clip {i+1}/{stats.total_clips}: {clip_info.get('id')}")
            
            # Check memory usage
            current_mem = get_memory_usage_mb()
            if current_mem > 6500:  # Safety margin
                logger.warning(f"High memory usage: {current_mem:.1f} MB, triggering GC")
                gc.collect()
            
            result = extract_activations(model, clip_info)
            results.append(result)
            
            stats.processed_clips += 1
            stats.total_frames_processed += result['frames_processed']
            stats.peak_memory_mb = max(stats.peak_memory_mb, get_memory_usage_mb())
            
            # Log periodic progress
            if (i + 1) % 10 == 0:
                log_feature_extraction_progress(
                    clip_id=clip_info.get('id', 'unknown'),
                    frames_processed=result['frames_processed'],
                    memory_mb=current_mem,
                    processing_time=time.time() - stats.start_time
                )
    
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise
    finally:
        stats.end_time = time.time()
        stats.peak_memory_mb = max(stats.peak_memory_mb, get_memory_usage_mb())
        
        # Save results
        save_features(results, output_features, output_metadata, stats)
        
        logger.info(f"Feature extraction completed. Stats: {stats.to_dict()}")

if __name__ == "__main__":
    main()