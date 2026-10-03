"""
Preprocessing module for SPARC galaxy data.

Handles parsing of rotation curve data, extraction of radial distance, velocity,
uncertainty, and application of quality filters.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from utils import get_logger, log_stage, ensure_directory

# Constants for quality filtering (FR-003)
MAX_INCLINATION_UNCERTAINTY_DEG = 10.0
MIN_ROTATION_CURVE_POINTS = 15

def parse_sparc_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse a single SPARC galaxy data file.

    Expected format:
    - First line: Galaxy name
    - Second line: Comments/headers (skipped)
    - Data lines: R (kpc), V_obs (km/s), Sigma_V (km/s), V_sys (km/s), etc.
    - Inclination data is typically in a separate metadata file or header.

    For this implementation, we assume a standard SPARC format where:
    - Column 0: Radial distance (kpc)
    - Column 1: Observed velocity (km/s)
    - Column 2: Uncertainty in velocity (km/s)
    - We need to handle inclination separately if available in the file or metadata.

    Returns a dictionary with:
    - 'galaxy_name': str
    - 'r': np.array (kpc)
    - 'v_obs': np.array (km/s)
    - 'v_err': np.array (km/s)
    - 'inclination_deg': float (if available)
    - 'inclination_err': float (if available)
    - 'raw_data': pd.DataFrame
    """
    logger = get_logger(__name__)

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        if len(lines) < 3:
            logger.warning(f"File {file_path} has too few lines to be valid.")
            return None

        galaxy_name = lines[0].strip()
        # Skip header/comments line (lines[1])
        # Data starts at lines[2]

        data_lines = []
        for line in lines[2:]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                parts = line.split()
                # SPARC files usually have: R, V_obs, Sigma_V, V_sys, V_rot, etc.
                # We need at least R, V_obs, Sigma_V
                if len(parts) >= 3:
                    r = float(parts[0])
                    v_obs = float(parts[1])
                    v_err = float(parts[2])
                    data_lines.append([r, v_obs, v_err])
            except ValueError:
                continue

        if not data_lines:
            logger.warning(f"No valid data rows found in {file_path}")
            return None

        df = pd.DataFrame(data_lines, columns=['r', 'v_obs', 'v_err'])

        # Try to extract inclination from filename or nearby metadata
        # SPARC often has a 'M' file for mass and 'I' file for inclination
        # For now, we'll try to parse a standard format if available
        inclination_deg = None
        inclination_err = None

        # Check if there's a companion file for inclination (e.g., galaxy_I.txt)
        stem = file_path.stem
        parent = file_path.parent
        inc_file = parent / f"{stem}_I.txt"
        if inc_file.exists():
            try:
                with open(inc_file, 'r') as f:
                    inc_lines = f.readlines()
                # Assume first line is inclination, second is error if present
                if len(inc_lines) >= 1:
                    inc_parts = inc_lines[0].strip().split()
                    if inc_parts:
                        inclination_deg = float(inc_parts[0])
                if len(inc_lines) >= 2:
                    inc_err_parts = inc_lines[1].strip().split()
                    if inc_err_parts:
                        inclination_err = float(inc_err_parts[0])
            except Exception as e:
                logger.warning(f"Could not parse inclination from {inc_file}: {e}")

        return {
            'galaxy_name': galaxy_name,
            'r': df['r'].values,
            'v_obs': df['v_obs'].values,
            'v_err': df['v_err'].values,
            'inclination_deg': inclination_deg,
            'inclination_err': inclination_err,
            'raw_data': df
        }

    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return None

def parse_galaxy_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse all galaxy data files in a directory.

    Args:
        data_dir: Path to directory containing SPARC galaxy data files.

    Returns:
        List of parsed galaxy dictionaries.
    """
    logger = get_logger(__name__)
    parsed_galaxies = []

    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} does not exist.")
        return parsed_galaxies

    # Look for typical SPARC data files (e.g., *.txt, *_Vrot.txt)
    data_files = list(data_dir.glob("*.txt")) + list(data_dir.glob("*_Vrot.txt"))

    for file_path in data_files:
        result = parse_sparc_file(file_path)
        if result:
            parsed_galaxies.append(result)
            logger.info(f"Parsed galaxy: {result['galaxy_name']}")

    logger.info(f"Successfully parsed {len(parsed_galaxies)} galaxies.")
    return parsed_galaxies

def apply_quality_filters(galaxies: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Apply quality filters to the parsed galaxy data (FR-003).

    Filters:
    1. Exclude galaxies with inclination uncertainty >= 10 degrees (if available).
    2. Exclude galaxies with fewer than MIN_ROTATION_CURVE_POINTS data points.

    Args:
        galaxies: List of parsed galaxy dictionaries.

    Returns:
        Tuple of (filtered_galaxies, num_removed)
    """
    logger = get_logger(__name__)
    filtered = []
    removed_count = 0

    for galaxy in galaxies:
        name = galaxy['galaxy_name']
        num_points = len(galaxy['r'])
        inc_err = galaxy.get('inclination_err')

        # Check point count
        if num_points < MIN_ROTATION_CURVE_POINTS:
            logger.debug(f"Removing {name}: only {num_points} points (< {MIN_ROTATION_CURVE_POINTS})")
            removed_count += 1
            continue

        # Check inclination uncertainty if available
        if inc_err is not None:
            if inc_err >= MAX_INCLINATION_UNCERTAINTY_DEG:
                logger.debug(f"Removing {name}: inclination uncertainty {inc_err} >= {MAX_INCLINATION_UNCERTAINTY_DEG}")
                removed_count += 1
                continue

        filtered.append(galaxy)

    logger.info(f"Quality filter applied: {removed_count} galaxies removed, {len(filtered)} retained.")
    return filtered, removed_count

def extract_rotation_curves(filtered_galaxies: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Extract rotation curve data into a standardized DataFrame.

    Args:
        filtered_galaxies: List of filtered galaxy dictionaries.

    Returns:
        DataFrame with columns: galaxy_name, r, v_obs, v_err, inclination_deg, inclination_err
    """
    rows = []
    for galaxy in filtered_galaxies:
        n_points = len(galaxy['r'])
        for i in range(n_points):
            rows.append({
                'galaxy_name': galaxy['galaxy_name'],
                'r': galaxy['r'][i],
                'v_obs': galaxy['v_obs'][i],
                'v_err': galaxy['v_err'][i],
                'inclination_deg': galaxy.get('inclination_deg'),
                'inclination_err': galaxy.get('inclination_err')
            })

    df = pd.DataFrame(rows)
    return df

def main():
    """
    Main entry point for preprocessing pipeline.

    Steps:
    1. Load raw SPARC data from data/raw/
    2. Parse all galaxy files
    3. Apply quality filters (FR-003)
    4. Save filtered data to data/processed/filtered_galaxies.csv
    5. Update metadata.yaml
    """
    logger = get_logger(__name__)
    log_stage(logger, "Starting preprocessing pipeline (T014)")

    # Paths
    raw_data_dir = Path("data/raw/sparc")
    processed_dir = Path("data/processed")
    metadata_path = Path("data/metadata.yaml")

    ensure_directory(processed_dir)

    # Parse data
    galaxies = parse_galaxy_directory(raw_data_dir)
    if not galaxies:
        logger.error("No galaxies parsed. Exiting.")
        return

    # Apply quality filters (T014)
    filtered_galaxies, removed_count = apply_quality_filters(galaxies)

    if not filtered_galaxies:
        logger.error("No galaxies passed quality filters. Exiting.")
        return

    # Extract to DataFrame
    df = extract_rotation_curves(filtered_galaxies)

    # Save output
    output_path = processed_dir / "filtered_galaxies.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} data points to {output_path}")

    # Update metadata
    if metadata_path.exists():
        import yaml
        from datetime import datetime

        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)

        metadata['preprocessing'] = {
            'timestamp': datetime.now().isoformat(),
            'filters_applied': {
                'min_points': MIN_ROTATION_CURVE_POINTS,
                'max_inclination_uncertainty': MAX_INCLINATION_UNCERTAINTY_DEG
            },
            'galaxies_before_filtering': len(galaxies),
            'galaxies_after_filtering': len(filtered_galaxies),
            'removed_count': removed_count
        }

        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)

        logger.info(f"Updated metadata at {metadata_path}")
    else:
        logger.warning(f"Metadata file {metadata_path} not found. Skipping update.")

    log_stage(logger, "Preprocessing pipeline completed successfully")

if __name__ == "__main__":
    main()