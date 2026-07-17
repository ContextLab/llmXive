"""
Output Metrics Module for T019.
Aggregates morphological metrics from processed images and writes the final CSV.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import get_path, ensure_dirs
from code.morphometry import (
    handle_empty_fields,
    denoise_and_subtract,
    skeletonize_and_count,
    calculate_soma_area_and_length,
    run_sholl_analysis,
    process_microglia_image
)
from code.data_ingestion import ingest_directory, validate_brain_region
from code.logging_utils import get_logger, warn_missing_metadata

logger = get_logger(__name__)

def process_image_file(
    image_path: Path,
    metadata: Dict[str, Any],
    sholl_radii: List[float] = [10.0, 20.0, 30.0, 40.0, 50.0]
) -> Optional[Dict[str, Any]]:
    """
    Process a single image file to extract morphological metrics.
    Returns a dictionary with metrics or None if the image is skipped.
    """
    # Validate brain region early to exclude invalid rows
    if not validate_brain_region(metadata.get('brain_region')):
        logger.warning(f"Skipping {image_path}: Invalid brain_region '{metadata.get('brain_region')}'")
        return None

    # Check for empty fields of view
    if handle_empty_fields(image_path):
        logger.warning(f"Skipping {image_path}: Empty field of view detected.")
        return None

    try:
        # 1. Load and Preprocess
        image = denoise_and_subtract(image_path)

        # 2. Skeletonize and Count Branch Points
        skeleton, branch_points = skeletonize_and_count(image)

        # 3. Calculate Soma Area and Total Length
        soma_area, total_length = calculate_soma_area_and_length(image, skeleton)

        # 4. Run Sholl Analysis
        sholl_intersections = run_sholl_analysis(skeleton, radii=sholl_radii)

        # Construct result row
        result = {
            'file_path': str(image_path),
            'brain_region': metadata.get('brain_region'),
            'pathology_status': metadata.get('pathology_status'),
            'branch_points': branch_points,
            'total_length': total_length,
            'soma_area': soma_area,
            'sholl_intersections': sholl_intersections,
            # Ensure cognitive_score is present if required by schema downstream,
            # though T012 handles exclusion of missing cognitive scores before this stage.
            'cognitive_score': metadata.get('cognitive_score')
        }
        return result

    except Exception as e:
        logger.error(f"Failed to process {image_path}: {e}")
        return None

def run_output_pipeline(
    input_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    sholl_radii: Optional[List[float]] = None
) -> str:
    """
    Main entry point to generate the morphological metrics CSV.
    Reads from the raw data directory, processes images, and writes to data/processed/morphological_metrics.csv.
    """
    if sholl_radii is None:
        sholl_radii = [10.0, 20.0, 30.0, 40.0, 50.0]

    # Determine paths using config
    if input_dir is None:
        input_dir = get_path('data_raw')
    if output_path is None:
        output_path = get_path('data_processed', 'morphological_metrics.csv')

    ensure_dirs(output_path)

    logger.info(f"Starting output pipeline. Input: {input_dir}, Output: {output_path}")

    # Ingest directory to get list of images and their metadata
    # This function internally handles filtering for valid brain regions and metadata
    image_list = ingest_directory(input_dir)

    if not image_list:
        logger.warning("No valid images found to process.")
        # Write empty CSV with headers to satisfy schema requirements
        df = pd.DataFrame(columns=[
            'file_path', 'brain_region', 'pathology_status',
            'branch_points', 'total_length', 'soma_area',
            'sholl_intersections', 'cognitive_score'
        ])
        df.to_csv(output_path, index=False)
        return str(output_path)

    results = []
    for img_path, metadata in image_list:
        # T012 Logic: Exclude subjects missing cognitive scores
        if metadata.get('cognitive_score') is None:
            warn_missing_metadata('cognitive_score', str(img_path))
            continue

        row = process_image_file(img_path, metadata, sholl_radii)
        if row:
            results.append(row)

    # Create DataFrame
    df = pd.DataFrame(results)

    # Ensure columns exist even if empty
    required_cols = [
        'file_path', 'brain_region', 'pathology_status',
        'branch_points', 'total_length', 'soma_area',
        'sholl_intersections', 'cognitive_score'
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    # Select and order columns
    df = df[required_cols]

    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {output_path}")

    return str(output_path)
