import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from config import load_config, get_config, ensure_dirs
from utils import get_logger, log_stage, ensure_directory
from download import download_sparc_data

# Constants for quality filtering
MAX_INCLINATION_UNCERTAINTY = 10.0  # degrees
MIN_ROTATION_CURVE_POINTS = 15

def parse_sparc_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse a single SPARC galaxy data file.
    
    Expected format:
    - Header lines starting with '#'
    - Data columns: R (kpc), V (km/s), sigma_V (km/s), L (Lsun), sigma_L (Lsun), etc.
    - Inclination info in header or separate metadata
    
    Returns a dictionary with galaxy metadata and rotation curve data.
    """
    logger = get_logger(__name__)
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return None
    
    # Parse header for metadata
    metadata = {}
    data_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('#'):
            # Parse header metadata
            if 'galaxy' in line.lower() or 'name' in line.lower():
                # Extract galaxy name
                parts = line.split(':')
                if len(parts) > 1:
                    metadata['name'] = parts[1].strip()
            elif 'inclination' in line.lower():
                # Parse inclination and uncertainty
                # Format: Inclination: 45.0 +/- 5.0 deg
                parts = line.split()
                try:
                    for i, part in enumerate(parts):
                        if '+' in part or '-' in part:
                            # Found +/- indicator
                            if i > 0:
                                inclination = float(parts[i-1])
                                uncertainty = float(part.replace('+', '').replace('-', ''))
                                metadata['inclination'] = inclination
                                metadata['inclination_uncertainty'] = uncertainty
                                break
                except (ValueError, IndexError):
                    pass
            elif 'distance' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        metadata['distance'] = float(parts[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
        else:
            data_lines.append(line)
    
    # Parse rotation curve data
    if not data_lines:
        logger.warning(f"No data lines found in {file_path}")
        return None if not metadata.get('name') else {'name': 'Unknown', 'data': pd.DataFrame()}
    
    # Determine column structure (SPARC typically has: R, V, sigma_V, ...)
    first_data = data_lines[0].split()
    if len(first_data) < 3:
        logger.warning(f"Insufficient columns in {file_path}")
        return None
    
    # Extract radial distance, velocity, and uncertainty
    rotation_data = []
    for line in data_lines:
        parts = line.split()
        if len(parts) >= 3:
            try:
                r = float(parts[0])  # Radial distance in kpc
                v = float(parts[1])  # Velocity in km/s
                sigma_v = float(parts[2])  # Velocity uncertainty in km/s
                rotation_data.append({'r': r, 'v': v, 'sigma_v': sigma_v})
            except ValueError:
                continue
    
    if not rotation_data:
        logger.warning(f"No valid data points in {file_path}")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(rotation_data)
    
    # Add metadata
    if 'name' not in metadata:
        metadata['name'] = file_path.stem
    
    return {
        'name': metadata['name'],
        'data': df,
        'inclination': metadata.get('inclination'),
        'inclination_uncertainty': metadata.get('inclination_uncertainty'),
        'distance': metadata.get('distance')
    }

def parse_galaxy_directory(directory: Path) -> List[Dict[str, Any]]:
    """
    Parse all galaxy files in a directory.
    
    Args:
        directory: Path to directory containing SPARC galaxy files
        
    Returns:
        List of parsed galaxy dictionaries
    """
    logger = get_logger(__name__)
    galaxies = []
    
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory}")
        return galaxies
    
    # Find all data files (common SPARC extensions)
    file_extensions = ['.dat', '.txt', '.csv']
    files = []
    for ext in file_extensions:
        files.extend(directory.glob(f'*{ext}'))
    
    # Also check for files without extension that might be data files
    for item in directory.iterdir():
        if item.is_file() and item.suffix not in file_extensions:
            # Check if it looks like a data file (has numeric content)
            try:
                with open(item, 'r') as f:
                    first_line = f.readline().strip()
                    if first_line and first_line[0].isdigit():
                        files.append(item)
            except:
                continue
    
    logger.info(f"Found {len(files)} potential data files in {directory}")
    
    for file_path in files:
        logger.debug(f"Parsing {file_path}")
        result = parse_sparc_file(file_path)
        if result and result.get('data') is not None and len(result['data']) > 0:
            galaxies.append(result)
    
    return galaxies

def apply_quality_filters(galaxies: List[Dict[str, Any]], 
                          max_inclination_uncertainty: float = MAX_INCLINATION_UNCERTAINTY,
                          min_points: int = MIN_ROTATION_CURVE_POINTS) -> List[Dict[str, Any]]:
    """
    Apply quality filters to exclude low-quality galaxies.
    
    Filters:
    1. Exclude galaxies with inclination uncertainty >= max_inclination_uncertainty degrees
    2. Exclude galaxies with fewer than min_points rotation curve measurements
    
    Args:
        galaxies: List of parsed galaxy dictionaries
        max_inclination_uncertainty: Maximum allowed inclination uncertainty (degrees)
        min_points: Minimum number of rotation curve points required
        
    Returns:
        Filtered list of galaxies
    """
    logger = get_logger(__name__)
    filtered_galaxies = []
    excluded_reasons = []
    
    for galaxy in galaxies:
        name = galaxy.get('name', 'Unknown')
        data = galaxy.get('data')
        inclination_uncertainty = galaxy.get('inclination_uncertainty')
        
        # Check number of points
        if data is None or len(data) < min_points:
            reason = f"Insufficient points ({len(data) if data is not None else 0} < {min_points})"
            excluded_reasons.append((name, reason))
            continue
        
        # Check inclination uncertainty
        if inclination_uncertainty is None:
            # If uncertainty is not available, we might want to exclude or include based on policy
            # For now, we'll exclude if uncertainty is missing as we can't verify quality
            reason = "Missing inclination uncertainty"
            excluded_reasons.append((name, reason))
            continue
        
        if inclination_uncertainty >= max_inclination_uncertainty:
            reason = f"Inclination uncertainty too high ({inclination_uncertainty} >= {max_inclination_uncertainty})"
            excluded_reasons.append((name, reason))
            continue
        
        # Galaxy passes all filters
        filtered_galaxies.append(galaxy)
    
    # Log summary
    logger.info(f"Quality filtering: {len(filtered_galaxies)} passed, {len(excluded_reasons)} excluded")
    for name, reason in excluded_reasons:
        logger.debug(f"Excluded {name}: {reason}")
    
    return filtered_galaxies

def extract_rotation_curves(galaxies: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Extract rotation curve data into a unified DataFrame.
    
    Args:
        galaxies: List of parsed galaxy dictionaries
        
    Returns:
        DataFrame with columns: galaxy_name, r, v, sigma_v, inclination, inclination_uncertainty
    """
    logger = get_logger(__name__)
    
    all_rows = []
    
    for galaxy in galaxies:
        name = galaxy.get('name', 'Unknown')
        data = galaxy.get('data')
        inclination = galaxy.get('inclination')
        inclination_uncertainty = galaxy.get('inclination_uncertainty')
        
        if data is None or len(data) == 0:
            continue
        
        for _, row in data.iterrows():
            all_rows.append({
                'galaxy_name': name,
                'r': row['r'],
                'v': row['v'],
                'sigma_v': row['sigma_v'],
                'inclination': inclination,
                'inclination_uncertainty': inclination_uncertainty
            })
    
    if not all_rows:
        logger.warning("No rotation curve data extracted")
        return pd.DataFrame(columns=['galaxy_name', 'r', 'v', 'sigma_v', 'inclination', 'inclination_uncertainty'])
    
    return pd.DataFrame(all_rows)

def main():
    """
    Main pipeline for downloading, parsing, and filtering SPARC data.
    
    This function:
    1. Downloads SPARC data (if not already present)
    2. Parses all galaxy files
    3. Applies quality filters (inclination uncertainty < 10°, points >= 15)
    4. Saves filtered data to data/processed/filtered_galaxies.csv
    5. Updates data/metadata.yaml with processing timestamp
    """
    logger = setup_logging()
    log_stage(logger, "START", "T014: Quality Filtering Pipeline")
    
    # Load configuration
    config = load_config()
    data_dir = Path(config.get('data_dir', 'data'))
    raw_dir = data_dir / 'raw'
    processed_dir = data_dir / 'processed'
    
    # Ensure directories exist
    ensure_dirs([raw_dir, processed_dir])
    
    # Step 1: Download SPARC data if needed
    sparc_url = config.get('sparc_url', 'https://bitbucket.org/kyleohayden/sparc/raw/master/')
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if data already exists
    galaxy_files = list(raw_dir.glob('*'))
    if not galaxy_files:
        logger.info("Downloading SPARC data...")
        download_sparc_data(sparc_url, raw_dir)
    else:
        logger.info(f"Found {len(galaxy_files)} existing files in {raw_dir}")
    
    # Step 2: Parse all galaxy files
    logger.info("Parsing galaxy files...")
    galaxies = parse_galaxy_directory(raw_dir)
    logger.info(f"Parsed {len(galaxies)} galaxies")
    
    if not galaxies:
        logger.error("No galaxies parsed. Exiting.")
        return
    
    # Step 3: Apply quality filters
    logger.info("Applying quality filters...")
    filtered_galaxies = apply_quality_filters(
        galaxies,
        max_inclination_uncertainty=MAX_INCLINATION_UNCERTAINTY,
        min_points=MIN_ROTATION_CURVE_POINTS
    )
    logger.info(f"Quality filter result: {len(filtered_galaxies)} galaxies passed")
    
    # Step 4: Extract rotation curves and save
    logger.info("Extracting rotation curves...")
    rotation_df = extract_rotation_curves(filtered_galaxies)
    
    output_file = processed_dir / 'filtered_galaxies.csv'
    rotation_df.to_csv(output_file, index=False)
    logger.info(f"Saved filtered data to {output_file}")
    logger.info(f"Total points: {len(rotation_df)}, Total galaxies: {rotation_df['galaxy_name'].nunique()}")
    
    # Step 5: Update metadata
    from utils import get_timestamp
    metadata_file = data_dir / 'metadata.yaml'
    
    if metadata_file.exists():
        import yaml
        with open(metadata_file, 'r') as f:
            metadata = yaml.safe_load(f) or {}
    else:
        metadata = {}
    
    metadata['last_processed'] = get_timestamp()
    metadata['filter_criteria'] = {
        'max_inclination_uncertainty': MAX_INCLINATION_UNCERTAINTY,
        'min_points': MIN_ROTATION_CURVE_POINTS
    }
    metadata['statistics'] = {
        'total_galaxies_parsed': len(galaxies),
        'galaxies_after_filter': len(filtered_galaxies),
        'total_data_points': len(rotation_df)
    }
    
    with open(metadata_file, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)
    
    logger.info(f"Updated metadata in {metadata_file}")
    log_stage(logger, "SUCCESS", "T014: Quality Filtering Pipeline completed")

if __name__ == "__main__":
    main()