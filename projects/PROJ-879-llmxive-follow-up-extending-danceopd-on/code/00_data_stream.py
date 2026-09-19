#!/usr/bin/env python
"""
Stream samples from raw data directories, extract prompt embeddings using CLIP,
and write combined samples to a Parquet file.

This script implements T012b: Stream & Process Data.
It reads from data/raw/, streams samples, and extracts prompt_embedding using the CLIP model.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd
import torch
from transformers import CLIPProcessor, CLIPModel
from itertools import islice
import logging
import json

from utils.config import get_config
from utils.models import get_clip_model, clear_model_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_prompt_embedding(processor, model, image_path: str) -> list:
    """
    Extract prompt embedding for a given image path using the CLIP model.
    
    Args:
        processor: CLIPProcessor instance
        model: CLIPModel instance
        image_path: Path to the image file
        
    Returns:
        List of float32 values representing the embedding, or None if failed.
    """
    try:
        # Load image using PIL via processor
        # CLIPProcessor expects a PIL Image or a path that PIL can open
        inputs = processor(images=image_path, return_tensors="pt")
        
        with torch.no_grad():
            # Get image features
            embeddings = model.get_image_features(inputs["pixel_values"])
        
        # Convert to list of floats
        return embeddings.squeeze().tolist()
    except Exception as e:
        logger.error(f"Failed to extract embedding for {image_path}: {e}")
        return None

def load_samples_from_parquet(parquet_path: Path, max_samples: int) -> pd.DataFrame:
    """
    Load samples from a parquet file, limiting to max_samples.
    
    Args:
        parquet_path: Path to the parquet file
        max_samples: Maximum number of samples to load
        
    Returns:
        DataFrame with sampled rows.
    """
    if not parquet_path.exists():
        logger.error(f"Parquet file not found: {parquet_path}")
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    # Read the parquet file
    df = pd.read_parquet(parquet_path)
    
    # Limit to max_samples
    if len(df) > max_samples:
        df = df.head(max_samples)
        
    return df

def run_data_streaming(config):
    """
    Main function to stream data, extract embeddings, and save to parquet.
    
    Args:
        config: Configuration object from utils.config
    """
    raw_data_dir = Path(config.get_path("RAW_DATA_DIR"))
    processed_dir = Path(config.get_path("PROCESSED_DATA_DIR"))
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Initialize CLIP model using the shared utility
    logger.info("Loading CLIP model...")
    try:
        processor, model = get_clip_model()
        model.eval()
    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")
        sys.exit(1)

    # Target sample size
    target_samples = config.get_hyperparameter("N_SAMPLES", 2500)
    samples_per_source = target_samples // 2

    combined_data = []

    # Load and stream ImageNet samples
    logger.info("Streaming ImageNet samples...")
    imagenet_path = raw_data_dir / "imagenet_samples.parquet"
    laion_path = raw_data_dir / "laion_samples.parquet"

    # Verify raw data exists (T012 should have done this, but we check again)
    if not imagenet_path.exists():
        logger.error(f"ImageNet samples file not found: {imagenet_path}")
        logger.error("Please ensure T012 (data fetch/verification) has completed successfully.")
        sys.exit(1)

    if not laion_path.exists():
        logger.error(f"LAION samples file not found: {laion_path}")
        logger.error("Please ensure T012 (data fetch/verification) has completed successfully.")
        sys.exit(1)

    # Load ImageNet samples
    try:
        df_imagenet = load_samples_from_parquet(imagenet_path, samples_per_source)
        logger.info(f"Loaded {len(df_imagenet)} ImageNet samples.")
    except Exception as e:
        logger.error(f"Failed to load ImageNet samples: {e}")
        sys.exit(1)

    # Process ImageNet samples
    processed_imagenet = 0
    for idx, row in df_imagenet.iterrows():
        image_path = row.get("image_path")
        if not image_path:
            logger.warning(f"Skipping row {idx}: missing image_path")
            continue
        
        if not Path(image_path).exists():
            logger.warning(f"Skipping row {idx}: image file not found at {image_path}")
            continue
            
        embedding = extract_prompt_embedding(processor, model, image_path)
        if embedding is not None:
            combined_data.append({
                "image_path": str(Path(image_path).absolute()),
                "noise_level": float(row.get("noise_level", 0.0)),
                "prompt_embedding": embedding
            })
            processed_imagenet += 1
            
        if len(combined_data) >= samples_per_source:
            break

    logger.info(f"Processed {processed_imagenet} ImageNet samples, collected {len(combined_data)} total.")

    # Load and stream LAION samples if we haven't reached target yet
    if len(combined_data) < target_samples:
        logger.info("Streaming LAION samples...")
        try:
            df_laion = load_samples_from_parquet(laion_path, samples_per_source)
            logger.info(f"Loaded {len(df_laion)} LAION samples.")
        except Exception as e:
            logger.error(f"Failed to load LAION samples: {e}")
            sys.exit(1)

        # Process LAION samples
        processed_laion = 0
        for idx, row in df_laion.iterrows():
            image_path = row.get("image_path")
            if not image_path:
                logger.warning(f"Skipping row {idx}: missing image_path")
                continue
            
            if not Path(image_path).exists():
                logger.warning(f"Skipping row {idx}: image file not found at {image_path}")
                continue
                
            embedding = extract_prompt_embedding(processor, model, image_path)
            if embedding is not None:
                combined_data.append({
                    "image_path": str(Path(image_path).absolute()),
                    "noise_level": float(row.get("noise_level", 0.0)),
                    "prompt_embedding": embedding
                })
                processed_laion += 1
                
            if len(combined_data) >= target_samples:
                break

        logger.info(f"Processed {processed_laion} LAION samples, collected {len(combined_data)} total.")

    # Validate minimum sample size
    if len(combined_data) < 1000:
        logger.error(f"Insufficient samples extracted: {len(combined_data)}. Required >= 1000.")
        logger.error("This fails the FR-001 minimum sample requirement.")
        sys.exit(1)

    # Create output DataFrame
    output_df = pd.DataFrame(combined_data)
    
    # Ensure correct types
    output_df['image_path'] = output_df['image_path'].astype(str)
    output_df['noise_level'] = output_df['noise_level'].astype(float)
    # prompt_embedding is already a list of floats from extract_prompt_embedding
    
    # Write to parquet
    output_path = processed_dir / "combined_samples.parquet"
    output_df.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully wrote {len(output_df)} samples to {output_path}")
    logger.info(f"Output schema: {output_df.dtypes.to_dict()}")
    
    # Log summary
    logger.info(f"Summary:")
    logger.info(f"  - Total samples: {len(output_df)}")
    logger.info(f"  - ImageNet samples: {sum(1 for p in output_df['image_path'] if 'imagenet' in p.lower())}")
    logger.info(f"  - LAION samples: {sum(1 for p in output_df['image_path'] if 'laion' in p.lower())}")

def main():
    """Main entry point."""
    config = get_config()
    run_data_streaming(config)

if __name__ == "__main__":
    main()