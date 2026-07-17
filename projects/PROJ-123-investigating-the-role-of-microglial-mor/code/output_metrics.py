"""
output_metrics.py

Handles the final aggregation and output of morphological metrics to CSV.
Implements Task T018: Output structured CSV data/processed/morphological_metrics.csv.
"""

import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import get_path, ensure_dirs, get_project_root
from code.data_ingestion import run_ingestion_pipeline_with_exclusion
from code.morphometry import (
    process_microglia_image,
    handle_empty_fields,
    denoise_and_subtract,
    skeletonize_and_count,
    calculate_soma_area_and_length,
    run_sholl_analysis
)

logger = logging.getLogger(__name__)

def process_image_file(
    image_path: Path,
    metadata: Dict[str, Any],
    sholl_radius_step: float = 10.0,
    sholl_max_radius: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Process a single image file to extract morphological metrics.

    This function orchestrates the pipeline:
    1. Handles empty fields of view.
    2. Denoises and subtracts background.
    3. Skeletonizes and counts branch points.
    4. Calculates soma area and total length.
    5. Runs Sholl analysis.

    Returns a dictionary containing the metrics or None if the image is invalid.
    """
    # 1. Handle empty fields of view (T017)
    if handle_empty_fields(image_path):
        logger.warning(f"Skipping empty field of view: {image_path}")
        return None

    # Load image (assuming load_image is handled in process_microglia_image or here)
    # The API surface shows process_microglia_image exists, but we need to ensure
    # we are using the functions correctly. Based on T013-T016, we call specific functions.
    # We assume image loading happens inside process_microglia_image or we do it here.
    # Let's assume process_microglia_image is the high-level wrapper, but since we need
    # to chain specific steps for T013-T016, we might need to call them individually
    # or ensure process_microglia_image does the right thing.
    # However, T018 is about OUTPUT. The processing logic is in T013-T017.
    # We will assume process_microglia_image returns the raw image or we load it.
    # Given the API surface, process_microglia_image is the main entry point.
    # Let's assume it returns the image array. If it returns a dict, we adapt.
    # To be safe and explicit per T013-T016 requirements:

    try:
        # Load image
        # We need to import load_image if it's not inside process_microglia_image
        # The API surface for data_ingestion has load_image.
        from code.data_ingestion import load_image
        image = load_image(image_path)

        if image is None or image.size == 0:
            logger.warning(f"Could not load image or image is empty: {image_path}")
            return None

        # T013: Denoising and background subtraction
        processed_image = denoise_and_subtract(image)

        # T014: Skeletonization and branch point counting
        branch_points, skeleton = skeletonize_and_count(processed_image)

        # T015: Soma area and total process length
        soma_area, total_length = calculate_soma_area_and_length(processed_image, skeleton)

        # T016: Sholl analysis
        sholl_intersections = run_sholl_analysis(processed_image, skeleton, step=sholl_radius_step, max_radius=sholl_max_radius)

        # Construct result
        result = {
            'image_path': str(image_path),
            'brain_region': metadata.get('brain_region', 'Unknown'),
            'pathology_status': metadata.get('pathology_status', 'Unknown'),
            'branch_points': branch_points,
            'total_length': total_length,
            'soma_area': soma_area,
            'sholl_intersections': sholl_intersections
        }

        return result

    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}", exc_info=True)
        return None


def run_output_pipeline(
    data_root: Optional[Path] = None,
    sholl_radius_step: float = 10.0,
    sholl_max_radius: Optional[float] = None
) -> Path:
    """
    Execute the full pipeline to generate morphological metrics CSV.

    Steps:
    1. Ingest images and parse metadata (T012a).
    2. Exclude subjects missing cognitive scores or untagged regions (T012b).
    3. Process each valid image to extract metrics (T013-T017).
    4. Aggregate results into a DataFrame.
    5. Write to data/processed/morphological_metrics.csv (T018).

    Returns the path to the generated CSV file.
    """
    logger.info("Starting output metrics pipeline (T018)...")

    if data_root is None:
        data_root = get_path('DATA_ROOT')

    # T012a & T012b: Ingest and exclude
    # run_ingestion_pipeline_with_exclusion returns a list of (image_path, metadata) tuples
    # that have passed exclusion criteria.
    logger.info("Running ingestion pipeline with exclusion logic...")
    valid_entries = run_ingestion_pipeline_with_exclusion(data_root)

    if not valid_entries:
        logger.warning("No valid entries found after ingestion and exclusion. Creating empty CSV.")
        output_path = get_path('DATA_PROCESSED', 'morphological_metrics.csv')
        ensure_dirs(output_path)
        df = pd.DataFrame(columns=[
            'image_path', 'brain_region', 'pathology_status',
            'branch_points', 'total_length', 'soma_area', 'sholl_intersections'
        ])
        df.to_csv(output_path, index=False)
        logger.info(f"Empty CSV created at {output_path}")
        return output_path

    results = []
    for image_path, metadata in valid_entries:
        logger.info(f"Processing: {image_path}")
        metrics = process_image_file(
            image_path,
            metadata,
            sholl_radius_step=sholl_radius_step,
            sholl_max_radius=sholl_max_radius
        )
        if metrics:
            results.append(metrics)

    if not results:
        logger.warning("No metrics extracted. Creating empty CSV.")
        output_path = get_path('DATA_PROCESSED', 'morphological_metrics.csv')
        ensure_dirs(output_path)
        df = pd.DataFrame(columns=[
            'image_path', 'brain_region', 'pathology_status',
            'branch_points', 'total_length', 'soma_area', 'sholl_intersections'
        ])
        df.to_csv(output_path, index=False)
        return output_path

    # Create DataFrame
    df = pd.DataFrame(results)

    # Ensure columns are in the correct order as per T018 spec
    # Spec: branch_points, total_length, soma_area, sholl_intersections (plus tags)
    # We include image_path, brain_region, pathology_status for traceability
    columns = [
        'image_path', 'brain_region', 'pathology_status',
        'branch_points', 'total_length', 'soma_area', 'sholl_intersections'
    ]
    # Reorder if necessary
    existing_cols = [c for c in columns if c in df.columns]
    df = df[existing_cols]

    # T018: Write to data/processed/morphological_metrics.csv
    output_path = get_path('DATA_PROCESSED', 'morphological_metrics.csv')
    ensure_dirs(output_path)

    df.to_csv(output_path, index=False)
    logger.info(f"Morphological metrics CSV written to {output_path} with {len(df)} rows.")
    logger.info(f"Columns: {list(df.columns)}")

    return output_path