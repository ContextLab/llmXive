import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

try:
    from config import get_project_root, get_data_path, get_output_path
except ImportError:
    from code.config import get_project_root, get_data_path, get_output_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_output_path() / 'run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_oc20_sample() -> pd.DataFrame:
    """Load the OC20 sample downloaded in T102."""
    path = get_data_path() / 'raw' / 'oc20_sample.parquet'
    if not path.exists():
        raise FileNotFoundError(f"OC20 sample not found at {path}")
    logger.info(f"Loading OC20 sample from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded OC20 sample with shape {df.shape}")
    return df


def load_mp_descriptors() -> Dict[str, Dict[str, Any]]:
    """Load Materials Project descriptors downloaded in T102."""
    path = get_data_path() / 'raw' / 'mp_descriptors.json'
    if not path.exists():
        raise FileNotFoundError(f"MP descriptors not found at {path}")
    logger.info(f"Loading MP descriptors from {path}")
    with open(path, 'r') as f:
        descriptors = json.load(f)
    logger.info(f"Loaded MP descriptors for {len(descriptors)} compositions")
    return descriptors


def extract_descriptors_from_oc20(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract electronic descriptors from OC20 data.
    
    OC20 contains DFT-calculated properties. We extract:
    - d_band_center: d-band center of the surface
    - p_band_center: p-band center of the surface
    - bader_charges: Bader partial charges
    - activation_barrier: computed from reaction energetics
    - reaction_energy: computed from reaction energetics
    """
    df_desc = df.copy()
    
    # Initialize descriptor columns if they don't exist
    if 'd_band_center' not in df_desc.columns:
        df_desc['d_band_center'] = np.nan
    if 'p_band_center' not in df_desc.columns:
        df_desc['p_band_center'] = np.nan
    if 'bader_charges' not in df_desc.columns:
        df_desc['bader_charges'] = np.nan
    if 'activation_barrier' not in df_desc.columns:
        df_desc['activation_barrier'] = np.nan
    if 'reaction_energy' not in df_desc.columns:
        df_desc['reaction_energy'] = np.nan
    
    # Extract from OC20 data if available
    # OC20 may have these as computed properties
    if 'dband_center' in df.columns:
        df_desc['d_band_center'] = df['dband_center']
    if 'pband_center' in df.columns:
        df_desc['p_band_center'] = df['pband_center']
    if 'bader_charge' in df.columns:
        df_desc['bader_charges'] = df['bader_charge']
    if 'activation_energy' in df.columns:
        df_desc['activation_barrier'] = df['activation_energy']
    if 'reaction_energy' in df.columns:
        df_desc['reaction_energy'] = df['reaction_energy']
    
    # Ensure composition and surface_facet exist
    if 'composition' not in df_desc.columns and 'formula' in df.columns:
        df_desc['composition'] = df['formula']
    if 'surface_facet' not in df_desc.columns and 'facet' in df.columns:
        df_desc['surface_facet'] = df['facet']
    
    logger.info(f"Extracted descriptors from OC20 data")
    logger.debug(f"Descriptor columns: {[c for c in df_desc.columns if 'band' in c or 'bader' in c or 'barrier' in c]}")
    
    return df_desc


def merge_mp_descriptors(df_oc20: pd.DataFrame, mp_descriptors: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Merge Materials Project bulk descriptors into OC20 data.
    
    Matches on composition (exact string match).
    """
    df_merged = df_oc20.copy()
    
    # Ensure composition column exists
    if 'composition' not in df_merged.columns:
        logger.warning("composition column not found in OC20 data")
        return df_merged
    
    # Initialize MP descriptor columns
    mp_cols = ['mp_d_band_center', 'mp_p_band_center', 'mp_bader_charges']
    for col in mp_cols:
        if col not in df_merged.columns:
            df_merged[col] = np.nan
    
    # Fill from MP data using exact composition match
    matched_count = 0
    for idx, row in df_merged.iterrows():
        comp = str(row['composition']).strip()
        if comp in mp_descriptors:
            mp_data = mp_descriptors[comp]
            if 'd_band_center' in mp_data:
                df_merged.at[idx, 'mp_d_band_center'] = mp_data['d_band_center']
            if 'p_band_center' in mp_data:
                df_merged.at[idx, 'mp_p_band_center'] = mp_data['p_band_center']
            if 'bader_charges' in mp_data:
                df_merged.at[idx, 'mp_bader_charges'] = mp_data['bader_charges']
            matched_count += 1
    
    logger.info(f"Merged MP descriptors: {matched_count}/{len(df_merged)} entries matched")
    
    return df_merged


def add_synthesis_condition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add synthesis_condition column if not present.
    This is used for alignment in FR-002.
    """
    if 'synthesis_condition' not in df.columns:
        # If not in data, use a default or derive from available info
        if 'reaction_condition' in df.columns:
            df['synthesis_condition'] = df['reaction_condition']
        else:
            # Default to a generic condition
            df['synthesis_condition'] = 'standard'
    return df


def main():
    """Main entry point for descriptor extraction."""
    logger.info("=" * 60)
    logger.info("Starting descriptor extraction (T103 part a)")
    logger.info("=" * 60)
    
    try:
        # Load raw data
        oc20_df = load_oc20_sample()
        mp_descriptors = load_mp_descriptors()
        
        # Extract descriptors from OC20
        df_with_descriptors = extract_descriptors_from_oc20(oc20_df)
        
        # Merge MP descriptors
        df_merged = merge_mp_descriptors(df_with_descriptors, mp_descriptors)
        
        # Add synthesis condition for alignment
        df_final = add_synthesis_condition(df_merged)
        
        # Save intermediate descriptor file
        output_path = get_data_path() / 'processed' / 'descriptors.parquet'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_final.to_parquet(output_path, index=False)
        logger.info(f"Saved extracted descriptors to {output_path}")
        
        logger.info("=" * 60)
        logger.info("Descriptor extraction completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during descriptor extraction: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
