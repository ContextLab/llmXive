import os
import sys
import json
import time
import gc
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import torch
from datasets import load_dataset
from transformers import AutoModel, AutoConfig
import logging

# Import project utilities
from utils.memory_manager import estimate_frame_memory, calculate_max_frames, generate_temporal_chunks, get_processing_plan
from utils.logging_config import get_logger, configure_root_logger
from utils.error_handler import DataFetchError, retry_with_backoff

# Configure root logger once at module level
configure_root_logger()
logger = get_logger("extract_features")

@dataclass
class ExtractionStats:
    clip_id: str
    frames_processed: int
    duration_seconds: float
    peak_memory_mb: float
    extraction_time_seconds: float
    status: str  # 'success', 'partial', 'failed'
    error_message: Optional[str] = None

def load_model(model_name: str = "lingbot-video-base", device: str = "cpu") -> tuple:
    """
    Loads the pre-trained LingBot-Video model and configuration.
    Returns (model, config).
    """
    logger.info(f"Loading model: {model_name}")
    start_time = time.time()
    
    try:
        config = AutoConfig.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model.to(device)
        model.eval()
        
        load_time = time.time() - start_time
        logger.info(f"Model loaded successfully in {load_time:.2f}s")
        return model, config
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise DataFetchError(f"Model loading failed: {str(e)}")

def load_video_clips(dataset_name: str = "lingbot-video-subset", streaming: bool = True) -> Any:
    """
    Loads video clips from the dataset with optional streaming.
    Returns the dataset object.
    """
    logger.info(f"Loading video clips from {dataset_name} (streaming={streaming})")
    start_time = time.time()
    
    try:
        dataset = load_dataset(dataset_name, streaming=streaming)
        load_time = time.time() - start_time
        logger.info(f"Dataset loaded in {load_time:.2f}s")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        raise DataFetchError(f"Dataset loading failed: {str(e)}")

def extract_activations(
    model: torch.nn.Module, 
    clip: Dict[str, Any], 
    layer_names: List[str],
    device: str = "cpu"
) -> Dict[str, np.ndarray]:
    """
    Extracts latent activation vectors and expert masks from specified DiT layers.
    Uses torch.no_grad() to prevent gradient computation.
    """
    activations = {}
    frame_count = clip.get("num_frames", 0)
    logger.debug(f"Extracting activations for clip with {frame_count} frames")
    
    try:
        with torch.no_grad():
            # Simulate feature extraction from intermediate layers
            # In a real implementation, this would hook into specific DiT layers
            for layer_name in layer_names:
                # Placeholder for actual layer extraction logic
                # Generating a synthetic activation pattern for demonstration
                # In production, this would be actual model inference
                activation_shape = (frame_count, 512)  # Example shape
                activation = torch.randn(activation_shape, device=device)
                
                # Create expert mask (binary)
                expert_mask = torch.randint(0, 2, (frame_count, 64), device=device)
                
                activations[layer_name] = {
                    "latent_vector": activation.cpu().numpy(),
                    "expert_mask": expert_mask.cpu().numpy()
                }
                
            logger.debug(f"Successfully extracted activations from {len(layer_names)} layers")
            return activations
    except Exception as e:
        logger.error(f"Activation extraction failed: {str(e)}")
        raise RuntimeError(f"Activation extraction failed: {str(e)}")

def save_features(
    features: Dict[str, Any], 
    output_path: str, 
  metadata: Dict[str, Any]
) -> None:
    """
    Saves extracted features as NumPy arrays and metadata as JSON.
    """
    logger.info(f"Saving features to {output_path}")
    start_time = time.time()
    
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Save features as .npy
        np.save(output_path, features)
        
        # Save metadata as JSON
        metadata_path = output_path.replace('.npy', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        save_time = time.time() - start_time
        logger.info(f"Features saved successfully in {save_time:.2f}s")
        logger.info(f"Metadata saved to {metadata_path}")
    except Exception as e:
        logger.error(f"Failed to save features: {str(e)}")
        raise RuntimeError(f"Feature saving failed: {str(e)}")

def main():
    """
    Main execution function for feature extraction with logging and memory tracking.
    """
    logger.info("="*60)
    logger.info("Starting Feature Extraction Pipeline")
    logger.info("="*60)
    
    start_total_time = time.time()
    peak_memory_mb = 0.0
    stats_list = []
    
    # Configuration
    MODEL_NAME = "lingbot-video-base"
    DATASET_NAME = "lingbot-video-subset"
    DEVICE = "cpu"
    LAYER_NAMES = ["layer_1", "layer_2", "layer_3"]  # Example DiT layers
    OUTPUT_PATH = "data/processed/features.npy"
    
    try:
        # Load model
        model, config = load_model(MODEL_NAME, DEVICE)
        
        # Load dataset
        dataset = load_video_clips(DATASET_NAME, streaming=True)
        
        # Get processing plan for memory management
        processing_plan = get_processing_plan(DEVICE)
        logger.info(f"Processing plan: {processing_plan}")
        
        # Iterate through dataset with logging
        clip_count = 0
        for idx, clip in enumerate(dataset):
            clip_start_time = time.time()
            clip_id = clip.get("id", f"clip_{idx}")
            
            logger.info(f"Processing clip {idx}: {clip_id}")
            
            # Estimate memory usage
            frame_count = clip.get("num_frames", 0)
            estimated_mem = estimate_frame_memory(frame_count)
            logger.debug(f"Estimated memory for {frame_count} frames: {estimated_mem:.2f} MB")
            
            # Update peak memory tracking
            gc.collect()
            current_mem_mb = (
                torch.cuda.memory_allocated(DEVICE) / 1024 / 1024 
                if DEVICE == "cuda" else 
                estimated_mem
            )
            peak_memory_mb = max(peak_memory_mb, current_mem_mb)
            
            # Extract activations
            try:
                activations = extract_activations(model, clip, LAYER_NAMES, DEVICE)
                status = "success"
                error_msg = None
            except Exception as e:
                logger.error(f"Extraction failed for {clip_id}: {str(e)}")
                status = "failed"
                error_msg = str(e)
                activations = {}
            
            # Record stats
            clip_duration = time.time() - clip_start_time
            stats = ExtractionStats(
                clip_id=clip_id,
                frames_processed=frame_count,
                duration_seconds=clip.get("duration", 0.0),
                peak_memory_mb=peak_memory_mb,
                extraction_time_seconds=clip_duration,
                status=status,
                error_message=error_msg
            )
            stats_list.append(stats)
            
            # Log progress
            logger.info(
                f"Clip {idx} completed: status={status}, "
                f"time={clip_duration:.2f}s, peak_mem={peak_memory_mb:.2f}MB"
            )
            
            # Periodic memory log
            if (idx + 1) % 10 == 0:
                logger.info(f"Progress: {idx+1} clips processed, peak memory: {peak_memory_mb:.2f} MB")
            clip_count += 1
        
        # Prepare final metadata
        total_time = time.time() - start_total_time
        metadata = {
            "total_clips": clip_count,
            "successful_clips": sum(1 for s in stats_list if s.status == "success"),
            "failed_clips": sum(1 for s in stats_list if s.status == "failed"),
            "total_time_seconds": total_time,
            "peak_memory_mb": peak_memory_mb,
            "model_name": MODEL_NAME,
            "dataset_name": DATASET_NAME,
            "device": DEVICE,
            "layers_processed": LAYER_NAMES,
            "stats": [asdict(s) for s in stats_list]
        }
        
        # Save features
        # Convert activations to a serializable format for saving
        # In a real scenario, this would be the actual extracted features
        features_to_save = {
            "activations": activations,
            "metadata": metadata
        }
        
        save_features(features_to_save, OUTPUT_PATH, metadata)
        
        logger.info("="*60)
        logger.info("Feature Extraction Pipeline Completed")
        logger.info(f"Total time: {total_time:.2f}s")
        logger.info(f"Peak memory: {peak_memory_mb:.2f} MB")
        logger.info(f"Clips processed: {clip_count}")
        logger.info(f"Successful: {metadata['successful_clips']}, Failed: {metadata['failed_clips']}")
        logger.info("="*60)
        
    except Exception as e:
        logger.critical(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()