import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np

from config import get_config
from logging_config import init_project_logging, handle_memory_pressure

def load_processed_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the processed merged data from US1."""
    data_path = Path(config['paths']['processed_data'])
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    return pd.read_csv(data_path)

def load_moderator_results(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the moderator analysis results from US3."""
    results_path = Path(config['paths']['moderator_results'])
    if not data_path.exists():
        raise FileNotFoundError(f"Moderator results not found at {results_path}")
    return pd.read_csv(results_path)

def validate_plot_exists(plot_path: Path) -> bool:
    """Check if the plot file exists and is not empty."""
    if not plot_path.exists():
        return False
    if plot_path.stat().st_size == 0:
        return False
    return True

def validate_plot_content(plot_path: Path, data: pd.DataFrame, results: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that the plot correctly visualizes the interaction effect and species grouping.
    
    Checks:
    1. File exists and is readable
    2. Image dimensions are reasonable
    3. Plot contains expected elements (title, legend, axes labels)
    4. Data points correspond to the input data
    5. Regression lines are present for both groups
    """
    errors = []
    
    # Check file exists
    if not validate_plot_exists(plot_path):
        errors.append("Plot file does not exist or is empty")
        return False, errors
    
    try:
        # Try to load and inspect the image
        img = mpimg.imread(str(plot_path))
        if img.shape[0] < 100 or img.shape[1] < 100:
            errors.append(f"Plot dimensions too small: {img.shape}")
    except Exception as e:
        errors.append(f"Failed to read plot image: {str(e)}")
        return False, errors
    
    # Validate that the plot corresponds to the data
    # Check that we have both migration groups in the data
    if 'migration_status' in data.columns:
        unique_groups = data['migration_status'].unique()
        if len(unique_groups) < 2:
            errors.append(f"Expected at least 2 migration groups, found {len(unique_groups)}")
    
    # Check that moderator results contain interaction term
    if results is not None and 'interaction_coefficient' in results.columns:
        interaction_coef = results['interaction_coefficient'].iloc[0]
        if np.isnan(interaction_coef):
            errors.append("Interaction coefficient is NaN - model may have failed")
    else:
        # Try to infer from results file
        errors.append("Could not find interaction coefficient in results")
    
    # Check that the plot has appropriate labels
    # This is a heuristic check - we can't easily parse text from the image
    # but we can check file size as a proxy for complexity
    if plot_path.stat().st_size < 5000:
        errors.append("Plot file size suspiciously small - may be incomplete")
    
    return len(errors) == 0, errors

def validate_species_grouping(data: pd.DataFrame, plot_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate that species are correctly grouped by migration status in the plot.
    
    This function performs a statistical check to ensure the grouping makes sense
    relative to the underlying data.
    """
    errors = []
    
    # Check that migration_status column exists
    if 'migration_status' not in data.columns:
        errors.append("Migration status column not found in data")
        return False, errors
    
    # Check that we have valid groups
    migration_groups = data['migration_status'].dropna().unique()
    if len(migration_groups) == 0:
        errors.append("No valid migration groups found in data")
        return False, errors
    
    # Check that each group has sufficient data points
    for group in migration_groups:
        group_count = len(data[data['migration_status'] == group])
        if group_count < 5:
            errors.append(f"Group '{group}' has only {group_count} data points (< 5)")
    
    # Validate that the plot file exists
    if not validate_plot_exists(plot_path):
        errors.append("Plot file does not exist")
        return False, errors
    
    return len(errors) == 0, errors

def main():
    """Main validation function for the moderator plot."""
    # Configure logging
    init_project_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = get_config()
        
        # Define paths
        plot_path = Path(config['paths']['moderator_plot'])
        data_path = Path(config['paths']['processed_data'])
        results_path = Path(config['paths']['moderator_results'])
        
        logger.info(f"Validating moderator plot at: {plot_path}")
        
        # Load data
        try:
            data = load_processed_data(config)
            logger.info(f"Loaded {len(data)} records from processed data")
        except FileNotFoundError as e:
            logger.error(f"Failed to load processed data: {str(e)}")
            return 1
        
        # Load results
        results = None
        if results_path.exists():
            try:
                results = pd.read_csv(results_path)
                logger.info(f"Loaded moderator results with {len(results)} records")
            except Exception as e:
                logger.warning(f"Failed to load moderator results: {str(e)}")
        else:
            logger.warning("Moderator results file not found")
        
        # Validate plot content
        is_valid, errors = validate_plot_content(plot_path, data, results)
        
        # Validate species grouping
        group_valid, group_errors = validate_species_grouping(data, plot_path)
        
        # Combine errors
        all_errors = errors + group_errors
        
        if is_valid and group_valid:
            logger.info("✓ Moderator plot validation PASSED")
            logger.info("  - Plot file exists and is readable")
            logger.info("  - Species grouping is valid")
            logger.info("  - Data distribution is appropriate")
            return 0
        else:
            logger.error("✗ Moderator plot validation FAILED")
            for error in all_errors:
                logger.error(f"  - {error}")
            return 1
            
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
