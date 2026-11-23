import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root setup
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import ensure_data_directories, get_processed_data_path, get_raw_data_path
from utils.io import load_csv, save_csv, load_and_filter_dataset
from utils.dedup import deduplicate_compositions, get_deduplication_stats
from features.descriptors import apply_descriptors_to_dataframe
from utils.provenance import register_source, update_source_checksum, add_processing_step, load_provenance, save_provenance

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    T016 Implementation: Generate data/processed/engineered_dataset.csv
    
    This script orchestrates the pipeline to:
    1. Load raw data from data/raw/ (Zenodo or MP)
    2. Deduplicate compositions
    3. Filter by phase label (if available)
    4. Compute atomic descriptors
    5. Save the final engineered dataset
    6. Update provenance
    """
    ensure_data_directories()
    
    raw_dir = get_raw_data_path()
    processed_path = get_processed_data_path()
    
    # Determine input file
    # We expect the ingestion pipeline (T013) to have placed a merged CSV here
    # If not, we look for specific source files
    input_candidates = [
        raw_dir / "merged_dataset.csv",
        raw_dir / "science_advances.csv",
        raw_dir / "materials_project.csv"
    ]
    
    input_file = None
    for candidate in input_candidates:
        if candidate.exists():
            input_file = candidate
            break
    
    if not input_file:
        raise FileNotFoundError(
            f"No raw input dataset found in {raw_dir}. "
            "Please run the ingestion pipeline (T013) first to generate raw data."
        )
    
    logger.info(f"Loading raw data from: {input_file}")
    df = load_csv(str(input_file))
    
    if df.empty:
        raise ValueError("Loaded dataset is empty. Cannot proceed with engineering.")
    
    logger.info(f"Loaded {len(df)} records. Starting deduplication...")
    
    # Deduplicate
    df_dedup, stats = deduplicate_compositions(df)
    logger.info(f"Deduplication stats: {stats}")
    
    # Filter by phase label (T014 logic)
    # Assuming 'phase_label' column exists or similar
    if 'phase_label' in df_dedup.columns:
        logger.info("Filtering by definitive phase labels...")
        df_filtered = load_and_filter_dataset(df_dedup)
        if len(df_filtered) < len(df_dedup):
            logger.warning(f"Filtered out {len(df_dedup) - len(df_filtered)} records without phase labels.")
        df_dedup = df_filtered
    else:
        logger.warning("No 'phase_label' column found. Skipping phase filter step.")
    
    # Compute Descriptors (T012 logic)
    logger.info("Computing atomic descriptors...")
    df_engineered = apply_descriptors_to_dataframe(df_dedup)
    
    # Verify completeness (T017 logic - basic check)
    required_descriptors = [
        'atomic_radius', 'electronegativity', 'valence_electron_concentration',
        'atomic_size_mismatch', 'mixing_enthalpy', 'atomic_size_difference',
        'valence_electron_size_mismatch', 'electron_atom_ratio', 
        'miedema_heat_of_formation', 'atomic_packing_factor'
    ]
    
    missing_cols = [col for col in required_descriptors if col not in df_engineered.columns]
    if missing_cols:
        raise RuntimeError(f"Missing required descriptor columns: {missing_cols}")
    
    # Check for NaNs in critical descriptor columns
    null_counts = df_engineered[required_descriptors].isnull().sum()
    total_nulls = null_counts.sum()
    if total_nulls > 0:
        logger.warning(f"Found {total_nulls} null values in descriptor columns. "
                     "Proceeding, but downstream models may need imputation.")
    
    # Save to processed
    output_file = str(processed_path / "engineered_dataset.csv")
    logger.info(f"Saving engineered dataset to: {output_file}")
    save_csv(df_engineered, output_file)
    
    # Update Provenance
    provenance_path = project_root / "data" / "provenance.json"
    if not provenance_path.exists():
        # Initialize if missing
        save_provenance([], str(provenance_path))
    
    provenance = load_provenance(str(provenance_path))
    
    # Register input source
    register_source(provenance, "raw_input", str(input_file))
    
    # Add processing step
    add_processing_step(
        provenance,
        step_name="T016_Generate_Engineered_Dataset",
        description="Deduplication, phase filtering, and descriptor computation",
        output_file=output_file,
        parameters={
            "dedup_stats": stats,
            "descriptor_columns": required_descriptors
        }
    )
    
    # Update checksums
    update_source_checksum(provenance, str(input_file))
    update_source_checksum(provenance, output_file)
    
    save_provenance(provenance, str(provenance_path))
    
    logger.info("T016 Complete: Engineered dataset generated successfully.")
    return df_engineered

if __name__ == "__main__":
    main()
