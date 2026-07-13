"""
Data download and verification module for bird migration and climate data.

This module provides functionality to:
- Check for real eBird/NOAA data files
- Generate synthetic data for development (if real data missing)
- Archive existing data and compute checksums
- Manage state tracking of data artifacts
"""

import os
import sys
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def check_data_availability(
    ebird_dir: Path,
    climate_dir: Path
) -> Dict[str, bool]:
    """
    Check for presence of real eBird and climate data files.

    Args:
        ebird_dir: Path to eBird raw data directory
        climate_dir: Path to climate raw data directory

    Returns:
        Dictionary with 'ebird' and 'climate' keys indicating availability
    """
    ebird_files = list(ebird_dir.glob("*.csv")) if ebird_dir.exists() else []
    climate_files = list(climate_dir.glob("*.parquet")) if climate_dir.exists() else []

    return {
        'ebird': len(ebird_files) > 0,
        'climate': len(climate_files) > 0
    }


def generate_synthetic_data(
    output_dir: Path,
    seed: int = 42
) -> Dict[str, Path]:
    """
    Generate synthetic eBird and climate data for development purposes.

    Args:
        output_dir: Directory to write synthetic data files
        seed: Random seed for reproducibility

    Returns:
        Dictionary mapping data type to generated file path
    """
    import numpy as np
    import pandas as pd

    np.random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate synthetic eBird data
    n_records = 1000
    species_list = ['Turdus migratorius', 'Setophaga coronata', 'Cardinalis cardinalis']
    ebird_data = {
        'species': np.random.choice(species_list, n_records),
        'lat': np.random.uniform(25, 50, n_records),
        'lon': np.random.uniform(-125, -70, n_records),
        'date': pd.date_range('2020-01-01', periods=n_records, freq='D'),
        'count': np.random.randint(1, 50, n_records),
        'checklist_id': [f'CHK_{i:06d}' for i in range(n_records)]
    }
    ebird_df = pd.DataFrame(ebird_data)
    ebird_path = output_dir / 'synthetic_ebird.csv'
    ebird_df.to_csv(ebird_path, index=False)

    # Generate synthetic climate data
    n_climate = 500
    climate_data = {
        'lat': np.random.uniform(25, 50, n_climate),
        'lon': np.random.uniform(-125, -70, n_climate),
        'temp': np.random.normal(15, 10, n_climate),
        'week': np.random.randint(1, 53, n_climate),
        'precip': np.random.exponential(5, n_climate)
    }
    climate_df = pd.DataFrame(climate_data)
    climate_path = output_dir / 'synthetic_climate.parquet'
    climate_df.to_parquet(climate_path, index=False)

    return {
        'ebird': ebird_path,
        'climate': climate_path
    }


def archive_data(
    source_dir: Path,
    archive_dir: Path,
    checksums: Optional[Dict[str, str]] = None
) -> None:
    """
    Archive existing data files without modification.

    Args:
        source_dir: Source directory containing data files
        archive_dir: Destination directory for archived files
        checksums: Optional dictionary to store checksums
    """
    if not source_dir.exists():
        logger.warning(f"Source directory {source_dir} does not exist")
        return

    archive_dir.mkdir(parents=True, exist_ok=True)

    for file_path in source_dir.iterdir():
        if file_path.is_file():
            dest_path = archive_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            logger.info(f"Archived: {file_path} -> {dest_path}")

            if checksums is not None:
                checksums[file_path.name] = compute_sha256(file_path)


def update_state_file(
    state_path: Path,
    artifact_hashes: Dict[str, str],
    updated_at: str
) -> None:
    """
    Update the project state file with artifact checksums and timestamp.

    Args:
        state_path: Path to the state YAML file
        artifact_hashes: Dictionary of artifact name to SHA-256 hash
        updated_at: ISO format timestamp
    """
    import yaml

    state_path.parent.mkdir(parents=True, exist_ok=True)

    state_data = {
        'artifact_hashes': artifact_hashes,
        'updated_at': updated_at
    }

    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)

    logger.info(f"Updated state file: {state_path}")


def run_download_pipeline(
    mode: str = 'production',
    seed: int = 42
) -> bool:
    """
    Main entry point for data download and preparation.

    Args:
        mode: 'production' (abort if no real data) or 'development' (generate synthetic)
        seed: Random seed for synthetic data generation

    Returns:
        True if data preparation succeeded, False otherwise
    """
    project_root = Path(__file__).parent.parent.parent
    data_raw_dir = project_root / 'data' / 'raw'
    ebird_dir = data_raw_dir / 'ebird'
    climate_dir = data_raw_dir / 'climate'
    archive_dir = data_raw_dir / 'archive'
    state_dir = project_root / 'state' / 'projects'

    # Check for real data
    availability = check_data_availability(ebird_dir, climate_dir)
    logger.info(f"Data availability: {availability}")

    if not (availability['ebird'] and availability['climate']):
        if mode == 'production':
            logger.error("Real data required for production run")
            sys.exit(1)
        else:
            logger.info("Real data missing, generating synthetic data for development")
            generate_synthetic_data(data_raw_dir, seed=seed)
            logger.info("Synthetic data generation complete")

    # Archive existing real data
    all_checksums = {}
    if ebird_dir.exists():
        archive_data(ebird_dir, archive_dir, all_checksums)
    if climate_dir.exists():
        archive_data(climate_dir, archive_dir, all_checksums)

    # Update state file
    if all_checksums:
        from datetime import datetime
        state_path = state_dir / 'PROJ-132-statistical-analysis-of-publicly-availab.yaml'
        update_state_file(
            state_path,
            artifact_hashes=all_checksums,
            updated_at=datetime.now().isoformat()
        )

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Data download and preparation pipeline')
    parser.add_argument(
        '--mode',
        choices=['production', 'development'],
        default='production',
        help='Operation mode: production (requires real data) or development (synthetic data)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for synthetic data generation'
    )

    args = parser.parse_args()
    success = run_download_pipeline(mode=args.mode, seed=args.seed)

    if success:
        logger.info("Data pipeline completed successfully")
        sys.exit(0)
    else:
        logger.error("Data pipeline failed")
        sys.exit(1)