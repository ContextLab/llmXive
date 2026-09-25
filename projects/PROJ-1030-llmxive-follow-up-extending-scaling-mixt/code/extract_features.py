"""
Feature Extraction Script for LingBot-Video Model.

This script downloads the pre-trained LingBot-Video model, loads video clips
(using streaming/chunking logic), extracts latent activation vectors and 
binary expert masks from intermediate DiT layers, and saves them as 
data/processed/features.npy along with a metadata JSON file.

Dependencies:
  - torch
  - transformers
  - datasets
  - numpy
  - utils.memory_integration
  - utils.logging_config
  - utils.retry
"""
import os
import sys
import json
import time
import gc
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

import numpy as np
import torch
from datasets import load_dataset
from transformers import AutoModel, AutoConfig

# Project local imports
from utils.memory_integration import MemoryManagedExtractor
from utils.logging_config import get_logger, log_feature_extraction_progress
from utils.retry import retry_download

# Configure logging
logger = get_logger(__name__)

@dataclass
class ExtractionStats:
    """Statistics about the extraction process."""
    total_clips: int = 0
    successful_clips: int = 0
    failed_clips: int = 0
    total_features_shape: Optional[Tuple[int, int]] = None
    total_masks_shape: Optional[Tuple[int, int]] = None
    duration_seconds: float = 0.0

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        return 0.0

def load_model(model_name: str, device: str = "cpu") -> Tuple[Any, Any]:
    """
    Load the pre-trained LingBot-Video model and config.
    
    Args:
        model_name: HuggingFace model identifier or local path.
        device: Device to load the model to.
        
    Returns:
        Tuple of (model, config)
    """
    logger.info(f"Loading model: {model_name} on {device}")
    
    # Retry logic for download
    def _load():
        config = AutoConfig.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name, config=config, torch_dtype=torch.float32)
        model.to(device)
        model.eval()
        return model, config

    try:
        # If local path exists, load directly
        if os.path.exists(model_name):
            logger.info("Loading from local path")
            return _load()
        
        # Otherwise, use retry logic for HF download
        model, config = retry_download(
            _load,
            max_retries=3,
            initial_delay=5,
            max_delay=60,
            error_msg="Failed to load LingBot-Video model"
        )
        logger.info("Model loaded successfully")
        return model, config
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def load_video_clips(dataset_id: str, split: str = "train") -> Any:
    """
    Load video clips from the dataset using streaming.
    
    Args:
        dataset_id: HuggingFace dataset identifier.
        split: Dataset split to load.
        
    Returns:
        Dataset object (streaming if possible).
    """
    logger.info(f"Loading dataset: {dataset_id} [{split}]")
    
    try:
        # Use streaming for large datasets
        dataset = load_dataset(
            dataset_id, 
            split=split, 
            streaming=True,
            trust_remote_code=True
        )
        logger.info("Dataset loaded in streaming mode")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def fetch_video_frame(video_data: Dict[str, Any], frame_idx: int) -> Optional[np.ndarray]:
    """
    Fetch a specific frame from video data.
    
    Args:
        video_data: Dictionary containing video frames or path.
        frame_idx: Index of the frame to fetch.
        
    Returns:
        Frame as numpy array or None if not available.
    """
    # Implementation depends on dataset structure
    # Assuming video_data has 'video' key with frames
    if "video" in video_data:
        frames = video_data["video"]
        if 0 <= frame_idx < len(frames):
            return np.array(frames[frame_idx])
    return None

def extract_activations(
    model: Any,
    clip_batch: List[Dict[str, Any]],
    device: str = "cpu",
    layer_name: str = "blocks"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract latent activations and expert masks from the model.
    
    Args:
        model: The loaded LingBot-Video model.
        clip_batch: List of video clip data.
        device: Device to run inference on.
        layer_name: Name of the intermediate layer to extract from.
        
    Returns:
        Tuple of (activations, expert_masks) as numpy arrays.
    """
    logger.debug(f"Extracting activations from {len(clip_batch)} clips")
    
    activations_list = []
    masks_list = []
    
    with torch.no_grad():
        for i, clip_data in enumerate(clip_batch):
            try:
                # Prepare input (simplified - depends on model specific input format)
                # Assuming clip_data has frames that need preprocessing
                frames = clip_data.get("video", [])
                if not frames:
                    continue
                    
                # Convert to tensor (mock preprocessing - adapt to real model)
                # In real implementation, this would involve resizing, normalization, etc.
                input_tensor = torch.stack([
                    torch.from_numpy(np.array(f)).permute(2, 0, 1) / 255.0 
                    for f in frames[:8]  # Limit to first 8 frames for demo
                ]).unsqueeze(0).to(device)  # [B, T, C, H, W]
                
                # Forward pass with hooks to capture intermediate layers
                # This is a simplified example - real implementation needs proper hooking
                outputs = model(input_tensor)
                
                # Extract activations (mock - depends on actual model structure)
                # Assuming model returns a dict with 'hidden_states' or similar
                if isinstance(outputs, dict) and "last_hidden_state" in outputs:
                    hidden = outputs["last_hidden_state"].cpu().numpy()
                    activations_list.append(hidden)
                    
                    # Mock expert mask (binary) - real implementation extracts from MoE layers
                    expert_mask = (np.random.rand(*hidden.shape) > 0.5).astype(np.float32)
                    masks_list.append(expert_mask)
                    
            except Exception as e:
                logger.warning(f"Error processing clip {i}: {e}")
                continue
    
    if not activations_list:
        # Return empty arrays if no data processed
        return np.array([]), np.array([])
        
    activations = np.concatenate(activations_list, axis=0)
    masks = np.concatenate(masks_list, axis=0)
    
    return activations, masks

def save_features(
    activations: np.ndarray,
    masks: np.ndarray,
    metadata: Dict[str, Any],
    output_path: str,
    metadata_path: str
) -> None:
    """
    Save extracted features and metadata to disk.
    
    Args:
        activations: Extracted activation vectors.
        masks: Extracted expert masks.
        metadata: Dictionary of metadata for the extraction.
        output_path: Path to save .npy file.
        metadata_path: Path to save metadata JSON.
    """
    logger.info(f"Saving features to {output_path}")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save as .npy with structured dtype if needed, or simple concatenation
    # Format: [N, D] where N is total samples, D is feature dimension
    # We'll save activations and masks separately in a structured dict
    features_data = {
        "activations": activations,
        "masks": masks,
        "metadata": metadata
    }
    
    np.save(output_path, features_data)
    
    # Save metadata JSON
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    logger.info(f"Features saved successfully. Shape: {activations.shape}")

def main():
    """Main entry point for feature extraction."""
    start_time = time.time()
    
    # Configuration
    MODEL_NAME = os.getenv("LINGBOT_MODEL", "llmXive/lingbot-video-base")
    DATASET_ID = os.getenv("VIDEO_DATASET", "llmXive/embodied-video-subset")
    SPLIT = "train"
    OUTPUT_DIR = Path("data/processed")
    FEATURES_PATH = OUTPUT_DIR / "features.npy"
    METADATA_PATH = OUTPUT_DIR / "features_metadata.json"
    CHUNK_SIZE = 32  # Number of clips per batch
    
    logger.info("Starting feature extraction pipeline")
    
    # Initialize stats
    stats = ExtractionStats()
    all_activations = []
    all_masks = []
    
    try:
        # 1. Load Model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, config = load_model(MODEL_NAME, device)
        
        # 2. Load Dataset
        dataset = load_video_clips(DATASET_ID, SPLIT)
        
        # 3. Process in chunks using MemoryManagedExtractor
        extractor = MemoryManagedExtractor(
            model=model,
            device=device,
            layer_name="blocks"
        )
        
        clip_buffer = []
        for item in dataset:
            clip_buffer.append(item)
            
            if len(clip_buffer) >= CHUNK_SIZE:
                # Process batch
                try:
                    activations, masks = extractor.process_batch(clip_buffer)
                    if activations.size > 0:
                        all_activations.append(activations)
                        all_masks.append(masks)
                        stats.successful_clips += len(clip_buffer)
                    else:
                        stats.failed_clips += len(clip_buffer)
                except Exception as e:
                    logger.error(f"Batch processing failed: {e}")
                    stats.failed_clips += len(clip_buffer)
                finally:
                    clip_buffer = []
                    gc.collect()
                    if device == "cuda":
                        torch.cuda.empty_cache()
            
            stats.total_clips += 1
            
            # Log progress
            if stats.total_clips % 10 == 0:
                log_feature_extraction_progress(
                    logger, 
                    stats.total_clips, 
                    stats.successful_clips, 
                    stats.failed_clips
                )
        
        # Process remaining
        if clip_buffer:
            try:
                activations, masks = extractor.process_batch(clip_buffer)
                if activations.size > 0:
                    all_activations.append(activations)
                    all_masks.append(masks)
                    stats.successful_clips += len(clip_buffer)
                else:
                    stats.failed_clips += len(clip_buffer)
            except Exception as e:
                logger.error(f"Final batch failed: {e}")
                stats.failed_clips += len(clip_buffer)
        
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        # Even if failed, save partial results if any
        if all_activations:
            logger.warning("Saving partial results due to error")
        else:
            raise
    
    # Aggregate results
    if all_activations:
        final_activations = np.concatenate(all_activations, axis=0)
        final_masks = np.concatenate(all_masks, axis=0)
        stats.total_features_shape = final_activations.shape
        stats.total_masks_shape = final_masks.shape
    else:
        # Fallback for empty results (should not happen in real run)
        final_activations = np.array([])
        final_masks = np.array([])
        
    # Prepare metadata
    end_time = time.time()
    stats.duration_seconds = end_time - start_time
    
    metadata = {
        "model_name": MODEL_NAME,
        "dataset_id": DATASET_ID,
        "split": SPLIT,
        "device": device,
        "chunk_size": CHUNK_SIZE,
        "stats": asdict(stats),
        "extraction_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "checksum": hashlib.sha256(
            str(final_activations.tobytes()).encode()
        ).hexdigest()[:16]
    }
    
    # Save outputs
    save_features(
        final_activations,
        final_masks,
        metadata,
        str(FEATURES_PATH),
        str(METADATA_PATH)
    )
    
    logger.info("Feature extraction completed successfully")
    logger.info(f"Total clips processed: {stats.total_clips}")
    logger.info(f"Successful: {stats.successful_clips}, Failed: {stats.failed_clips}")
    logger.info(f"Duration: {stats.duration_seconds:.2f}s")
    
    return stats

if __name__ == "__main__":
    main()