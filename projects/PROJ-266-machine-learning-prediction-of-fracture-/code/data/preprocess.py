import os
import argparse
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import json
import pandas as pd
import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split

from code.utils.config import get_config_dict, get_split_seed
from code.utils.logger import get_logger

# Ensure project root is in path if run as script
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def setup_logging(log_file: Path) -> logging.Logger:
    """Configure logging for the preprocessing pipeline."""
    logger = get_logger("PREPROCESS")
    logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def load_image(image_path: Path) -> Image.Image:
    """Load an image from disk."""
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    return Image.open(image_path)

def convert_to_grayscale(img: Image.Image) -> Image.Image:
    """Convert image to grayscale."""
    return img.convert('L')

def resize_without_aspect_ratio_distortion(img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    """
    Resize image to target_size without distorting aspect ratio.
    If aspect ratio differs, pad with black pixels.
    Logs a warning if resizing occurs.
    """
    original_width, original_height = img.size
    target_width, target_height = target_size

    if (original_width, original_height) == target_size:
        return img

    logger = logging.getLogger("PREPROCESS")
    logger.warning(f"Resizing image from {original_width}x{original_height} to {target_width}x{target_height} (aspect ratio preserved, padded)")

    # Calculate aspect ratios
    img_ratio = original_width / original_height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        # Image is wider than target
        new_width = target_width
        new_height = int(target_width / img_ratio)
    else:
        # Image is taller than target
        new_height = target_height
        new_width = int(target_height * img_ratio)

    # Resize
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create new image with target size and paste resized image in center
    new_img = Image.new('L', (target_width, target_height), color=0)
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    new_img.paste(resized, (paste_x, paste_y))

    return new_img

def normalize_intensity(img: Image.Image) -> Image.Image:
    """Normalize intensity to [0, 255] range."""
    arr = np.array(img, dtype=np.float32)
    if arr.max() > arr.min():
        arr = (arr - arr.min()) / (arr.max() - arr.min()) * 255.0
    return Image.fromarray(arr.astype(np.uint8))

def process_single_image(image_path: Path, output_dir: Path, target_size: Tuple[int, int] = (128, 128)) -> Path:
    """Process a single image: grayscale, resize, normalize."""
    img = load_image(image_path)
    img = convert_to_grayscale(img)
    img = resize_without_aspect_ratio_distortion(img, target_size)
    img = normalize_intensity(img)
    
    output_path = output_dir / image_path.name
    img.save(output_path)
    return output_path

def run_preprocessing(input_dir: Path, output_dir: Path, target_size: Tuple[int, int] = (128, 128)) -> List[Dict[str, Any]]:
    """
    Run preprocessing on all images in input_dir.
    Returns list of processed image metadata.
    """
    logger = logging.getLogger("PREPROCESS")
    logger.info(f"Starting preprocessing on {input_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    processed_images = []
    image_files = list(input_dir.glob("*.png")) + list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.jpeg"))
    
    if not image_files:
        logger.warning(f"No images found in {input_dir}")
        return processed_images

    for img_path in image_files:
        try:
            output_path = process_single_image(img_path, output_dir, target_size)
            processed_images.append({
                "original_path": str(img_path),
                "processed_path": str(output_path),
                "filename": img_path.name
            })
            logger.info(f"Processed: {img_path.name}")
        except Exception as e:
            logger.error(f"Failed to process {img_path.name}: {e}")
    
    logger.info(f"Preprocessing complete. Processed {len(processed_images)} images.")
    return processed_images

def perform_stratified_split(metadata_path: Path, output_path: Path, config: Dict[str, Any]) -> None:
    """
    Perform stratified split of dataset into train, val, test sets.
    Uses alloy_family as stratification column.
    """
    logger = logging.getLogger("PREPROCESS")
    logger.info("Performing stratified split...")

    # Load metadata
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    df = pd.read_json(metadata_path)
    
    # Ensure required columns exist
    required_cols = ['image_path', 'alloy_family']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in metadata: {missing_cols}")

    # Validate alloy families
    valid_families = {'steel', 'Al', 'Ti'}
    actual_families = set(df['alloy_family'].unique())
    if not actual_families.issubset(valid_families):
        raise ValueError(f"Invalid alloy families found: {actual_families - valid_families}")

    # Check minimum samples per family
    family_counts = df['alloy_family'].value_counts()
    for family in valid_families:
        count = family_counts.get(family, 0)
        if count < 3:
            raise ValueError(f"Insufficient samples for alloy family '{family}': {count} (need at least 3 for stratified split)")

    # Get split seed from config
    split_seed = get_split_seed(config)
    logger.info(f"Using split seed: {split_seed}")

    # Stratified split: 70% train, 15% val, 15% test
    # First split: train (70%) vs temp (30%)
    train_df, temp_df = train_test_split(
        df, 
        test_size=0.3, 
        stratify=df['alloy_family'], 
        random_state=split_seed
    )

    # Second split: val (50% of temp) vs test (50% of temp)
    val_df, test_df = train_test_split(
        temp_df, 
        test_size=0.5, 
        stratify=temp_df['alloy_family'], 
        random_state=split_seed
    )

    # Add split labels
    train_df['split'] = 'train'
    val_df['split'] = 'val'
    test_df['split'] = 'test'

    # Concatenate
    split_df = pd.concat([train_df, val_df, test_df], ignore_index=True)

    # Validate that test set has at least one sample per alloy family
    test_families = set(test_df['alloy_family'].unique())
    if not test_families.issuperset(valid_families):
        missing = valid_families - test_families
        logger.error(f"Test set missing alloy families: {missing}")
        raise ValueError(f"ERROR: Test set missing alloy family: {missing}")

    # Save split metadata
    split_df.to_csv(output_path, index=False)
    logger.info(f"Stratified split saved to {output_path}")

    # Log distribution
    split_dist = split_df.groupby(['split', 'alloy_family']).size().unstack(fill_value=0)
    logger.info("Split distribution:")
    logger.info(split_dist.to_string())

def generate_split_metadata_csv(split_df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate a summary CSV of split metadata showing count per split and alloy family.
    Output format: ['split', 'alloy_family', 'count']
    """
    logger = logging.getLogger("PREPROCESS")
    
    summary = split_df.groupby(['split', 'alloy_family']).size().reset_index(name='count')
    summary = summary.sort_values(['split', 'alloy_family'])
    summary.to_csv(output_path, index=False)
    logger.info(f"Split metadata summary saved to {output_path}")

def main():
    """Main entry point for preprocessing pipeline."""
    parser = argparse.ArgumentParser(description="Preprocess microstructure images and split dataset")
    parser.add_argument("--input", type=str, default="data/raw", help="Input directory for raw images")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory for processed images")
    parser.add_argument("--metadata", type=str, default="data/raw/metadata.json", help="Path to metadata JSON")
    parser.add_argument("--config", type=str, default="code/utils/config.py", help="Path to config module")
    parser.add_argument("--target-size", type=int, nargs=2, default=[128, 128], help="Target image size (width height)")
    parser.add_argument("--log", type=str, default="logs/preprocess.log", help="Log file path")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    metadata_path = Path(args.metadata)
    log_path = Path(args.log)
    target_size = tuple(args.target_size)
    
    # Setup logging
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_path)
    logger.info("Starting preprocessing pipeline")
    
    # Load config
    config = get_config_dict()
    
    # Step 1: Preprocess images
    processed_images = run_preprocessing(input_dir, output_dir, target_size)
    
    if not processed_images:
        logger.error("No images were processed. Exiting.")
        return 1

    # Step 2: Update metadata with processed paths
    # Load original metadata
    if metadata_path.exists():
        df = pd.read_json(metadata_path)
    else:
        # Fallback: create from processed images if metadata missing
        logger.warning(f"Metadata not found at {metadata_path}, creating from processed images")
        df = pd.DataFrame(processed_images)
        df['alloy_family'] = 'unknown'  # Default, will fail split validation if not fixed

    # Map processed paths back to original filenames
    processed_map = {p['filename']: p['processed_path'] for p in processed_images}
    df['processed_path'] = df['image_path'].apply(lambda x: processed_map.get(Path(x).name, str(Path(output_dir) / Path(x).name)))
    
    # Step 3: Perform stratified split
    split_output_path = output_dir / "split_metadata.csv"
    try:
        perform_stratified_split(metadata_path, split_output_path, config)
    except ValueError as e:
        logger.error(str(e))
        return 1
    
    # Step 4: Generate summary CSV
    summary_output_path = output_dir / "split_distribution.csv"
    if split_output_path.exists():
        split_df = pd.read_csv(split_output_path)
        generate_split_metadata_csv(split_df, summary_output_path)
    
    logger.info("Preprocessing pipeline completed successfully")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
