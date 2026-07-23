"""
Preprocessing pipeline for Carbon diffusion in BCC metals.
Implements T010: Filter, compute descriptors, log-transform, and split strategy selection.
"""
import os
import logging
import sys
import json
import re
import math
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import pandas as pd
import numpy as np
from pymatgen.core import Element

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from exceptions import DataInsufficientError, PowerWarning, SHAPError
from logging_config import setup_logger, handle_data_insufficient, handle_power_warning
from utils import get_atomic_radius, get_vec, get_electronegativity, load_config_value
import yaml

logger = setup_logger(__name__)

# Constants
R_GAS = 8.314  # J/(mol·K)

def load_raw_data() -> pd.DataFrame:
    """Load the raw dataset from the downloaded parquet file."""
    raw_path = Path("data/raw/dataset.parquet")
    if not raw_path.exists():
        # Check for the specific path mentioned in the error log
        alt_path = Path("data/raw/dataset.parquet")
        if not alt_path.exists():
            raise DataInsufficientError(f"Raw dataset not found at {raw_path}. Run 01_download.py first.")
        raw_path = alt_path

    logger.info(f"Loading raw data from {raw_path}")
    try:
        df = pd.read_parquet(raw_path)
    except Exception as e:
        raise DataInsufficientError(f"Failed to read parquet file: {e}")

    # Validate required columns
    required_cols = ['structure', 'composition', 'diffusion_coefficient', 'temperature', 'microstructure_controlled', 'single_crystal']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataInsufficientError(f"Missing required columns in raw data: {missing}")

    return df

def parse_composition(comp_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Fe0.8Cr0.2C' into a dict of elements and fractions.
    Handles formats like 'Fe0.8Cr0.2C' or 'Fe:0.8,Cr:0.2,C:1.0' (simplified regex).
    """
    if not isinstance(comp_str, str) or pd.isna(comp_str):
        return {}

    # Normalize: remove spaces
    comp_str = comp_str.replace(" ", "")

    # Regex to match ElementSymbol followed by optional number
    # This handles 'Fe0.8', 'Cr0.2', 'C' (implied 1.0)
    # Note: This assumes the input format is consistent with the dataset.
    # If the dataset uses 'Fe:0.8', we might need to adjust.
    # Let's try a flexible approach: split by element capitals or colons.
    # Pattern: (Element)(Number) or (Element):(Number)
    # We'll assume standard notation: ElementSymbol[Number]
    # e.g., "Fe0.8Cr0.2C" -> Fe:0.8, Cr:0.2, C:1.0

    elements = {}
    # Regex to capture element symbol and optional fraction
    # Matches: Element (1-2 chars) followed by optional digits/dot
    pattern = r'([A-Z][a-z]?)([\d.]+)?'
    matches = re.findall(pattern, comp_str)

    total = 0.0
    for elem, frac in matches:
        if not frac:
            frac = 1.0
        else:
            frac = float(frac)
        elements[elem] = frac
        total += frac

    return elements, total

def filter_bcc_carbon(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for BCC structure and Carbon solute."""
    logger.info("Filtering for BCC structure and Carbon solute...")

    # Filter structure == 'BCC'
    df = df[df['structure'].str.upper() == 'BCC']

    # Filter for Carbon solute.
    # The dataset might have 'solute' column or it might be embedded in composition.
    # T010 description says: "Filter for structure == 'BCC' and solute == 'C'"
    if 'solute' in df.columns:
        df = df[df['solute'].str.upper() == 'C']
    else:
        # Infer from composition if 'solute' column missing
        # Check if 'C' is in the composition string
        df = df[df['composition'].str.contains('C', regex=False, na=False)]

    logger.info(f"Filtered dataset size: {len(df)}")
    return df

def enforce_provenance(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce provenance check: exclude entries missing flags."""
    logger.info("Enforcing provenance checks...")
    initial_count = len(df)

    # Check for required flags
    required_flags = ['microstructure_controlled', 'single_crystal']
    missing_flags = [f for f in required_flags if f not in df.columns]

    if missing_flags:
        # If columns are missing, we might need to handle them or raise error
        # Based on T009, these should exist. If not, raise error.
        raise DataInsufficientError(f"Missing provenance columns: {missing_flags}")

    # Drop rows where flags are missing (NaN) or False?
    # Task says: "exclude entries missing microstructure_controlled/single_crystal flags"
    # Usually means NaN or None.
    # Let's assume we need valid (True/False) or at least not NaN.
    # If the task implies only 'True' is valid, we'd filter df[col] == True.
    # But "missing flags" usually implies data quality check (NaN).
    # Let's filter out NaNs first.
    df = df.dropna(subset=required_flags)

    # Log excluded
    excluded = initial_count - len(df)
    if excluded > 0:
        logger.warning(f"Excluded {excluded} entries due to missing provenance flags.")

    return df

def normalize_atomic_fractions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize atomic fractions to sum to 1.0."""
    logger.info("Normalizing atomic fractions...")

    def normalize_comp(comp_str):
        elements, total = parse_composition(comp_str)
        if total == 0:
            return comp_str, {} # Return empty
        normalized = {k: v/total for k, v in elements.items()}
        return comp_str, normalized

    # Apply normalization and store results
    # We need to extract the normalized fractions to compute descriptors
    normalized_data = []
    for idx, row in df.iterrows():
        _, norm_dict = normalize_comp(row['composition'])
        normalized_data.append(norm_dict)

    df['_normalized_composition'] = normalized_data
    return df

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptors: atomic_radius_variance, VEC, electronegativity_spread, mixing_entropy."""
    logger.info("Computing descriptors...")

    def calculate_row_descriptors(norm_comp: Dict[str, float], temperature: float) -> Dict[str, float]:
        if not norm_comp:
            return {}

        elements = list(norm_comp.keys())
        fractions = list(norm_comp.values())

        # Get properties
        radii = []
        vecs = []
        electronegativities = []

        for elem, frac in zip(elements, fractions):
            try:
                el = Element(elem)
                radii.append(el.atomic_radius)
                vecs.append(el.oxi_state or 0) # VEC is often valence electron count
                # pymatgen Element doesn't have direct VEC. Use get_valence_electrons?
                # Or use a lookup. Let's use a standard VEC lookup for common metals.
                # For now, assume get_vec helper exists.
                vecs.append(get_vec(elem))
                electronegativities.append(el.X) # Pauling electronegativity
            except Exception as e:
                logger.warning(f"Could not get properties for {elem}: {e}")
                radii.append(0)
                vecs.append(0)
                electronegativities.append(0)

        if not radii:
            return {}

        # Atomic radius variance
        mean_radius = np.mean(radii)
        radius_variance = np.var(radii) # Variance of radii

        # VEC (Average)
        # VEC = sum(xi * VECi)
        avg_vec = np.sum(np.array(fractions) * np.array(vecs))

        # Electronegativity spread (Standard deviation or range)
        # "electronegativity_spread" usually means std dev or max-min
        elec_std = np.std(electronegativities)

        # Mixing entropy: -R * sum(xi * ln(xi))
        # xi must be > 0
        mixing_entropy = 0.0
        for x in fractions:
            if x > 0:
                mixing_entropy -= x * math.log(x)
        mixing_entropy *= R_GAS # J/(mol·K) - wait, usually dimensionless or in R units.
        # Task says: mixing_entropy = -R * sum(xi * ln(xi)).
        # So units are J/(mol·K) if T is involved later? No, entropy is J/(mol·K).
        # But often in ML, it's just the dimensionless sum. Let's follow the formula.

        # inv_temperature = 1.0 / T
        inv_temp = 1.0 / temperature if temperature > 0 else 0.0

        return {
            'atomic_radius_variance': radius_variance,
            'VEC': avg_vec,
            'electronegativity_spread': elec_std,
            'mixing_entropy': mixing_entropy,
            'inv_temperature': inv_temp
        }

    descriptors = []
    for idx, row in df.iterrows():
        norm_comp = row['_normalized_composition']
        temp = row['temperature']
        desc = calculate_row_descriptors(norm_comp, temp)
        descriptors.append(desc)

    # Flatten descriptors into columns
    desc_df = pd.DataFrame(descriptors)
    df = pd.concat([df, desc_df], axis=1)
    return df

def apply_log_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """Apply log10 transformation to diffusion_coefficient."""
    logger.info("Applying log10 transformation to diffusion coefficient...")
    if 'diffusion_coefficient' in df.columns:
        # Handle potential zeros or negatives
        df['log_D'] = np.log10(df['diffusion_coefficient'].clip(lower=1e-20))
    else:
        raise DataInsufficientError("Column 'diffusion_coefficient' not found.")
    return df

def clean_and_finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Final cleaning and column selection."""
    logger.info("Finalizing dataset...")
    # Select required columns per schema T004b
    # composition, structure, log_D, atomic_radius_variance, VEC, electronegativity_spread,
    # mixing_entropy, inv_temperature, microstructure_controlled, single_crystal
    required_cols = [
        'composition', 'structure', 'log_D', 'atomic_radius_variance', 'VEC',
        'electronegativity_spread', 'mixing_entropy', 'inv_temperature',
        'microstructure_controlled', 'single_crystal'
    ]

    # Ensure all exist
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataInsufficientError(f"Missing columns in final dataset: {missing}")

    df = df[required_cols].copy()
    return df

def validate_split_config(strategy: str, n_samples: int) -> Dict[str, Any]:
    """Validate and return split config dict."""
    # T004c schema: strategy (enum), n_samples (int), warning_emitted (bool)
    config = {
        'strategy': strategy,
        'n_samples': n_samples,
        'warning_emitted': False
    }
    return config

def determine_split_strategy(df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
    """Determine split strategy based on sample size."""
    n = len(df)
    strategy = "80/20"
    warning_emitted = False

    if n < 30:
        strategy = "LOOCV"
        warning_emitted = True
        logger.warning(f"Sample size ({n}) < 30. Switching to LOOCV. Emitting PowerWarning.")
        # Raise PowerWarning to be caught by main or logging
        # We can't raise it here if we want to continue, but we log it.
        # The task says "emit PowerWarning".
        # Let's raise it so the main function can handle it or log it.
        # But we need to return the strategy.
        # We'll handle the raise in main.
        # Actually, let's just log and return. The task says "emit", which can be log.
        # But T007 defines PowerWarning exception.
        # Let's raise it.
        raise PowerWarning(f"Sample size ({n}) < 30. Using LOOCV.")

    return strategy, {'strategy': strategy, 'n_samples': n, 'warning_emitted': warning_emitted}

def main():
    """Main execution for T010."""
    logger.info("Starting preprocessing pipeline...")

    try:
        # 1. Load raw data
        df = load_raw_data()

        # 2. Filter for BCC and Carbon
        df = filter_bcc_carbon(df)

        # 3. Enforce provenance
        df = enforce_provenance(df)

        # 4. Normalize atomic fractions
        df = normalize_atomic_fractions(df)

        # 5. Compute descriptors
        df = compute_descriptors(df)

        # 6. Apply log transformation
        df = apply_log_transformation(df)

        # 7. Determine split strategy
        try:
            strategy, split_config = determine_split_strategy(df)
        except PowerWarning as pw:
            logger.warning(str(pw))
            # Re-calculate strategy for the return value
            n = len(df)
            strategy = "LOOCV" if n < 30 else "80/20"
            split_config = {'strategy': strategy, 'n_samples': n, 'warning_emitted': True}

        # 8. Clean and finalize
        df = clean_and_finalize(df)

        # 9. Write outputs
        output_csv = Path("data/processed/dataset_cleaned.csv")
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved cleaned dataset to {output_csv}")

        # 10. Write split config
        output_json = Path("data/processed/split_config.json")
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, 'w') as f:
            json.dump(split_config, f, indent=2)
        logger.info(f"Saved split config to {output_json}")

        logger.info("Preprocessing pipeline completed successfully.")

    except DataInsufficientError as e:
        handle_data_insufficient(e)
        sys.exit(1)
    except PowerWarning as e:
        handle_power_warning(e)
        # Continue execution, as we handled the warning
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()