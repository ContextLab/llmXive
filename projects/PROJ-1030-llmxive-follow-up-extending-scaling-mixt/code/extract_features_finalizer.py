"""
T016 Implementation: Save extracted features as data/processed/features.npy with metadata JSON.

This script finalizes the feature extraction process by:
1. Loading the raw extraction results (if any intermediate format exists) or re-running extraction via the existing pipeline
2. Consolidating latent vectors and expert masks into a single NumPy archive
3. Generating a comprehensive metadata JSON file describing the dataset
4. Writing checksums for verification

Note: This task assumes T013 (extraction logic) and T015 (retry logic) are functional.
It orchestrates the final save step.
"""
import os
import sys
import json
import hashlib
import time
import logging
import argparse
from pathlib import Path
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from extract_features import ExtractionResult, save_features, load_model, load_video_clips, extract_activations
from utils.logging_config import get_logger, fail_loudly
from utils.retry import retry_with_backoff
from utils.memory_manager import get_processing_plan

logger = get_logger("extract_features_finalizer")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_metadata_json(output_dir: Path, features_path: Path, config: dict) -> Path:
    """
    Save comprehensive metadata for the extracted features.
    
    Args:
        output_dir: Directory where metadata will be saved
        features_path: Path to the generated features.npy file
        config: Configuration used for extraction
        
    Returns:
        Path to the metadata file
    """
    metadata = {
        "created_at": datetime.utcnow().isoformat(),
        "artifact_type": "feature_extraction_batch",
        "feature_file": features_path.name,
        "feature_file_sha256": calculate_sha256(features_path),
        "feature_file_size_bytes": features_path.stat().st_size,
        "extraction_config": config,
        "version": "1.0.0",
        "pipeline_task_id": "T016",
        "dependencies": {
            "model_weights": "data/external/lingbot_weights/",
            "video_manifest": "data/raw/sample_list.csv"
        }
    }
    
    metadata_path = output_dir / "features_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved metadata to {metadata_path}")
    return metadata_path

def consolidate_and_save_features(
    features_data: dict, 
    output_path: Path
) -> dict:
    """
    Consolidate extracted features into a single NumPy archive.
    
    Expected features_data structure:
    {
        "latent_vectors": np.ndarray,  # shape: (N, D_latent)
        "expert_masks": np.ndarray,    # shape: (N, D_experts)
        "clip_ids": list,              # list of clip identifiers
        "chunk_indices": list          # list of chunk indices for temporal tracking
    }
    
    Args:
        features_data: Dictionary containing extracted arrays
        output_path: Path to save the .npy file
        
    Returns:
        Dictionary with saving statistics
    """
    if not features_data:
        fail_loudly("No features data to save. Extraction may have failed or returned empty results.")
    
    # Validate dimensions
    if "latent_vectors" not in features_data:
        fail_loudly("Missing 'latent_vectors' in features data.")
    if "expert_masks" not in features_data:
        fail_loudly("Missing 'expert_masks' in features data.")
    
    latent = features_data["latent_vectors"]
    masks = features_data["expert_masks"]
    
    if latent.shape[0] != masks.shape[0]:
        fail_loudly(f"Dimension mismatch: latent_vectors shape {latent.shape} vs expert_masks shape {masks.shape}")
    
    logger.info(f"Consolidating features: {latent.shape[0]} samples, latent dim {latent.shape[1]}, expert dim {masks.shape[1]}")
    
    # Create a structured array or dictionary for saving
    # We save a dictionary of arrays to preserve named access
    save_dict = {
        "latent_vectors": latent,
        "expert_masks": masks,
        "clip_ids": features_data.get("clip_ids", []),
        "chunk_indices": features_data.get("chunk_indices", []),
        "extraction_timestamp": datetime.utcnow().isoformat()
    }
    
    np.save(output_path, save_dict)
    
    stats = {
        "num_samples": latent.shape[0],
        "latent_dim": latent.shape[1],
        "expert_dim": masks.shape[1],
        "file_size_bytes": output_path.stat().st_size,
        "sha256": calculate_sha256(output_path)
    }
    
    logger.info(f"Saved features to {output_path} ({stats['file_size_bytes']} bytes)")
    return stats

def main():
    parser = argparse.ArgumentParser(description="T016: Finalize and save extracted features with metadata")
    parser.add_argument("--config", type=str, default="data/processed/chunking_config.json",
                        help="Path to chunking/extraction config")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                        help="Directory to save outputs")
    parser.add_argument("--manifest", type=str, default="data/external/manifest.json",
                        help="Path to video manifest")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting T016 feature finalization. Output dir: {output_dir}")
    
    # Load config
    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path, "r") as f:
            extraction_config = json.load(f)
    else:
        logger.warning(f"Config not found at {config_path}, using defaults")
        extraction_config = {
            "subsample_rate": 2,
            "chunk_size": 32,
            "model_name": "lingbot-video-base",
            "layers": ["layer_10", "layer_20"]
        }
    
    # Attempt to load existing extracted data if re-running finalization
    # If T013 produced an intermediate file, load it. Otherwise, we assume 
    # the extraction pipeline needs to be run or we are aggregating.
    # For this task, we assume the extraction logic from T013/T014.2 
    # has been run and we are finalizing the save.
    # If no intermediate data exists, we trigger a minimal extraction run 
    # to ensure we have real data (as per "Fail Loudly" constraint).
    
    features_data = None
    
    # Check for intermediate extraction results
    intermediate_path = output_dir / "temp_features.npz"
    if intermediate_path.exists():
        logger.info(f"Loading intermediate features from {intermediate_path}")
        loaded = np.load(intermediate_path, allow_pickle=True)
        features_data = {
            "latent_vectors": loaded["latent_vectors"],
            "expert_masks": loaded["expert_masks"],
            "clip_ids": loaded["clip_ids"].tolist() if "clip_ids" in loaded else [],
            "chunk_indices": loaded["chunk_indices"].tolist() if "chunk_indices" in loaded else []
        }
    else:
        logger.info("No intermediate features found. Running extraction pipeline to generate real data.")
        # Run extraction via the main pipeline logic
        # We call the extraction functions directly to ensure we have real data
        try:
            model = load_model()
            clips = load_video_clips(args.manifest)
            
            if not clips:
                fail_loudly("No video clips found in manifest. Cannot extract features.")
            
            all_latents = []
            all_masks = []
            all_ids = []
            all_chunks = []
            
            for i, clip in enumerate(clips):
                logger.info(f"Processing clip {i+1}/{len(clips)}: {clip.id}")
                frames = clip.frames
                if not frames:
                    continue
                
                # Extract activations
                result = extract_activations(model, frames, clip.id)
                if result:
                    all_latents.append(result["latent_vector"])
                    all_masks.append(result["expert_mask"])
                    all_ids.append(clip.id)
                    all_chunks.append(i)
                
                # Memory management
                if (i + 1) % 10 == 0:
                    gc.collect()
            
            if not all_latents:
                fail_loudly("Extraction produced no valid features. Check model and data integrity.")
            
            features_data = {
                "latent_vectors": np.vstack(all_latents),
                "expert_masks": np.vstack(all_masks),
                "clip_ids": all_ids,
                "chunk_indices": all_chunks
            }
            
        except Exception as e:
            fail_loudly(f"Extraction pipeline failed: {str(e)}")
    
    # Save consolidated features
    features_output_path = output_dir / "features.npy"
    save_stats = consolidate_and_save_features(features_data, features_output_path)
    
    # Save metadata
    config_for_metadata = {
        **extraction_config,
        "samples_processed": save_stats["num_samples"],
        "final_dimensions": {
            "latent": save_stats["latent_dim"],
            "experts": save_stats["expert_dim"]
        }
    }
    save_metadata_json(output_dir, features_output_path, config_for_metadata)
    
    logger.info("T016 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
