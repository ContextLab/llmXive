"""
Generic ROI Fallback Implementation for User Story 1 (T013).

This module implements the logic to apply a Generic ROI Fallback (3x3 grid)
if `roi_annotations` are missing from the dataset. It integrates with the
existing validation and feature extraction pipeline.

Key Functions:
- define_generic_roi_grid: Creates a 3x3 grid definition for face images.
- apply_roi_fallback: Injects the grid into records missing `roi_annotations`.
- run_roi_fallback_pipeline: Orchestrates the fallback application and logging.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from existing API surface
from config import get_config
from utils.logging import get_logger

# Import the existing fallback definition from extraction if available,
# or define it here to ensure T013 logic is self-contained and visible.
# The spec mentions T007 implemented this in extraction.py, so we import it.
try:
    from features.extraction import define_generic_roi_grid
except ImportError:
    # Fallback definition if T007 wasn't fully exposed or for standalone use
    def define_generic_roi_grid(image_width: int = 200, image_height: int = 200) -> Dict[str, Any]:
        """
        Defines a 3x3 grid ROI for face images.
        
        Args:
            image_width: Width of the face image in pixels.
            image_height: Height of the face image in pixels.
            
        Returns:
            A dictionary defining the 9 grid regions with coordinates.
        """
        grid = {}
        cols = 3
        rows = 3
        cell_w = image_width / cols
        cell_h = image_height / rows
        
        for r in range(rows):
            for c in range(cols):
                roi_id = f"grid_{r}_{c}"
                grid[roi_id] = {
                    "x_min": int(c * cell_w),
                    "x_max": int((c + 1) * cell_w),
                    "y_min": int(r * cell_h),
                    "y_max": int((r + 1) * cell_h),
                    "label": f"Region_{r}_{c}"
                }
        return grid


def apply_roi_fallback(
    data: List[Dict[str, Any]], 
    logger: logging.Logger,
    image_width: int = 200,
    image_height: int = 200
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Applies the Generic ROI Fallback (3x3 grid) to records missing `roi_annotations`.
    
    This function iterates through the dataset. If a record lacks `roi_annotations`,
    it generates the 3x3 grid and injects it.
    
    Args:
        data: List of participant records (dictionaries).
        logger: Logger instance for progress and status.
        image_width: Assumed width of the stimulus image.
        image_height: Assumed height of the stimulus image.
        
    Returns:
        Tuple of (updated_data_list, count_of_fallbacks_applied).
    """
    if not data:
        logger.warning("No data provided to ROI fallback.")
        return data, 0
    
    fallback_count = 0
    fallback_grid = define_generic_roi_grid(image_width, image_height)
    
    for idx, record in enumerate(data):
        if "roi_annotations" not in record or record["roi_annotations"] is None:
            logger.debug(f"Record {idx} missing roi_annotations. Applying 3x3 grid fallback.")
            record["roi_annotations"] = fallback_grid
            fallback_count += 1
        else:
            # Verify if it's actually empty or just missing key
            if not record.get("roi_annotations"):
                logger.debug(f"Record {idx} has empty roi_annotations. Applying fallback.")
                record["roi_annotations"] = fallback_grid
                fallback_count += 1
                
    if fallback_count > 0:
        logger.info(f"Applied Generic ROI Fallback (3x3 grid) to {fallback_count} records.")
    else:
        logger.info("No records required ROI fallback; all had valid annotations.")
        
    return data, fallback_count


def run_roi_fallback_pipeline(
    input_data_path: Optional[Path] = None,
    output_data_path: Optional[Path] = None,
    force_overwrite: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for the ROI Fallback pipeline (T013).
    
    Reads processed or raw data, applies the fallback if missing, 
    and writes the result back.
    
    Args:
        input_data_path: Path to the input JSON/CSV data. If None, attempts to find
                         the latest processed data or raw data.
        output_data_path: Path to write the updated data.
        force_overwrite: Whether to overwrite existing output files.
        
    Returns:
        Dictionary containing pipeline execution stats.
    """
    config = get_config()
    logger = get_logger("roi_fallback")
    
    # Determine paths if not provided
    if input_data_path is None:
        # Try to find the data file that T012 validated or T010 downloaded
        # Defaulting to a common location based on project structure
        possible_paths = [
            config.DATA_PATH / "processed" / "validated_data.json",
            config.DATA_PATH / "raw" / "downloaded_data.json",
            config.DATA_PATH / "raw" / "dataset.json"
        ]
        input_data_path = next((p for p in possible_paths if p.exists()), None)
        
    if input_data_path is None:
        logger.error("No input data path found. Please specify input_data_path.")
        return {"status": "error", "message": "Input data not found"}
        
    if not input_data_path.exists():
        logger.error(f"Input file not found: {input_data_path}")
        return {"status": "error", "message": f"File not found: {input_data_path}"}
        
    logger.info(f"Reading data from {input_data_path}")
    
    # Load data
    try:
        if input_data_path.suffix == '.json':
            with open(input_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif input_data_path.suffix == '.csv':
            import pandas as pd
            df = pd.read_csv(input_data_path)
            # Convert to list of dicts for processing
            data = df.to_dict(orient='records')
        else:
            logger.error(f"Unsupported file format: {input_data_path.suffix}")
            return {"status": "error", "message": "Unsupported format"}
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {"status": "error", "message": str(e)}
        
    if not isinstance(data, list):
        # If it's a single record or a dict containing a list
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        elif isinstance(data, dict):
            data = [data]
        else:
            logger.error("Data structure is not a list or dict with 'data' key.")
            return {"status": "error", "message": "Invalid data structure"}

    # Apply fallback
    updated_data, fallback_count = apply_roi_fallback(data, logger)
    
    # Determine output path
    if output_data_path is None:
        output_data_path = input_data_path.parent / f"{input_data_path.stem}_with_roi_fallback{input_data_path.suffix}"
        
    if output_data_path.exists() and not force_overwrite:
        logger.warning(f"Output file exists and overwrite not forced: {output_data_path}")
        # Still return success stats, but don't write
        return {
            "status": "success",
            "fallbacks_applied": fallback_count,
            "output_path": str(output_data_path),
            "message": "Skipped write due to existing file"
        }
        
    # Write output
    try:
        logger.info(f"Writing updated data to {output_data_path}")
        if output_data_path.suffix == '.json':
            with open(output_data_path, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, indent=2)
        elif output_data_path.suffix == '.csv':
            import pandas as pd
            # Flatten roi_annotations for CSV if needed, or store as JSON string
            # For simplicity, we store the grid as a JSON string in a column
            df_out = pd.DataFrame(updated_data)
            if 'roi_annotations' in df_out.columns:
                df_out['roi_annotations'] = df_out['roi_annotations'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
            df_out.to_csv(output_data_path, index=False)
            
        return {
            "status": "success",
            "fallbacks_applied": fallback_count,
            "output_path": str(output_data_path),
            "message": "ROI Fallback applied and saved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        return {"status": "error", "message": str(e)}


def main():
    """CLI entry point for T013."""
    logger = get_logger("roi_fallback_main")
    logger.info("Starting ROI Fallback Pipeline (T013)")
    
    result = run_roi_fallback_pipeline()
    
    if result["status"] == "success":
        logger.info(f"Pipeline completed successfully. Fallbacks: {result.get('fallbacks_applied', 0)}")
        sys.exit(0)
    else:
        logger.error(f"Pipeline failed: {result.get('message')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
