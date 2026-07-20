import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import get_path, ensure_dirs, get_project_root

logger = logging.getLogger(__name__)

def process_image_file(
    image_path: str,
    metadata: Dict[str, Any],
    branch_points: int,
    total_length: float,
    soma_area: float,
    sholl_intersections: float
) -> Dict[str, Any]:
    """
    Compile morphological metrics for a single image into a structured record.
    
    Args:
        image_path: Path to the source image.
        metadata: Dictionary containing brain_region, pathology_status, etc.
        branch_points: Count from skeletonize_and_count.
        total_length: Total process length in pixels.
        soma_area: Soma area in pixels.
        sholl_intersections: Count of Sholl intersections at default radius.
    
    Returns:
        Dictionary ready for DataFrame conversion.
    """
    brain_region = metadata.get('brain_region')
    pathology_status = metadata.get('pathology_status')
    
    # Validate required fields per T012a/T017 logic
    if not brain_region:
        logger.warning(f"Skipping {image_path}: missing brain_region metadata.")
        return {}
    
    if not pathology_status:
        logger.warning(f"Skipping {image_path}: missing pathology_status metadata.")
        return {}

    return {
        'file_path': str(image_path),
        'brain_region': brain_region,
        'pathology_status': pathology_status,
        'branch_points': branch_points,
        'total_length': total_length,
        'soma_area': soma_area,
        'sholl_intersections': sholl_intersections
    }

def run_output_pipeline(
    processed_data: List[Dict[str, Any]],
    output_filename: str = "morphological_metrics.csv"
) -> Optional[str]:
    """
    Aggregate processed image data into a single CSV file.
    
    This function implements T018: Output structured CSV with required columns.
    
    Args:
        processed_data: List of dictionaries returned by process_image_file.
        output_filename: Name of the output CSV file.
    
    Returns:
        Path to the generated CSV file, or None if data is empty.
    """
    if not processed_data:
        logger.warning("No data to write. Output CSV will not be generated.")
        return None

    # Filter out empty records (from skipped files)
    valid_records = [r for r in processed_data if r]
    
    if not valid_records:
        logger.warning("No valid records after filtering. Output CSV will not be generated.")
        return None

    df = pd.DataFrame(valid_records)
    
    # Ensure required columns exist and are in order per T018 spec
    required_cols = [
        'file_path', 'brain_region', 'pathology_status',
        'branch_points', 'total_length', 'soma_area', 'sholl_intersections'
    ]
    
    # Verify columns
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in output: {missing_cols}")
    
    df = df[required_cols]
    
    # Write to disk
    output_path = get_path('data', 'processed', output_filename)
    ensure_dirs(output_path)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} records to {output_path}")
    
    return str(output_path)
