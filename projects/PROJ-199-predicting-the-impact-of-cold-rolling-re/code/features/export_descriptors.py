"""
Export calculated texture descriptors to CSV.

This module loads processed EBSD data, calculates descriptors using the
feature extraction logic, validates mass balance per T019 requirements,
and exports the final dataset to `data/processed/descriptors.csv`.

It ensures that only valid samples (passing mass balance checks) are
included in the final output, linking them to their original sample IDs.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import from sibling modules based on provided API surface
from code.utils.logging import get_logger
from code.data.models import TextureDescriptor, MaterialType
from code.features.descriptors import calculate_descriptors
from code.features.mass_balance import validate_descriptor_mass_balance
from code.data.preprocess import load_ebsd_data

logger = get_logger(__name__)

def load_processed_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load processed EBSD data from the interim or processed directory.

    Args:
        input_path: Optional path to the input parquet file. Defaults to
                    `data/processed/cleaned_ebsd.parquet` if not provided.

    Returns:
        A pandas DataFrame containing the cleaned EBSD data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or lacks required columns.
    """
    if input_path is None:
        input_path = "data/processed/cleaned_ebsd.parquet"

    path = Path(input_path)
    if not path.exists():
        # Try relative to project root if absolute path not provided
        if not path.is_absolute():
            project_root = Path.cwd()
            full_path = project_root / input_path
            if full_path.exists():
                path = full_path
            else:
                raise FileNotFoundError(f"Input file not found: {input_path}")
        else:
            raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading processed data from {path}")
    df = pd.read_parquet(path)

    if df.empty:
        raise ValueError(f"Input file {path} is empty.")

    required_cols = ['sample_id', 'material', 'reduction', 'phi1', 'Phi', 'phi2', 'confidence']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")

    return df

def calculate_and_export_descriptors(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate descriptors for all samples and export to CSV.

    This function:
    1. Loads processed EBSD data.
    2. Groups data by sample_id.
    3. Calculates texture descriptors (Volume Fractions, Texture Index) for each sample.
    4. Validates mass balance for each sample (T019 logic).
    5. Filters out samples that fail mass balance validation.
    6. Exports the valid descriptors to a CSV file linked to sample IDs.

    Args:
        input_path: Path to the input cleaned EBSD parquet file.
        output_path: Path for the output descriptors CSV. Defaults to
                     `data/processed/descriptors.csv`.

    Returns:
        The DataFrame of exported descriptors.
    """
    if output_path is None:
        output_path = "data/processed/descriptors.csv"

    # Ensure output directory exists
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_processed_data(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Group by sample_id to calculate descriptors per sample
    # We assume each row in the input is an orientation point within a sample.
    # We need to aggregate these into a single descriptor row per sample.
    # However, `calculate_descriptors` in `code/features/descriptors.py`
    # expects a list of orientations (or a DataFrame with Euler angles)
    # and returns a single descriptor object for that set.

    sample_ids = df['sample_id'].unique()
    logger.info(f"Found {len(sample_ids)} unique samples.")

    results = []
    excluded_samples = []

    for sample_id in sample_ids:
        sample_df = df[df['sample_id'] == sample_id]
        
        # Extract material and reduction for this sample (assuming constant per sample)
        material_str = sample_df['material'].iloc[0]
        reduction_val = sample_df['reduction'].iloc[0]

        try:
            material = MaterialType(material_str)
        except ValueError:
            logger.warning(f"Unknown material '{material_str}' for sample {sample_id}. Skipping.")
            excluded_samples.append((sample_id, "Unknown material"))
            continue

        # Extract Euler angles
        euler_angles = sample_df[['phi1', 'Phi', 'phi2']].values.tolist()

        # Calculate descriptors
        # The `calculate_descriptors` function from `code/features/descriptors.py`
        # should handle the calculation of volume fractions and texture index.
        # We assume it returns a dictionary or a TextureDescriptor object.
        try:
            descriptor = calculate_descriptors(
                orientations=euler_angles,
                material=material,
                reduction=reduction_val
            )
            
            # Ensure descriptor is a dict or convert to dict
            if hasattr(descriptor, 'model_dump'):
                desc_dict = descriptor.model_dump()
            elif isinstance(descriptor, dict):
                desc_dict = descriptor
            else:
                # Fallback if it's an object without model_dump
                desc_dict = {
                    'brass': getattr(descriptor, 'brass_fraction', 0.0),
                    'copper': getattr(descriptor, 'copper_fraction', 0.0),
                    's': getattr(descriptor, 's_fraction', 0.0),
                    'goss': getattr(descriptor, 'goss_fraction', 0.0),
                    'texture_index': getattr(descriptor, 'texture_index', 0.0),
                    'random_fraction': getattr(descriptor, 'random_fraction', 0.0)
                }

            # Validate mass balance (T019 requirement)
            # We check if the sum of components + random is close to 1.0
            total = (desc_dict.get('brass', 0.0) + 
                     desc_dict.get('copper', 0.0) + 
                     desc_dict.get('s', 0.0) + 
                     desc_dict.get('goss', 0.0) + 
                     desc_dict.get('random_fraction', 0.0))
            
            is_valid, message = validate_descriptor_mass_balance(
                brass=desc_dict.get('brass', 0.0),
                copper=desc_dict.get('copper', 0.0),
                s=desc_dict.get('s', 0.0),
                goss=desc_dict.get('goss', 0.0),
                random_fraction=desc_dict.get('random_fraction', 0.0)
            )

            if not is_valid:
                logger.warning(f"Sample {sample_id} failed mass balance check: {message}. Excluding.")
                excluded_samples.append((sample_id, message))
                continue

            # Add metadata
            row = {
                'sample_id': sample_id,
                'material': material_str,
                'reduction': reduction_val,
                **desc_dict
            }
            results.append(row)

        except Exception as e:
            logger.error(f"Error calculating descriptors for sample {sample_id}: {e}")
            excluded_samples.append((sample_id, str(e)))

    if not results:
        logger.error("No valid samples found to export. Aborting CSV generation.")
        raise RuntimeError("No valid samples found to export. Aborting CSV generation.")

    output_df = pd.DataFrame(results)
    
    # Sort by sample_id for consistency
    output_df = output_df.sort_values('sample_id')

    logger.info(f"Exporting {len(output_df)} valid samples to {output_path}")
    output_df.to_csv(output_path, index=False)

    logger.info(f"Excluded {len(excluded_samples)} samples due to errors or mass balance failure.")
    if excluded_samples:
        logger.debug(f"Excluded samples details: {excluded_samples[:5]}...") # Log first 5

    return output_df

def main():
    """Main entry point for the export script."""
    logging.basicConfig(level=logging.INFO)
    
    input_file = "data/processed/cleaned_ebsd.parquet"
    output_file = "data/processed/descriptors.csv"

    # Check if input exists (it should, from T015)
    if not Path(input_file).exists():
        logger.error(f"Input file {input_file} not found. Please run T015 first.")
        sys.exit(1)

    try:
        df = calculate_and_export_descriptors(input_path=input_file, output_path=output_file)
        logger.info(f"Successfully exported descriptors to {output_file}")
        print(f"Exported {len(df)} rows to {output_file}")
    except Exception as e:
        logger.critical(f"Failed to export descriptors: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
