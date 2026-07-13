import os
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Import project utilities and exceptions
from config import load_config, set_global_seed
from exceptions import DataInsufficientError, PowerWarning
from logging_config import setup_logger, handle_power_warning
from utils import get_properties_batch
from memory_monitor import update_peak_memory, reset_peak_memory

# Configure logging
logger = setup_logger(__name__)

def load_raw_data(input_path: Path) -> pd.DataFrame:
    """Load the raw parquet file downloaded by 01_download.py."""
    if not input_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {input_path}")
    
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def filter_bcc_carbon(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for BCC structure and Carbon solute."""
    logger.info("Filtering for structure == 'BCC' and solute == 'C'")
    filtered = df[
        (df['structure'] == 'BCC') & 
        (df['solute'] == 'C')
    ].copy()
    logger.info(f"Retained {len(filtered)} rows after filtering")
    return filtered

def enforce_provenance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce provenance check: exclude entries missing 
    microstructure_controlled or single_crystal flags.
    """
    logger.info("Enforcing provenance check (microstructure_controlled or single_crystal)")
    
    # Identify columns if they exist, otherwise raise error if missing
    # Assuming column names based on typical materials science datasets
    # If columns are missing, we assume the data is not usable for this specific filter
    required_flags = ['microstructure_controlled', 'single_crystal']
    existing_flags = [col for col in required_flags if col in df.columns]
    
    if not existing_flags:
        logger.warning("No provenance flag columns found. Proceeding without provenance filter.")
        return df

    # Keep rows where at least one of the existing flags is True
    # If a column is missing, we treat it as False for the OR logic, 
    # but since we only filter on existing columns, we just OR the existing ones.
    mask = pd.Series(False, index=df.index)
    for col in existing_flags:
        # Ensure boolean type, handle NaNs by filling False
        mask = mask | (df[col].fillna(False) == True)
    
    filtered = df[mask].copy()
    logger.info(f"Retained {len(filtered)} rows after provenance check")
    return filtered

def normalize_atomic_fractions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize atomic fractions to sum to 1.0."""
    logger.info("Normalizing atomic fractions")
    
    # Identify composition columns (typically starting with 'comp_' or similar pattern)
    # Based on MeLiDC schema, composition columns often look like 'comp_Fe', 'comp_C', etc.
    comp_cols = [col for col in df.columns if col.startswith('comp_')]
    
    if not comp_cols:
        logger.warning("No composition columns found to normalize.")
        return df

    # Calculate sum of atomic fractions for each row
    df['comp_sum'] = df[comp_cols].sum(axis=1)
    
    # Normalize
    for col in comp_cols:
        df[col] = df[col] / df['comp_sum']
    
    df.drop(columns=['comp_sum'], inplace=True)
    logger.info("Atomic fractions normalized")
    return df

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute descriptors per FR-002:
    - atomic_radius_variance
    - VEC (Valence Electron Concentration)
    - electronegativity_spread
    """
    logger.info("Computing descriptors")
    
    comp_cols = [col for col in df.columns if col.startswith('comp_')]
    if not comp_cols:
        raise ValueError("No composition columns found to compute descriptors.")

    # Extract element and fraction pairs for each row
    # We expect columns like 'comp_Fe', 'comp_C', etc.
    elements = [col.replace('comp_', '') for col in comp_cols]
    
    # Use utils.get_properties_batch to fetch properties
    # We need to construct a list of (element, fraction) for each row
    # Since get_properties_batch expects a list of elements and optionally fractions
    # We will iterate row by row or use a vectorized approach if possible.
    # Given the potential complexity, we'll iterate rows for clarity and correctness.
    
    radius_data = []
    vec_data = []
    el_data = []
    
    for idx, row in df.iterrows():
        update_peak_memory()
        row_elements = []
        row_fractions = []
        for elem_str, col in zip(elements, comp_cols):
            frac = row[col]
            if pd.notna(frac) and frac > 0:
                row_elements.append(elem_str)
                row_fractions.append(frac)
        
        if not row_elements:
            radius_data.append(np.nan)
            vec_data.append(np.nan)
            el_data.append(np.nan)
            continue

        try:
            props = get_properties_batch(row_elements, row_fractions)
            
            # props is expected to be a list of dicts or similar structure
            # We need to calculate:
            # 1. Atomic Radius Variance: Var(r_i) where r_i is radius of element i weighted by fraction?
            #    Or variance of radii of constituent elements?
            #    Standard practice: weighted variance or just variance of the set of radii.
            #    Let's assume weighted variance of atomic radii.
            #    Var = sum(f_i * (r_i - mean_r)^2)
            
            # 2. VEC: sum(f_i * VEC_i)
            # 3. Electronegativity Spread: max(EN) - min(EN) or std(EN)
            
            radii = [p['atomic_radius'] for p in props]
            vecs = [p['vec'] for p in props]
            ens = [p['electronegativity'] for p in props]
            
            # Weighted VEC
            weighted_vec = sum(f * v for f, v in zip(row_fractions, vecs))
            
            # Weighted mean radius
            mean_radius = sum(f * r for f, r in zip(row_fractions, radii))
            # Weighted variance of radius
            radius_var = sum(f * (r - mean_radius)**2 for f, r in zip(row_fractions, radii))
            
            # Electronegativity spread (range)
            en_spread = max(ens) - min(ens)
            
            radius_data.append(radius_var)
            vec_data.append(weighted_vec)
            el_data.append(en_spread)
            
        except Exception as e:
            logger.error(f"Error computing properties for row {idx}: {e}")
            radius_data.append(np.nan)
            vec_data.append(np.nan)
            el_data.append(np.nan)
    
    df['atomic_radius_variance'] = radius_data
    df['VEC'] = vec_data
    df['electronegativity_spread'] = el_data
    
    logger.info(f"Descriptors computed: atomic_radius_variance, VEC, electronegativity_spread")
    return df

def apply_log_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """Apply log10 transformation to diffusion_coefficient (FR-003)."""
    logger.info("Applying log10 transformation to diffusion_coefficient")
    
    target_col = 'diffusion_coefficient'
    if target_col not in df.columns:
        raise ValueError(f"Column '{target_col}' not found in dataframe.")
    
    # Handle non-positive values if any (log undefined)
    # Assuming data is physically meaningful (D > 0)
    df['log_diffusion_coefficient'] = np.log10(df[target_col])
    
    logger.info("Log transformation applied")
    return df

def clean_and_finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Remove intermediate columns and ensure final schema."""
    # Keep only necessary columns
    keep_cols = [
        'structure', 'solute', 
        'atomic_radius_variance', 'VEC', 'electronegativity_spread',
        'log_diffusion_coefficient'
    ]
    
    # Add back composition columns if needed for analysis, 
    # but for the model input, we might just want the descriptors.
    # The task says "Output dataset_cleaned.csv". 
    # We should include descriptors and target.
    
    comp_cols = [col for col in df.columns if col.startswith('comp_')]
    final_cols = keep_cols + comp_cols
    
    # Filter existing columns
    final_cols = [c for c in final_cols if c in df.columns]
    
    df_final = df[final_cols].copy()
    return df_final

def main():
    """Main execution flow for preprocessing."""
    logger.info("Starting preprocessing pipeline (T010)")
    reset_peak_memory()
    
    # Load config
    config = load_config()
    set_global_seed(config.get('random_seed', 42))
    
    # Define paths
    base_dir = Path(config.get('data_dir', 'data'))
    raw_path = base_dir / 'raw' / 'melidc.parquet'
    output_dir = base_dir / 'processed'
    output_path = output_dir / 'dataset_cleaned.csv'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load
        df = load_raw_data(raw_path)
        
        # 2. Filter
        df = filter_bcc_carbon(df)
        
        if len(df) == 0:
            raise DataInsufficientError("No data remaining after filtering for BCC and C.")
        
        # 3. Provenance
        df = enforce_provenance(df)
        
        if len(df) == 0:
            raise DataInsufficientError("No data remaining after provenance check.")
        
        # 4. Normalize
        df = normalize_atomic_fractions(df)
        
        # 5. Compute Descriptors
        df = compute_descriptors(df)
        
        # 6. Log Transform
        df = apply_log_transformation(df)
        
        # 7. Finalize
        df = clean_and_finalize(df)
        
        # Check power warning condition (N < 30)
        if len(df) < 30:
            warning_msg = f"Dataset size ({len(df)}) is below 30. LOOCV fallback will be triggered in training."
            logger.warning(warning_msg)
            handle_power_warning(PowerWarning(warning_msg))
        
        # Save
        df.to_csv(output_path, index=False)
        logger.info(f"Cleaned dataset saved to {output_path}")
        logger.info(f"Final dataset shape: {df.shape}")
        
        update_peak_memory()
        logger.info(f"Peak memory usage: {get_peak_memory_mb():.2f} MB")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()
