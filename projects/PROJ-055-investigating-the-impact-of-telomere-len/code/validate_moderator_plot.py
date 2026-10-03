import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config
from logging_config import init_project_logging

logger = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the merged processed data from the pipeline."""
    config = get_config()
    file_path = config.get('paths', {}).get('merged_data', 'data/processed/merged_data.csv')
    path_obj = Path(file_path)
    
    if not path_obj.exists():
        raise FileNotFoundError(f"Processed data file not found at {path_obj}")
    
    return pd.read_csv(path_obj)

def load_moderator_results() -> pd.DataFrame:
    """Load the moderator analysis results containing interaction stats."""
    config = get_config()
    file_path = config.get('paths', {}).get('moderator_results', 'results/moderator_analysis.csv')
    path_obj = Path(file_path)
    
    if not path_obj.exists():
        raise FileNotFoundError(f"Moderator results file not found at {path_obj}")
    
    return pd.read_csv(path_obj)

def validate_plot_exists(plot_path: str) -> bool:
    """Check if the moderator plot file exists."""
    p = Path(plot_path)
    if not p.exists():
        logger.error(f"Plot file does not exist: {plot_path}")
        return False
    
    # Check file size is non-zero
    if p.stat().st_size == 0:
        logger.error(f"Plot file is empty: {plot_path}")
        return False
    
    return True

def validate_plot_content(plot_path: str, data: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate the content of the plot image.
    Checks:
    1. Image can be opened.
    2. Image has reasonable dimensions (not a tiny placeholder).
    3. (Heuristic) Image is not purely white/black (indicates a blank plot).
    """
    errors = []
    try:
        img = Image.open(plot_path)
        width, height = img.size
        
        # Minimum reasonable size for a scientific plot
        if width < 400 or height < 300:
            errors.append(f"Image dimensions too small: {width}x{height}")
            return False, errors

        # Convert to numpy to check for blankness
        img_array = np.array(img)
        
        # Check if image is completely uniform (blank)
        if np.all(img_array == img_array[0, 0]):
            errors.append("Image appears to be a solid color (blank plot)")
            return False, errors
        
        # Check for very low variance (likely a blank or error plot)
        if np.std(img_array) < 5.0:
            errors.append("Image has very low variance (likely blank or error)")
            return False, errors

        logger.info(f"Plot content validation passed: {width}x{height}, std={np.std(img_array):.2f}")
        return True, []

    except Exception as e:
        errors.append(f"Failed to open or process image: {str(e)}")
        return False, errors

def validate_species_grouping(data: pd.DataFrame, plot_path: str) -> Tuple[bool, List[str]]:
    """
    Validate that the plot correctly visualizes species grouping by migration status.
    Logic:
    1. Verify input data has distinct groups for 'migration_status'.
    2. Verify the plot file exists (checked elsewhere but re-verified here).
    3. (Heuristic) Since we cannot easily parse text from the PNG without OCR,
       we validate that the INPUT data supports the grouping. If the data has
       no 'Migratory' or 'Resident' groups, the plot cannot be correct.
    4. We assume the plotting function (T035) was correct if the data supports it.
       This validator ensures the DATA prerequisites for the plot are met.
    """
    errors = []
    
    # Check required column exists
    if 'migration_status' not in data.columns:
        errors.append("Input data missing 'migration_status' column")
        return False, errors
    
    if 'telomere_length_kb' not in data.columns:
        errors.append("Input data missing 'telomere_length_kb' column")
        return False, errors
    
    if 'lifespan' not in data.columns:
        errors.append("Input data missing 'lifespan' column")
        return False, errors

    # Check for expected groups
    unique_statuses = data['migration_status'].dropna().unique()
    unique_statuses = [str(s).strip() for s in unique_statuses]
    
    expected_groups = {'Migratory', 'Resident'}
    found_groups = set(unique_statuses)
    
    if not expected_groups.issubset(found_groups):
        missing = expected_groups - found_groups
        errors.append(f"Input data missing required migration groups: {missing}. "
                      f"Found: {unique_statuses}")
        return False, errors
    
    # Count species per group to ensure we have data to plot
    group_counts = data['migration_status'].value_counts()
    for group in expected_groups:
        if group_counts.get(group, 0) < 2:
            errors.append(f"Insufficient data for group '{group}' (count: {group_counts.get(group, 0)})")
            return False, errors

    logger.info(f"Species grouping validation passed. Groups found: {unique_statuses}")
    return True, []

def main():
    """Main entry point for validation."""
    init_project_logging()
    logger.info("Starting Moderator Plot Validation (T036)")
    
    config = get_config()
    plot_path = config.get('paths', {}).get('moderator_plot', 'results/moderator_plot.png')
    
    success = True
    
    # 1. Check file existence
    if not validate_plot_exists(plot_path):
        success = False
    else:
        # 2. Load data
        try:
            data = load_processed_data()
            _ = load_moderator_results() # Ensure results exist too
        except FileNotFoundError as e:
            logger.error(f"Data loading failed: {e}")
            success = False
            data = None
        except Exception as e:
            logger.error(f"Unexpected error loading data: {e}")
            success = False
            data = None
        
        if data is not None:
            # 3. Validate plot content
            content_ok, content_errors = validate_plot_content(plot_path, data)
            if not content_ok:
                success = False
                for err in content_errors:
                    logger.error(f"Plot content error: {err}")
            
            # 4. Validate species grouping logic
            grouping_ok, grouping_errors = validate_species_grouping(data, plot_path)
            if not grouping_ok:
                success = False
                for err in grouping_errors:
                    logger.error(f"Grouping validation error: {err}")

    if success:
        logger.info("Validation PASSED: results/moderator_plot.png is valid.")
        return 0
    else:
        logger.error("Validation FAILED: results/moderator_plot.png is invalid or missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
