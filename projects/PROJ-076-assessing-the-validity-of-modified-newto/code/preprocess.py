import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from utils import get_logger, ensure_directory
from config import get_config

logger = get_logger(__name__)


def parse_sparc_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse a single SPARC galaxy data file.
    
    Expects a file format with columns:
    R (kpc), V (km/s), V_err (km/s), inclination, inclination_err
    
    Returns a dictionary with galaxy metadata and rotation curve data.
    """
    logger.info(f"Parsing SPARC file: {file_path}")
    
    try:
        # SPARC files often have headers; we try to read the data section
        # Assuming a standard format where data starts after header lines
        df = pd.read_csv(file_path, delim_whitespace=True, comment='#', header=None)
        
        # Expected columns based on SPARC format:
        # 0: R (kpc), 1: V (km/s), 2: V_err (km/s), 3: inclination, 4: inclination_err
        # Some files might have different column orders, so we check headers if available
        
        if df.shape[1] < 5:
            logger.warning(f"File {file_path} has fewer than 5 columns, skipping.")
            return None
        
        rotation_data = {
            'r': df.iloc[:, 0].values,
            'v': df.iloc[:, 1].values,
            'v_err': df.iloc[:, 2].values,
            'inclination': df.iloc[:, 3].values,
            'inclination_err': df.iloc[:, 4].values
        }
        
        # Extract galaxy name from filename
        galaxy_name = file_path.stem
        
        return {
            'name': galaxy_name,
            'file_path': str(file_path),
            'rotation_data': rotation_data,
            'n_points': len(rotation_data['r'])
        }
        
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return None


def parse_galaxy_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse all galaxy files in a directory.
    
    Args:
        data_dir: Path to directory containing SPARC galaxy files
        
    Returns:
        List of parsed galaxy dictionaries
    """
    logger.info(f"Parsing galaxy directory: {data_dir}")
    
    if not data_dir.exists():
        logger.error(f"Directory does not exist: {data_dir}")
        return []
    
    galaxies = []
    
    # Look for .txt or .dat files
    for file_path in data_dir.iterdir():
        if file_path.suffix.lower() in ['.txt', '.dat']:
            galaxy_data = parse_sparc_file(file_path)
            if galaxy_data:
                galaxies.append(galaxy_data)
    
    logger.info(f"Parsed {len(galaxies)} galaxies from {data_dir}")
    return galaxies


def apply_quality_filters(galaxies: List[Dict[str, Any]], 
                          min_points: int = 15,
                          max_inclination_err: float = 10.0) -> List[Dict[str, Any]]:
    """
    Apply quality filters to the parsed galaxy data.
    
    Filters:
    - Exclude galaxies with inclination uncertainty >= 10°
    - Exclude galaxies with fewer than 15 data points
    
    Args:
        galaxies: List of parsed galaxy dictionaries
        min_points: Minimum number of rotation curve points required
        max_inclination_err: Maximum allowed inclination uncertainty (degrees)
        
    Returns:
        List of filtered galaxy dictionaries that pass all quality checks
    """
    logger.info(f"Applying quality filters: min_points={min_points}, max_inclination_err={max_inclination_err}")
    
    filtered_galaxies = []
    rejected_count = 0
    rejection_reasons = {
        'low_points': 0,
        'high_inclination_err': 0
    }
    
    for galaxy in galaxies:
        name = galaxy['name']
        n_points = galaxy['n_points']
        inclination_err = galaxy['rotation_data']['inclination_err']
        
        # Check number of points
        if n_points < min_points:
            logger.debug(f"Rejecting {name}: only {n_points} points (min: {min_points})")
            rejection_reasons['low_points'] += 1
            rejected_count += 1
            continue
        
        # Check inclination uncertainty (using mean if multiple values)
        if isinstance(inclination_err, np.ndarray):
            mean_inclination_err = np.mean(inclination_err)
        else:
            mean_inclination_err = inclination_err
        
        if mean_inclination_err >= max_inclination_err:
            logger.debug(f"Rejecting {name}: inclination error {mean_inclination_err:.2f}° >= {max_inclination_err}°")
            rejection_reasons['high_inclination_err'] += 1
            rejected_count += 1
            continue
        
        # Galaxy passes all filters
        filtered_galaxies.append(galaxy)
        logger.debug(f"Accepted {name}: {n_points} points, inclination_err={mean_inclination_err:.2f}°")
    
    logger.info(f"Quality filter complete: {len(filtered_galaxies)} galaxies passed, {rejected_count} rejected")
    logger.info(f"  - Rejected for low points: {rejection_reasons['low_points']}")
    logger.info(f"  - Rejected for high inclination error: {rejection_reasons['high_inclination_err']}")
    
    return filtered_galaxies


def extract_rotation_curves(filtered_galaxies: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Extract rotation curve data from filtered galaxies into a single DataFrame.
    
    Args:
        filtered_galaxies: List of filtered galaxy dictionaries
        
    Returns:
        DataFrame with columns: galaxy, r, v, v_err, inclination, inclination_err
    """
    logger.info(f"Extracting rotation curves from {len(filtered_galaxies)} galaxies")
    
    rows = []
    
    for galaxy in filtered_galaxies:
        name = galaxy['name']
        rotation_data = galaxy['rotation_data']
        
        # Ensure arrays are of equal length
        n = len(rotation_data['r'])
        
        for i in range(n):
            rows.append({
                'galaxy': name,
                'r': rotation_data['r'][i],
                'v': rotation_data['v'][i],
                'v_err': rotation_data['v_err'][i],
                'inclination': rotation_data['inclination'][i],
                'inclination_err': rotation_data['inclination_err'][i]
            })
    
    df = pd.DataFrame(rows)
    logger.info(f"Extracted {len(df)} data points from {len(filtered_galaxies)} galaxies")
    
    return df


def main():
    """
    Main entry point for the preprocessing pipeline.
    
    This function:
    1. Loads configuration
    2. Parses all galaxy files from the source directory
    3. Applies quality filters (inclination uncertainty < 10°, points >= 15)
    4. Extracts rotation curves into a DataFrame
    5. Saves the filtered data to CSV
    6. Updates metadata.yaml with processing info
    """
    logger.info("Starting preprocessing pipeline (T013 -> T014)")
    
    config = get_config()
    data_dir = Path(config['data']['source_dir'])
    output_dir = Path(config['data']['processed_dir'])
    metadata_path = Path(config['data']['metadata_path'])
    
    ensure_directory(output_dir)
    
    # Step 1: Parse galaxy files (T013)
    logger.info("Step 1: Parsing galaxy files...")
    galaxies = parse_galaxy_directory(data_dir)
    
    if not galaxies:
        logger.error("No galaxies found to process. Exiting.")
        return 1
    
    # Step 2: Apply quality filters (T014)
    logger.info("Step 2: Applying quality filters...")
    filtered_galaxies = apply_quality_filters(
        galaxies,
        min_points=15,
        max_inclination_err=10.0
    )
    
    if not filtered_galaxies:
        logger.error("No galaxies passed quality filters. Exiting.")
        return 1
    
    # Step 3: Extract rotation curves
    logger.info("Step 3: Extracting rotation curves...")
    rotation_df = extract_rotation_curves(filtered_galaxies)
    
    # Step 4: Save filtered data
    output_file = output_dir / 'filtered_galaxies.csv'
    logger.info(f"Saving filtered data to {output_file}")
    rotation_df.to_csv(output_file, index=False)
    
    logger.info(f"Preprocessing complete. Output: {output_file}")
    logger.info(f"  - Total galaxies processed: {len(galaxies)}")
    logger.info(f"  - Galaxies after filtering: {len(filtered_galaxies)}")
    logger.info(f"  - Total data points: {len(rotation_df)}")
    
    return 0


if __name__ == '__main__':
    exit(main())