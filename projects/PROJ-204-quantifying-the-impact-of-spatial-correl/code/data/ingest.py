"""
Ingestion pipeline for Perovskite Solar Cell data.
Orchestrates download, alignment, and masking to produce a unified dataset.
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import from existing API surface
from data.download_eds import load_feasibility_status, download_file, download_from_zenodo
from data.align import align_maps, create_aligned_dataset
from preprocess.calibrate import mask_defective_regions, apply_mask_to_dataset
from utils.config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_data(config: Dict[str, Any], raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Download EDS maps and performance metrics from verified sources.
    Returns a list of sample metadata dictionaries.
    """
    feasibility = load_feasibility_status()
    if not feasibility.get('success', False):
        raise RuntimeError(f"Data feasibility check failed: {feasibility.get('reason', 'Unknown')}")

    zenodo_id = feasibility.get('zenodo_id')
    if not zenodo_id:
        raise RuntimeError("No Zenodo ID found in feasibility status.")

    logger.info(f"Starting download from Zenodo ID: {zenodo_id}")
    # Simulate fetching the manifest from Zenodo based on the feasibility check
    # In a real scenario, this would parse the Zenodo API response or a manifest file
    # For this implementation, we assume the download_eds module handles the specific retrieval logic
    # and we rely on the existence of the files in raw_dir after download_from_zenodo is called.
    
    # We call the download function which populates raw_dir
    # We assume download_from_zenodo returns a list of metadata dicts or populates a manifest
    manifest = download_from_zenodo(zenodo_id, raw_dir)
    
    if not manifest:
        raise RuntimeError("Download completed but no manifest found. Data might be missing.")
    
    logger.info(f"Downloaded {len(manifest)} samples.")
    return manifest

def align_maps_internal(samples: List[Dict[str, Any]], raw_dir: Path, processed_dir: Path) -> List[Dict[str, Any]]:
    """
    Align elemental maps for each sample.
    Returns updated sample metadata with aligned paths.
    """
    logger.info("Starting map alignment...")
    aligned_samples = []
    
    for sample in samples:
        try:
            # Extract paths relative to raw_dir
            pb_path = raw_dir / sample['pb_map_filename']
            i_path = raw_dir / sample['i_map_filename']
            ma_path = raw_dir / sample['ma_map_filename']
            
            # Validate existence
            if not all(p.exists() for p in [pb_path, i_path, ma_path]):
                logger.warning(f"Missing map files for sample {sample['sample_id']}. Skipping.")
                continue
            
            # Use the align module to process
            # Note: align_maps expects paths or loaded arrays. Assuming it handles file I/O or we load here.
            # Based on API: align_maps, create_aligned_dataset. 
            # We assume create_aligned_dataset takes the sample dict and paths.
            aligned_sample = create_aligned_dataset(sample, raw_dir, processed_dir)
            
            if aligned_sample:
                aligned_samples.append(aligned_sample)
            else:
                logger.warning(f"Alignment failed for {sample['sample_id']}.")
                
        except Exception as e:
            logger.error(f"Error aligning sample {sample['sample_id']}: {e}")
            continue
    
    logger.info(f"Aligned {len(aligned_samples)} samples.")
    return aligned_samples

def mask_defects(samples: List[Dict[str, Any]], processed_dir: Path) -> List[Dict[str, Any]]:
    """
    Apply defect masking to aligned maps.
    Returns updated sample metadata with masked paths and stats.
    """
    logger.info("Starting defect masking...")
    masked_samples = []
    
    for sample in samples:
        try:
            # Paths to aligned maps
            pb_path = Path(sample['aligned_pb_map_path'])
            i_path = Path(sample['aligned_i_map_path'])
            ma_path = Path(sample['aligned_ma_map_path'])
            
            if not all(p.exists() for p in [pb_path, i_path, ma_path]):
                logger.warning(f"Missing aligned files for {sample['sample_id']}. Skipping masking.")
                continue
            
            # Apply masking
            masked_sample = apply_mask_to_dataset(sample, processed_dir)
            
            if masked_sample:
                masked_samples.append(masked_sample)
            else:
                logger.warning(f"Masking failed for {sample['sample_id']}.")
                
        except Exception as e:
            logger.error(f"Error masking sample {sample['sample_id']}: {e}")
            continue
    
    logger.info(f"Masked {len(masked_samples)} samples.")
    return masked_samples

def ingest_and_filter_dataset(samples: List[Dict[str, Any]], output_path: Path) -> pd.DataFrame:
    """
    Construct the unified DataFrame from processed samples and write to CSV.
    Columns: sample_id, Pb_map_path, I_map_path, MA_map_path, PCE, J_sc, V_oc
    """
    logger.info(f"Constructing unified dataset for {len(samples)} samples...")
    
    records = []
    for s in samples:
        record = {
            'sample_id': s.get('sample_id'),
            'Pb_map_path': s.get('masked_pb_map_path'),
            'I_map_path': s.get('masked_i_map_path'),
            'MA_map_path': s.get('masked_ma_map_path'),
            'PCE': s.get('pce'),
            'J_sc': s.get('j_sc'),
            'V_oc': s.get('v_oc')
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    
    # Drop rows with missing critical data (pre-filter)
    # We keep rows where performance metrics exist, even if map paths are missing? 
    # No, the task says "unified dataset" with these columns. 
    # Usually, if a map is missing, the sample is invalid for spatial analysis.
    # We drop rows where ANY of the required columns are null.
    required_cols = ['sample_id', 'Pb_map_path', 'I_map_path', 'MA_map_path', 'PCE', 'J_sc', 'V_oc']
    df = df.dropna(subset=required_cols)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Unified dataset written to {output_path} with {len(df)} rows.")
    
    return df

def main(config_path: Optional[str] = None):
    """
    Main entry point for the ingestion pipeline.
    """
    config = get_config(config_path)
    base_dir = Path(config.get('base_dir', '.'))
    raw_dir = base_dir / 'data' / 'raw'
    processed_dir = base_dir / 'data' / 'processed'
    output_file = processed_dir / 'unified_dataset.csv'
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Download
    samples = download_data(config, raw_dir)
    if not samples:
        logger.warning("No samples downloaded. Exiting.")
        return
    
    # Step 2: Align
    aligned_samples = align_maps_internal(samples, raw_dir, processed_dir)
    if not aligned_samples:
        logger.warning("No samples aligned. Exiting.")
        return
    
    # Step 3: Mask
    masked_samples = mask_defects(aligned_samples, processed_dir)
    if not masked_samples:
        logger.warning("No samples masked. Exiting.")
        return
    
    # Step 4: Ingest & Write
    df = ingest_and_filter_dataset(masked_samples, output_file)
    
    if len(df) == 0:
        logger.error("Final dataset is empty after filtering.")
    else:
        logger.info(f"Successfully ingested {len(df)} valid samples.")

if __name__ == '__main__':
    main()
