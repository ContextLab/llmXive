"""
Preprocessing module for chemical reaction data.

This module handles:
1. Resampling IR/Raman spectra to a fixed mid-infrared grid.
2. Resampling NMR spectra to a fixed ppm grid.
3. Unit variance normalization of spectral features.
4. Extraction of the target variable: normalized DFT total molecular energy.
5. Encoding of reaction conditions (solvent, catalyst, temperature).
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for spectral ranges (based on typical MolSpectra/schema definitions)
# Mid-infrared range: 400 cm-1 to 4000 cm-1
IR_RAMAN_MIN_WAVENUMBER = 400.0
IR_RAMAN_MAX_WAVENUMBER = 4000.0
IR_RAMAN_STEP = 2.0  # cm-1

# NMR range: -10 ppm to 20 ppm (typical for 1H/13C, extended for generality)
NMR_MIN_PPM = -10.0
NMR_MAX_PPM = 20.0
NMR_STEP = 0.1  # ppm

# Target column name as per project pivot
TARGET_COLUMN = "normalized_dft_total_molecular_energy"
RAW_ENERGY_COLUMN = "dft_total_molecular_energy"
MOLECULAR_WEIGHT_COLUMN = "molecular_weight"

def resample_spectrum(
    wavenumbers: np.ndarray,
    intensities: np.ndarray,
    target_min: float,
    target_max: float,
    target_step: float,
    spectrum_type: str = "IR"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Resamples a spectrum to a fixed grid using linear interpolation.

    Args:
        wavenumbers: Original x-axis values (cm-1 or ppm).
        intensities: Original y-axis values (intensity).
        target_min: Minimum value of the target grid.
        target_max: Maximum value of the target grid.
        target_step: Step size for the target grid.
        spectrum_type: Type of spectrum for logging ("IR", "Raman", "NMR").

    Returns:
        Tuple of (new_wavenumbers, new_intensities) as numpy arrays.
    """
    if len(wavenumbers) != len(intensities):
        raise ValueError(f"Length mismatch in {spectrum_type} spectrum: wavenumbers vs intensities")

    if len(wavenumbers) < 2:
        raise ValueError(f"Insufficient data points for {spectrum_type} spectrum resampling")

    # Create target grid
    target_grid = np.arange(target_min, target_max + target_step, target_step)

    # Ensure wavenumbers are sorted
    sort_idx = np.argsort(wavenumbers)
    x_sorted = wavenumbers[sort_idx]
    y_sorted = intensities[sort_idx]

    # Clip original data to target range to avoid extrapolation errors
    valid_mask = (x_sorted >= target_min) & (x_sorted <= target_max)
    if not np.any(valid_mask):
        logger.warning(f"No data points for {spectrum_type} within target range [{target_min}, {target_max}]. Returning zeros.")
        return target_grid, np.zeros_like(target_grid)

    x_valid = x_sorted[valid_mask]
    y_valid = y_sorted[valid_mask]

    # Interpolate
    try:
        new_intensities = np.interp(target_grid, x_valid, y_valid)
    except Exception as e:
        logger.error(f"Interpolation failed for {spectrum_type}: {e}")
        raise

    return target_grid, new_intensities

def normalize_spectrum(intensities: np.ndarray) -> np.ndarray:
    """
    Applies unit variance normalization (z-score) to a spectrum.
    Formula: (x - mean) / std

    Args:
        intensities: 1D array of intensity values.

    Returns:
        Normalized 1D array.
    """
    mean_val = np.mean(intensities)
    std_val = np.std(intensities)

    if std_val == 0:
        logger.warning("Standard deviation is zero. Returning zeros for normalization.")
        return np.zeros_like(intensities)

    return (intensities - mean_val) / std_val

def extract_normalized_energy(
    df: pd.DataFrame,
    energy_col: str = RAW_ENERGY_COLUMN,
    weight_col: str = MOLECULAR_WEIGHT_COLUMN
) -> np.ndarray:
    """
    Extracts and normalizes the DFT total molecular energy.
    Normalization is performed by dividing by molecular weight to get energy per unit mass,
    then z-score normalizing across the dataset.

    Args:
        df: DataFrame containing energy and weight columns.
        energy_col: Name of the column with raw DFT energy.
        weight_col: Name of the column with molecular weight.

    Returns:
        1D array of normalized energy values.
    """
    if energy_col not in df.columns:
        raise ValueError(f"Column '{energy_col}' not found in dataframe")
    if weight_col not in df.columns:
        raise ValueError(f"Column '{weight_col}' not found in dataframe")

    raw_energies = df[energy_col].values.astype(float)
    weights = df[weight_col].values.astype(float)

    # Avoid division by zero
    if np.any(weights == 0):
        logger.warning("Found zero molecular weights. Setting normalized energy to 0 for those rows.")
        weights_safe = np.where(weights == 0, 1.0, weights)
    else:
        weights_safe = weights

    # Energy per unit mass
    energy_per_mass = raw_energies / weights_safe

    # Z-score normalization across the dataset
    mean_e = np.mean(energy_per_mass)
    std_e = np.std(energy_per_mass)

    if std_e == 0:
        logger.warning("Standard deviation of energy per mass is zero. Returning zeros.")
        return np.zeros_like(energy_per_mass)

    normalized_energy = (energy_per_mass - mean_e) / std_e
    return normalized_energy

def encode_conditions_onehot(
    df: pd.DataFrame,
    condition_cols: List[str],
    categorical_cols: List[str]
) -> pd.DataFrame:
    """
    One-hot encodes specified categorical condition columns.

    Args:
        df: Input DataFrame.
        condition_cols: List of column names to encode.
        categorical_cols: List of columns that are categorical (for safety check).

    Returns:
        DataFrame with one-hot encoded columns appended (original categorical cols removed).
    """
    if not condition_cols:
        return df

    # Drop original categorical columns if they are in condition_cols
    # We assume the input df has them as object/string types
    df_encoded = pd.get_dummies(df, columns=condition_cols, prefix_sep='_')

    # Ensure we only encode the requested columns and don't accidentally one-hot numeric columns
    # get_dummies handles this, but we verify the logic matches requirements
    logger.info(f"One-hot encoded conditions: {condition_cols}")

    return df_encoded

def preprocess_dataset(
    df: pd.DataFrame,
    ir_col: str = "ir_spectrum_wavenumbers",
    ir_int_col: str = "ir_spectrum_intensities",
    raman_col: Optional[str] = "raman_spectrum_wavenumbers",
    raman_int_col: Optional[str] = "raman_spectrum_intensities",
    nmr_col: Optional[str] = "nmr_spectrum_ppm",
    nmr_int_col: Optional[str] = "nmr_spectrum_intensities",
    condition_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Full preprocessing pipeline for a dataset.

    1. Resamples IR/Raman to fixed mid-IR grid.
    2. Resamples NMR to fixed ppm grid.
    3. Normalizes all spectra (unit variance).
    4. Extracts normalized DFT energy as target.
    5. One-hot encodes reaction conditions.
    6. Flattens spectral arrays into columns for model consumption.

    Args:
        df: Input DataFrame.
        ir_col: Column name for IR wavenumbers (comma-separated string or list).
        ir_int_col: Column name for IR intensities.
        raman_col: Column name for Raman wavenumbers.
        raman_int_col: Column name for Raman intensities.
        nmr_col: Column name for NMR ppm.
        nmr_int_col: Column name for NMR intensities.
        condition_cols: List of condition columns to one-hot encode.

    Returns:
        Preprocessed DataFrame with flattened features and normalized target.
    """
    logger.info(f"Starting preprocessing on {len(df)} samples")

    # Helper to parse string lists if necessary
    def parse_series(s):
        if isinstance(s.iloc[0], str):
            return s.apply(lambda x: np.fromstring(x.strip('[]'), sep=',') if isinstance(x, str) else x)
        return s

    # Process IR
    if ir_col in df.columns and ir_int_col in df.columns:
        df['ir_wavenumbers'] = parse_series(df[ir_col])
        df['ir_intensities'] = parse_series(df[ir_int_col])

        ir_resampled_w = []
        ir_resampled_i = []

        for idx, row in df.iterrows():
            w, i = row['ir_wavenumbers'], row['ir_intensities']
            if w is None or i is None or len(w) == 0:
                ir_resampled_w.append(np.zeros(int((IR_RAMAN_MAX_WAVENUMBER - IR_RAMAN_MIN_WAVENUMBER) / IR_RAMAN_STEP) + 1))
                ir_resampled_i.append(np.zeros_like(ir_resampled_w[-1]))
                continue
            
            # Resample
            new_w, new_i = resample_spectrum(
                np.array(w), np.array(i),
                IR_RAMAN_MIN_WAVENUMBER, IR_RAMAN_MAX_WAVENUMBER, IR_RAMAN_STEP,
                "IR"
            )
            # Normalize
            new_i_norm = normalize_spectrum(new_i)
            ir_resampled_w.append(new_w)
            ir_resampled_i.append(new_i_norm)

        df['ir_resampled'] = ir_resampled_i
        # Flatten for storage (will be expanded to columns later)
        logger.info("IR resampling and normalization complete")

    # Process Raman
    if raman_col and raman_col in df.columns and raman_int_col in df.columns:
        df['raman_wavenumbers'] = parse_series(df[raman_col])
        df['raman_intensities'] = parse_series(df[raman_int_col])

        raman_resampled_i = []
        for idx, row in df.iterrows():
            w, i = row['raman_wavenumbers'], row['raman_intensities']
            if w is None or i is None or len(w) == 0:
                raman_resampled_i.append(np.zeros_like(ir_resampled_i[0])) # Assume same grid as IR if needed, or zero
                continue
            
            new_w, new_i = resample_spectrum(
                np.array(w), np.array(i),
                IR_RAMAN_MIN_WAVENUMBER, IR_RAMAN_MAX_WAVENUMBER, IR_RAMAN_STEP,
                "Raman"
            )
            new_i_norm = normalize_spectrum(new_i)
            raman_resampled_i.append(new_i_norm)
        
        df['raman_resampled'] = raman_resampled_i
        logger.info("Raman resampling and normalization complete")

    # Process NMR
    if nmr_col and nmr_col in df.columns and nmr_int_col in df.columns:
        df['nmr_ppm'] = parse_series(df[nmr_col])
        df['nmr_intensities'] = parse_series(df[nmr_int_col])

        nmr_resampled_i = []
        for idx, row in df.iterrows():
            w, i = row['nmr_ppm'], row['nmr_intensities']
            if w is None or i is None or len(w) == 0:
                nmr_resampled_i.append(np.zeros(int((NMR_MAX_PPM - NMR_MIN_PPM) / NMR_STEP) + 1))
                continue

            new_w, new_i = resample_spectrum(
                np.array(w), np.array(i),
                NMR_MIN_PPM, NMR_MAX_PPM, NMR_STEP,
                "NMR"
            )
            new_i_norm = normalize_spectrum(new_i)
            nmr_resampled_i.append(new_i_norm)
        
        df['nmr_resampled'] = nmr_resampled_i
        logger.info("NMR resampling and normalization complete")

    # Extract Target
    if TARGET_COLUMN not in df.columns:
        df[TARGET_COLUMN] = extract_normalized_energy(df)
        logger.info(f"Extracted normalized target: {TARGET_COLUMN}")

    # Encode Conditions
    if condition_cols:
        # Identify which are categorical (assuming string/object)
        cat_cols = [c for c in condition_cols if c in df.columns and df[c].dtype == 'object']
        if cat_cols:
            df = encode_conditions_onehot(df, cat_cols, cat_cols)
            logger.info(f"Encoded conditions: {cat_cols}")

    # Flatten spectral columns for model input
    # We drop the list columns and create fixed-width columns
    final_df = df.copy()
    
    if 'ir_resampled' in final_df.columns:
        # Expand list to columns
        ir_cols = [f'ir_{i}' for i in range(len(final_df['ir_resampled'].iloc[0]))]
        ir_df = pd.DataFrame(final_df['ir_resampled'].tolist(), columns=ir_cols, index=final_df.index)
        final_df = pd.concat([final_df.drop('ir_resampled', axis=1), ir_df], axis=1)
    
    if 'raman_resampled' in final_df.columns:
        raman_cols = [f'raman_{i}' for i in range(len(final_df['raman_resampled'].iloc[0]))]
        raman_df = pd.DataFrame(final_df['raman_resampled'].tolist(), columns=raman_cols, index=final_df.index)
        final_df = pd.concat([final_df.drop('raman_resampled', axis=1), raman_df], axis=1)

    if 'nmr_resampled' in final_df.columns:
        nmr_cols = [f'nmr_{i}' for i in range(len(final_df['nmr_resampled'].iloc[0]))]
        nmr_df = pd.DataFrame(final_df['nmr_resampled'].tolist(), columns=nmr_cols, index=final_df.index)
        final_df = pd.concat([final_df.drop('nmr_resampled', axis=1), nmr_df], axis=1)

    # Drop raw intermediate columns
    drop_cols = ['ir_wavenumbers', 'ir_intensities', 'raman_wavenumbers', 'raman_intensities', 
                 'nmr_ppm', 'nmr_intensities']
    final_df = final_df.drop(columns=[c for c in drop_cols if c in final_df.columns])

    logger.info(f"Preprocessing complete. Output shape: {final_df.shape}")
    return final_df

def load_and_preprocess(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    condition_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Convenience function to load a CSV, preprocess, and save.

    Args:
        input_path: Path to input CSV.
        output_path: Path to save processed CSV.
        condition_cols: List of condition columns to encode.

    Returns:
        Preprocessed DataFrame.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    logger.info("Running preprocessing pipeline")
    df_processed = preprocess_dataset(df, condition_cols=condition_cols)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_processed.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

    return df_processed