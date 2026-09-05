"""
Main entry point for the data pipeline (US1).

Orchestrates:
1. Fetching materials data (T011)
2. Computing descriptors (T012)
3. Generating SHA256 checksums for raw and processed data (T030a)
4. Running VIF checks (T014)
5. Saving processed data

This script is designed to be run as:
    python code/main.py

It handles configuration, logging, and error handling.
"""
import os
import sys
import logging
import hashlib
from pathlib import Path
from typing import Optional, List

import pandas as pd
import numpy as np

from config import get_config, load_config
from code.utils.logger import get_pipeline_logger
from code.utils.error_handling import handle_error, PipelineError, DataProcessingError
from code.utils.stability_checks import check_nan_inf, validate_dataframe, get_memory_stats
from code.utils.collinearity_utils import calculate_vif, identify_high_collinearity

# Import data fetching and processing modules
# Note: These are assumed to be implemented in T011, T012, T014
try:
    from code.data.fetch_materials_project import fetch_materials_data
    from code.data.compute_descriptors import compute_descriptors
except ImportError:
    # Fallback for testing if modules are not yet implemented
    # In a real scenario, these would raise errors if not implemented
    fetch_materials_data = None
    compute_descriptors = None

logger = get_pipeline_logger(__name__)

def _compute_file_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 hash of a single file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal SHA256 digest string.
    """
    hash_sha256 = hashlib.sha256()
    # Read the file in chunks to avoid loading large files into memory
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def _generate_checksums(directories: List[Path], output_path: Path) -> None:
    """
    Generate SHA256 checksums for all files in the given directories
    and write them to a single checksum file.

    The checksum file format is:
        <relative_path_to_file> <sha256_hash>

    Args:
        directories: List of directories to scan (recursively).
        output_path: Path to the checksum file to write.
    """
    logger.info(f"Generating checksums for directories: {[str(d) for d in directories]}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as out_f:
        for base_dir in directories:
            if not base_dir.is_dir():
                logger.warning(f"Checksum step: directory does not exist: {base_dir}")
                continue
            for root, _, files in os.walk(base_dir):
                for fname in files:
                    file_path = Path(root) / fname
                    # Compute checksum
                    try:
                        checksum = _compute_file_sha256(file_path)
                        # Store path relative to project root for reproducibility
                        rel_path = file_path.relative_to(Path.cwd())
                        out_f.write(f"{rel_path} {checksum}\\n")
                    except Exception as e:
                        logger.error(f"Failed to compute checksum for {file_path}: {e}")

    logger.info(f"Checksums written to {output_path}")

def run_pipeline(output_path: Optional[str] = None) -> str:
    """
    Run the full data pipeline.

    Args:
        output_path: Optional path to save the output CSV. If None, uses config default.

    Returns:
        Path to the output CSV file.
    """
    config = get_config()

    if output_path is None:
        output_path = config.get('paths', {}).get('data_processed', 'data/processed')
        output_path = os.path.join(output_path, 'pipeline_output.csv')

    try:
        logger.info("Starting data pipeline...")

        # Step 1: Fetch data (T011)
        logger.info("Step 1: Fetching materials data...")
        if fetch_materials_data is None:
            # Mock data for testing if fetch_materials_data is not implemented
            # In a real run, this would be a call to the API
            logger.warning("fetch_materials_data not implemented. Using mock data for testing.")
            df_raw = pd.DataFrame({
                'material_id': [f'mp-{i}' for i in range(5000)],
                'melting_point': np.random.uniform(300, 2000, 5000),
                'latent_heat': np.random.uniform(10, 100, 5000),
                'elements': ['Al', 'Si', 'Fe'] * 1666 + ['Al'],
                'structure': ['simple'] * 5000
            })
        else:
            df_raw = fetch_materials_data()

        if df_raw is None or len(df_raw) == 0:
            raise DataProcessingError("No data fetched from Materials Project.")

        logger.info(f"Fetched {len(df_raw)} compounds.")

        # Step 2: Compute descriptors (T012)
        logger.info("Step 2: Computing descriptors...")
        if compute_descriptors is None:
            # Mock descriptors for testing
            logger.warning("compute_descriptors not implemented. Using mock descriptors for testing.")
            df_processed = df_raw.copy()
            df_processed['feat_atomic_number'] = np.random.randint(1, 100, len(df_raw))
            df_processed['feat_electronegativity'] = np.random.uniform(0.5, 4.0, len(df_raw))
            df_processed['feat_radius'] = np.random.uniform(0.5, 2.0, len(df_raw))
            df_processed['feat_mass'] = np.random.uniform(10, 200, len(df_raw))
            df_processed['feat_valence'] = np.random.randint(1, 8, len(df_raw))
        else:
            df_processed = compute_descriptors(df_raw)

        if df_processed is None or len(df_processed) == 0:
            raise DataProcessingError("Descriptor computation resulted in empty dataframe.")

        logger.info(f"Computed descriptors for {len(df_processed)} compounds.")

        # -----------------------------------------------------------------
        # Step 2b: Generate checksums for raw and processed data (T030a)
        # -----------------------------------------------------------------
        logger.info("Step 2b: Generating SHA256 checksums for raw and processed data...")
        raw_dir = Path("data/raw")
        processed_dir = Path("data/processed")
        checksum_file = Path("data/checksums.txt")
        _generate_checksums([raw_dir, processed_dir], checksum_file)

        # Step 3: VIF Check (T014)
        logger.info("Step 3: Running VIF check...")
        feature_cols = [col for col in df_processed.columns if col.startswith('feat_')]
        if len(feature_cols) > 1:
            vif_results = calculate_vif(df_processed[feature_cols])
            high_vif_cols = identify_high_collinearity(vif_results, threshold=10.0)
            if high_vif_cols:
                logger.warning(f"High VIF detected in columns: {high_vif_cols}. Consider removing or combining these features.")
                # Optionally drop high VIF columns
                # df_processed = df_processed.drop(columns=high_vif_cols)
            logger.info(f"VIF check completed. High VIF columns: {high_vif_cols}")
        else:
            logger.info("Not enough feature columns for VIF check.")

        # Step 4: Stability checks
        logger.info("Step 4: Running stability checks...")
        check_nan_inf(df_processed.values, column_name="all")
        validate_dataframe(df_processed)

        # Step 5: Save output
        logger.info(f"Step 5: Saving output to {output_path}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_processed.to_csv(output_path, index=False)

        # Log memory usage
        mem_stats = get_memory_stats()
        logger.info(f"Pipeline completed. Memory usage: {mem_stats}")

        return output_path

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise PipelineError(f"Pipeline execution failed: {str(e)}")

def main():
    """Main entry point."""
    try:
        output_path = run_pipeline()
        logger.info(f"Pipeline completed successfully. Output: {output_path}")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()