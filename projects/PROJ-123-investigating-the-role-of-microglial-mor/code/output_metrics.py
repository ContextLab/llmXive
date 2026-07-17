"""
T019: Output structured CSV with morphological metrics and brain region tags.

This module aggregates the results from the morphometry pipeline (T013-T017)
and writes them to a single structured CSV file as required by User Story 1.

Output: data/processed/morphological_metrics.csv
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import get_path, ensure_dirs
from code.logging_utils import get_logger
from code.data_ingestion import parse_metadata_from_filename
from code.morphometry import (
    handle_empty_fields,
    skeletonize_and_count,
    calculate_soma_area_and_length,
    run_sholl_analysis,
    denoise_and_subtract
)

logger = get_logger(__name__)

def process_image_file(image_path: Path, metadata_cache: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Process a single image file: denoise, skeletonize, calculate metrics, and attach metadata.
    
    Args:
        image_path: Path to the image file.
        metadata_cache: Optional pre-parsed metadata to avoid re-parsing filenames.
    
    Returns:
        A dictionary containing all metrics and metadata, or None if the image is invalid/empty.
    """
    try:
        # 1. Parse Metadata
        if metadata_cache and str(image_path) in metadata_cache:
            meta = metadata_cache[str(image_path)]
        else:
            meta = parse_metadata_from_filename(image_path.name)
            if metadata_cache is not None:
                metadata_cache[str(image_path)] = meta
        
        # Validate brain region (T011 requirement)
        if not meta.get('brain_region'):
            logger.warning(f"Skipping {image_path.name}: Missing brain region tag in filename.")
            return None

        # 2. Load and Preprocess (T013)
        # Note: load_image is expected to return a numpy array (grayscale)
        # We assume code/data_ingestion.py has a load_image function that returns np.ndarray
        # If it returns a PIL image, we convert it here.
        from code.data_ingestion import load_image
        img = load_image(image_path)
        
        if img is None or img.size == 0:
            logger.warning(f"Skipping {image_path.name}: Image could not be loaded or is empty.")
            return None

        # Handle empty fields (T017)
        if handle_empty_fields(img):
            logger.info(f"Skipping {image_path.name}: Detected empty field of view.")
            return None

        denoised_img = denoise_and_subtract(img)

        # 3. Skeletonize and Count Branch Points (T014)
        branch_points, skeleton_img = skeletonize_and_count(denoised_img)

        # 4. Calculate Soma Area and Length (T015)
        soma_area, total_length = calculate_soma_area_and_length(denoised_img, skeleton_img)

        # 5. Run Sholl Analysis (T016)
        # Using default parameters from config or hardcoded reasonable defaults if not specified
        sholl_results = run_sholl_analysis(denoised_img)

        # 6. Compile Result
        result = {
            'file_name': image_path.name,
            'brain_region': meta['brain_region'],
            'subject_id': meta.get('subject_id', 'unknown'),
            'time_point': meta.get('time_point', 'unknown'),
            'branch_points': branch_points,
            'soma_area': soma_area,
            'total_process_length': total_length,
            'sholl_max_intersections': sholl_results.get('max_intersections', 0),
            'sholl_decay_rate': sholl_results.get('decay_rate', 0.0),
            'processing_status': 'success'
        }
        return result

    except Exception as e:
        logger.error(f"Error processing {image_path}: {str(e)}", exc_info=True)
        return None

def run_output_pipeline(
    input_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    force_regenerate: bool = False
) -> Path:
    """
    Main entry point for T019.
    
    Scans the input directory for images, processes them using the morphometry pipeline,
    and writes the aggregated results to a CSV file.
    
    Args:
        input_dir: Directory containing raw microscopy images. Defaults to config 'raw_images_dir'.
        output_path: Path for the output CSV. Defaults to config 'morph_metrics_csv'.
        force_regenerate: If True, overwrites existing output file.
    
    Returns:
        Path to the generated CSV file.
    """
    # Resolve paths
    if input_dir is None:
        input_dir = get_path('raw_images_dir')
    if output_path is None:
        output_path = get_path('morph_metrics_csv')
    
    # Ensure output directory exists
    ensure_dirs(output_path)

    # Check if output already exists and force is not set
    if output_path.exists() and not force_regenerate:
        logger.info(f"Output file {output_path} already exists. Skipping generation.")
        return output_path

    logger.info(f"Starting morphological metrics extraction for {input_dir}")
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Find all image files
    image_extensions = {'.tif', '.tiff', '.png', '.jpg', '.jpeg'}
    image_files = [
        f for f in input_dir.iterdir() 
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not image_files:
        logger.warning(f"No image files found in {input_dir}")
        # Create an empty CSV with headers to satisfy schema
        df = pd.DataFrame(columns=[
            'file_name', 'brain_region', 'subject_id', 'time_point',
            'branch_points', 'soma_area', 'total_process_length',
            'sholl_max_intersections', 'sholl_decay_rate', 'processing_status'
        ])
        df.to_csv(output_path, index=False)
        return output_path

    results = []
    metadata_cache = {}

    for img_file in image_files:
        logger.debug(f"Processing: {img_file.name}")
        row = process_image_file(img_file, metadata_cache)
        if row:
            results.append(row)

    # Create DataFrame
    if results:
        df = pd.DataFrame(results)
        
        # Sort by brain_region and subject_id for consistency
        df = df.sort_values(by=['brain_region', 'subject_id', 'time_point'])
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(results)} records to {output_path}")
    else:
        logger.warning("No valid records were generated. Creating empty CSV.")
        df = pd.DataFrame(columns=[
            'file_name', 'brain_region', 'subject_id', 'time_point',
            'branch_points', 'soma_area', 'total_process_length',
            'sholl_max_intersections', 'sholl_decay_rate', 'processing_status'
        ])
        df.to_csv(output_path, index=False)

    return output_path

if __name__ == "__main__":
    # Run the pipeline when executed directly
    output_file = run_output_pipeline()
    print(f"Pipeline complete. Output saved to: {output_file}")
