"""
Data preparation module for the Visual Salience project.
Handles dataset ingestion, filtering, salience manipulation, and validation.
Implements strict 'Fail Loudly' behavior for data fetching.
"""

import os
import sys
import hashlib
import json
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
import random

# Import from project modules
from config import seed_everything
from env_config import get_config, EnvConfig
from logging_config import setup_logging, get_logger
from models import Scenario, StimulusVariant, AmbiguityLabel, SalienceLevel

# Configure logging
logger = get_logger(__name__)

# Custom Exceptions
class DataFetchError(Exception):
    """Raised when real data fetch fails and no valid fallback is configured."""
    pass

class DataIngestionError(Exception):
    """Raised when data ingestion or processing fails."""
    pass

class SemanticChangeError(Exception):
    """Raised when semantic preservation verification fails."""
    pass

class ManipulationFailureError(Exception):
    """Raised when salience manipulation fails."""
    pass

@dataclass
class DatasetSource:
    """Represents a potential data source."""
    name: str
    url: str
    is_verified: bool = False

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _verify_verified_source(source: str) -> Optional[DatasetSource]:
    """
    Check if a verified source is configured via environment variable.
    If present, return the source details; otherwise, return None.
    """
    if not source:
        return None
    
    # Expected format: package_name::recipe_name or direct_url
    if "::" in source:
        parts = source.split("::")
        return DatasetSource(
            name=parts[0],
            url=parts[1] if len(parts) > 1 else parts[0],
            is_verified=True
        )
    else:
        # Assume it's a direct URL or package name
        return DatasetSource(name=source, url=source, is_verified=True)

def _fetch_from_verified_source(source: DatasetSource, output_dir: Path) -> Path:
    """
    Fetch data from a verified source.
    Currently supports Hugging Face datasets and direct URLs.
    """
    if not source.is_verified:
        raise DataFetchError(f"Source {source.name} is not verified.")
    
    # Check if it's a Hugging Face dataset
    if source.name in ["visual_genome", "morald"]:
        try:
            from datasets import load_dataset
            logger.info(f"Loading dataset from Hugging Face: {source.name}")
            dataset = load_dataset(source.name, split="train", streaming=False)
            
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the dataset to a local file (parquet format)
            output_file = output_dir / f"{source.name}_subset.parquet"
            dataset.to_parquet(str(output_file))
            
            logger.info(f"Dataset saved to {output_file}")
            return output_file
        except Exception as e:
            raise DataFetchError(f"Failed to load dataset from Hugging Face: {str(e)}")
    
    # Check if it's a direct URL
    elif source.url.startswith(("http://", "https://")):
        try:
            response = requests.get(source.url, stream=True)
            response.raise_for_status()
            
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the file
            output_file = output_dir / Path(source.url).name
            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"File downloaded to {output_file}")
            return output_file
        except requests.RequestException as e:
            raise DataFetchError(f"Failed to download file from URL: {str(e)}")
    
    else:
        raise DataFetchError(f"Unsupported source type: {source.name}")

def ingest_dataset(
    output_dir: Optional[Path] = None,
    force_verify: bool = False
) -> Tuple[Path, Dict[str, Any]]:
    """
    Ingest dataset from a real source with strict 'Fail Loudly' behavior.
    
    Args:
        output_dir: Directory to save the dataset. Defaults to data/raw/
        force_verify: If True, force verification of the dataset even if already downloaded.
    
    Returns:
        Tuple of (path_to_dataset, metadata_dict)
    
    Raises:
        DataFetchError: If the real data fetch fails and no valid fallback is configured.
    """
    seed_everything(42)
    
    if output_dir is None:
        output_dir = Path("data/raw")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get configuration
    config = get_config()
    
    # Check for verified source first
    verified_source_str = os.getenv("VERIFIED_DATA_SOURCE", "")
    verified_source = _verify_verified_source(verified_source_str)
    
    if verified_source:
        logger.info(f"Using verified source: {verified_source.name}")
        dataset_path = _fetch_from_verified_source(verified_source, output_dir)
        metadata = {
            "source": verified_source.name,
            "source_type": "verified",
            "checksum": _calculate_sha256(dataset_path),
            "timestamp": str(pd.Timestamp.now())
        }
    else:
        # Try primary source (MoralD)
        primary_source = DatasetSource(
            name="morald",
            url="https://huggingface.co/datasets/morald",
            is_verified=False
        )
        
        # Try secondary source (Visual Genome)
        secondary_source = DatasetSource(
            name="visual_genome",
            url="https://huggingface.co/datasets/visual_genome",
            is_verified=False
        )
        
        dataset_path = None
        metadata = {}
        
        # Try primary source
        try:
            logger.info(f"Attempting to fetch from primary source: {primary_source.name}")
            dataset_path = _fetch_from_verified_source(primary_source, output_dir)
            metadata = {
                "source": primary_source.name,
                "source_type": "primary",
                "checksum": _calculate_sha256(dataset_path),
                "timestamp": str(pd.Timestamp.now())
            }
        except DataFetchError as e:
            logger.warning(f"Primary source failed: {str(e)}")
            
            # Try secondary source
            try:
                logger.info(f"Attempting to fetch from secondary source: {secondary_source.name}")
                dataset_path = _fetch_from_verified_source(secondary_source, output_dir)
                metadata = {
                    "source": secondary_source.name,
                    "source_type": "secondary",
                    "checksum": _calculate_sha256(dataset_path),
                    "timestamp": str(pd.Timestamp.now())
                }
            except DataFetchError as e2:
                logger.error(f"Secondary source also failed: {str(e2)}")
                
                # Check if synthetic fallback is explicitly configured
                synthetic_fallback_enabled = os.getenv("ALLOW_SYNTHETIC_FALLBACK", "").lower() == "true"
                
                if synthetic_fallback_enabled:
                    logger.info("Synthetic fallback is explicitly enabled. Generating synthetic data.")
                    # Import synthetic generation function if available
                    try:
                        from code.synthetic_data import generate_synthetic_dataset
                        synthetic_path = output_dir / "synthetic_dataset.parquet"
                        generate_synthetic_dataset(synthetic_path, seed=42)
                        dataset_path = synthetic_path
                        metadata = {
                            "source": "synthetic",
                            "source_type": "fallback",
                            "checksum": _calculate_sha256(synthetic_path),
                            "timestamp": str(pd.Timestamp.now()),
                            "note": "Synthetic fallback used as explicitly configured"
                        }
                    except ImportError:
                        raise DataFetchError("Synthetic fallback requested but not available.")
                else:
                    # Strict fail loudly - no fallback
                    raise DataFetchError(
                        "Failed to fetch real data from all sources and synthetic fallback is not explicitly configured. "
                        "Set ALLOW_SYNTHETIC_FALLBACK=true to enable synthetic data generation."
                    )
    
    # Save metadata
    metadata_path = output_dir / "dataset_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Dataset ingested successfully. Metadata saved to {metadata_path}")
    return dataset_path, metadata

def filter_candidates(
    dataset_path: Path,
    output_path: Path,
    tags: Optional[List[str]] = None
) -> Path:
    """
    Filter dataset candidates based on metadata tags.
    
    Args:
        dataset_path: Path to the ingested dataset.
        output_path: Path to save filtered candidates.
        tags: List of tags to filter by (e.g., 'social', 'conflict').
    
    Returns:
        Path to the filtered candidates file.
    """
    seed_everything(42)
    
    if tags is None:
        tags = ["social", "conflict"]
    
    logger.info(f"Filtering candidates with tags: {tags}")
    
    # Load dataset
    try:
        import pandas as pd
        df = pd.read_parquet(dataset_path)
    except Exception as e:
        raise DataIngestionError(f"Failed to load dataset: {str(e)}")
    
    # Filter by tags
    # Assuming there's a 'tags' column in the dataset
    if "tags" not in df.columns:
        raise DataIngestionError("Dataset does not contain a 'tags' column.")
    
    # Convert tags column to list if it's a string
    df["tags"] = df["tags"].apply(lambda x: x.split(",") if isinstance(x, str) else x)
    
    # Filter rows that contain any of the specified tags
    mask = df["tags"].apply(lambda x: any(tag in x for tag in tags))
    filtered_df = df[mask]
    
    # Save filtered candidates
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered {len(filtered_df)} candidates. Saved to {output_path}")
    
    return output_path

def manipulate_salience(
    image_path: Path,
    salience_level: SalienceLevel,
    output_path: Path,
    target_region: Optional[Tuple[int, int, int, int]] = None
) -> Path:
    """
    Manipulate salience of an image by adjusting luminance in a target region.
    
    Args:
        image_path: Path to the original image.
        salience_level: Level of salience to apply (low, medium, high).
        output_path: Path to save the manipulated image.
        target_region: Optional bounding box (x, y, width, height) for the target region.
    
    Returns:
        Path to the manipulated image.
    """
    seed_everything(42)
    
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        raise DataIngestionError("PIL and numpy are required for image manipulation.")
    
    logger.info(f"Manipulating salience to {salience_level} for {image_path}")
    
    # Load image
    try:
        img = Image.open(image_path).convert("RGB")
        img_array = np.array(img)
    except Exception as e:
        raise ManipulationFailureError(f"Failed to load image: {str(e)}")
    
    # Determine luminance adjustment factor
    if salience_level == SalienceLevel.LOW:
        factor = 0.7
    elif salience_level == SalienceLevel.MEDIUM:
        factor = 0.85
    elif salience_level == SalienceLevel.HIGH:
        factor = 1.15
    else:
        raise ValueError(f"Invalid salience level: {salience_level}")
    
    # Apply adjustment to target region or whole image
    if target_region:
        x, y, w, h = target_region
        # Ensure region is within image bounds
        x = max(0, min(x, img_array.shape[1]))
        y = max(0, min(y, img_array.shape[0]))
        w = max(1, min(w, img_array.shape[1] - x))
        h = max(1, min(h, img_array.shape[0] - y))
        
        # Apply luminance adjustment to target region
        img_array[y:y+h, x:x+w] = np.clip(
            img_array[y:y+h, x:x+w] * factor, 0, 255
        ).astype(np.uint8)
    else:
        # Apply to whole image
        img_array = np.clip(img_array * factor, 0, 255).astype(np.uint8)
    
    # Save manipulated image
    manipulated_img = Image.fromarray(img_array)
    manipulated_img.save(output_path)
    logger.info(f"Salience manipulation complete. Saved to {output_path}")
    
    return output_path

def process_salience_manipulation(
    scenarios: List[Scenario],
    output_dir: Path,
    config: Optional[Dict[str, Any]] = None
) -> List[StimulusVariant]:
    """
    Process salience manipulation for a list of scenarios.
    
    Args:
        scenarios: List of Scenario objects to process.
        output_dir: Directory to save manipulated images.
        config: Optional configuration dictionary.
    
    Returns:
        List of StimulusVariant objects.
    """
    seed_everything(42)
    
    if config is None:
        config = {}
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    salience_levels = [SalienceLevel.LOW, SalienceLevel.MEDIUM, SalienceLevel.HIGH]
    variants = []
    
    for scenario in scenarios:
        for salience_level in salience_levels:
            # Generate output path
            output_filename = f"{scenario.id}_{salience_level.value}.png"
            output_path = output_dir / output_filename
            
            # Get target region from config or use default (center 50% of image)
            target_region = config.get("target_region")
            if target_region is None:
                # Default: center 50% of image
                # This would need actual image dimensions, so we'll skip for now
                target_region = None
            
            # Perform manipulation
            try:
                manipulate_salience(
                    Path(scenario.image_path),
                    salience_level,
                    output_path,
                    target_region
                )
                
                # Create StimulusVariant
                variant = StimulusVariant(
                    id=f"{scenario.id}_{salience_level.value}",
                    scenario_id=scenario.id,
                    salience_level=salience_level,
                    image_path=str(output_path)
                )
                variants.append(variant)
            except Exception as e:
                logger.error(f"Failed to manipulate {scenario.id} for {salience_level}: {str(e)}")
                # Log failure but continue with other scenarios
                continue
    
    logger.info(f"Processed {len(variants)} stimulus variants.")
    return variants

def main():
    """Main entry point for data preparation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Preparation for Visual Salience Project")
    parser.add_argument("--ingest", action="store_true", help="Ingest dataset")
    parser.add_argument("--filter", action="store_true", help="Filter candidates")
    parser.add_argument("--manipulate", action="store_true", help="Manipulate salience")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory")
    parser.add_argument("--dataset-path", type=str, help="Path to dataset")
    parser.add_argument("--config", type=str, help="Path to config file")
    
    args = parser.parse_args()
    
    setup_logging()
    
    if args.ingest:
        output_dir = Path(args.output_dir)
        dataset_path, metadata = ingest_dataset(output_dir)
        logger.info(f"Ingested dataset: {dataset_path}")
        logger.info(f"Metadata: {metadata}")
    
    if args.filter:
        if not args.dataset_path:
            logger.error("--dataset-path is required for filtering")
            sys.exit(1)
        
        output_path = Path(args.output_dir) / "filtered_candidates.csv"
        filter_candidates(Path(args.dataset_path), output_path)
        logger.info(f"Filtered candidates saved to {output_path}")
    
    if args.manipulate:
        # This would need a list of scenarios, which is not provided here
        logger.warning("Salience manipulation requires a list of scenarios. Skipping.")
    
    logger.info("Data preparation complete.")

if __name__ == "__main__":
    main()