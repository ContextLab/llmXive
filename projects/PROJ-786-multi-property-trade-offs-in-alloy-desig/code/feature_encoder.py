"""
Feature Encoder for Alloy Composition Data.

Encodes alloy compositions using elemental fractions and periodic descriptors
(atomic radius, electronegativity) fetched via mendeleev.

This module implements FR-002: Encoding compositions using elemental fractions
and periodic descriptors for all elements present.
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from mendeleev import element

# Import project utilities
from utils.logging_config import get_logger, log_info_with_context, log_error_with_context, log_warning_with_context
from config import get_config

# Configure logger
logger = get_logger(__name__)

# Constants for feature naming
FRACTION_PREFIX = "frac_"
RADIUS_PREFIX = "radius_"
ELECTRONEG_PREFIX = "electroneg_"
MISSING_VALUE = -1.0  # Sentinel for missing periodic data

def get_periodic_property(element_symbol: str, property_name: str) -> float:
    """
    Fetch a periodic property for a given element symbol.

    Args:
        element_symbol: Chemical symbol (e.g., 'Fe', 'Ni')
        property_name: Name of the property ('atomic_radius', 'electronegativity')

    Returns:
        The property value, or MISSING_VALUE if not available.
    """
    try:
        elem = element(element_symbol)
        if property_name == 'atomic_radius':
            val = elem.atomic_radius
        elif property_name == 'electronegativity':
            val = elem.electronegativity
        else:
            raise ValueError(f"Unsupported property: {property_name}")

        if val is None:
            return MISSING_VALUE
        return float(val)
    except Exception as e:
        log_warning_with_context(
            logger,
            f"Failed to fetch {property_name} for element {element_symbol}: {e}",
            context={"element": element_symbol, "property": property_name}
        )
        return MISSING_VALUE

def encode_composition(composition_str: str) -> Dict[str, float]:
    """
    Encode a single composition string into a feature vector.

    The composition string is expected to be in the format:
    "Element1:Fraction1,Element2:Fraction2,..."
    e.g., "Fe:0.5,Ni:0.3,Cr:0.2"

    Args:
        composition_str: String representation of the alloy composition.

    Returns:
        Dictionary of features including elemental fractions and periodic descriptors.
    """
    features: Dict[str, float] = {}
    elements = []
    fractions = []

    # Parse composition string
    if not composition_str or pd.isna(composition_str):
        log_error_with_context(logger, "Empty or null composition string provided")
        return features

    try:
        parts = composition_str.split(',')
        for part in parts:
            if ':' not in part:
                log_warning_with_context(logger, f"Invalid composition format: {part}")
                continue
            sym, frac = part.split(':')
            sym = sym.strip()
            frac = float(frac.strip())
            elements.append(sym)
            fractions.append(frac)
    except Exception as e:
        log_error_with_context(logger, f"Failed to parse composition string: {composition_str}", context={"error": str(e)})
        return features

    if not elements:
        return features

    # Calculate weighted averages for periodic descriptors
    total_frac = sum(fractions)
    if total_frac == 0:
        log_error_with_context(logger, "Sum of fractions is zero")
        return features

    norm_fractions = [f / total_frac for f in fractions]

    # Store elemental fractions
    for sym, frac in zip(elements, norm_fractions):
        features[f"{FRACTION_PREFIX}{sym}"] = frac

    # Calculate weighted average descriptors
    avg_radius = 0.0
    avg_electroneg = 0.0
    radius_count = 0
    electroneg_count = 0

    for sym, frac in zip(elements, norm_fractions):
        radius = get_periodic_property(sym, 'atomic_radius')
        electroneg = get_periodic_property(sym, 'electronegativity')

        if radius != MISSING_VALUE:
            avg_radius += frac * radius
            radius_count += 1
        if electroneg != MISSING_VALUE:
            avg_electroneg += frac * electroneg
            electroneg_count += 1

    # Only include descriptors if at least one element had valid data
    if radius_count > 0:
        features["avg_atomic_radius"] = avg_radius
    if electroneg_count > 0:
        features["avg_electronegativity"] = avg_electroneg

    # Add element count as a feature
    features["num_elements"] = float(len(elements))

    return features

def encode_dataframe(df: pd.DataFrame, composition_col: str = 'composition') -> pd.DataFrame:
    """
    Encode a DataFrame of alloy entries.

    Args:
        df: Input DataFrame containing a composition column.
        composition_col: Name of the column containing composition strings.

    Returns:
        DataFrame with encoded features appended.
    """
    log_info_with_context(logger, "Starting feature encoding process", context={"rows": len(df)})

    if composition_col not in df.columns:
        raise ValueError(f"Composition column '{composition_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")

    # Apply encoding to each row
    encoded_features = df[composition_col].apply(encode_composition)

    # Convert list of dicts to DataFrame
    encoded_df = pd.DataFrame(encoded_features.tolist(), index=df.index)

    # Merge with original DataFrame
    result_df = pd.concat([df, encoded_df], axis=1)

    # Log statistics
    total_features = len(encoded_df.columns)
    features_with_data = encoded_df.notna().sum().sum()
    total_cells = encoded_df.size
    fill_rate = (features_with_data / total_cells * 100) if total_cells > 0 else 0

    log_info_with_context(
        logger,
        f"Encoding complete. Generated {total_features} features.",
        context={"fill_rate": f"{fill_rate:.2f}%", "rows_processed": len(df)}
    )

    return result_df

def save_encoded_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the encoded DataFrame to a CSV file.

    Args:
        df: DataFrame to save.
        output_path: Path to the output CSV file.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        log_info_with_context(logger, f"Encoded data saved to {output_path}", context={"rows": len(df), "columns": len(df.columns)})
    except Exception as e:
        log_error_with_context(logger, f"Failed to save encoded data to {output_path}", context={"error": str(e)})
        raise

def main() -> None:
    """
    Main entry point for the feature encoder script.

    Reads from data/processed/encoded_alloys_raw.csv (output of data_ingestion.py)
    and writes to data/processed/encoded_alloys.csv.
    """
    config = get_config()
    input_path = config.get('input_encoded_path', 'data/processed/encoded_alloys_raw.csv')
    output_path = config.get('output_encoded_path', 'data/processed/encoded_alloys.csv')

    log_info_with_context(logger, "Feature Encoder started", context={"input": input_path, "output": output_path})

    if not os.path.exists(input_path):
        log_error_with_context(logger, f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(input_path)
        log_info_with_context(logger, f"Loaded {len(df)} rows from {input_path}")

        encoded_df = encode_dataframe(df, composition_col='composition')

        save_encoded_data(encoded_df, output_path)

        log_info_with_context(logger, "Feature encoding completed successfully")

    except Exception as e:
        log_error_with_context(logger, f"Feature encoding failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
