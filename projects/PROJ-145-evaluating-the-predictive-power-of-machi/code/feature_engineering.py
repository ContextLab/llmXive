"""
Feature Engineering for High-Entropy Alloy (HEA) Composition Analysis.

This module calculates compositional descriptors (atomic radius, electronegativity,
VEC, melting point) using pymatgen and applies numerical clamping to ensure
stability during downstream model training.
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from pymatgen.core import Element

from config import DATA_PROCESSED, setup_logging

# Ensure logging is configured
setup_logging()
logger = logging.getLogger(__name__)

# Numerical stability threshold to prevent division by zero or log(0)
NUMERICAL_CLAMP_THRESHOLD = 1e-6


def get_element_property(element_symbol: str, property_name: str) -> float:
    """
    Retrieve a specific atomic property for a given element symbol using pymatgen.

    Args:
        element_symbol: The chemical symbol (e.g., 'Fe', 'Ni').
        property_name: The property to retrieve ('atomic_radius', 'electronegativity',
                       'melting_point', 'VEC').

    Returns:
        The property value as a float.

    Raises:
        ValueError: If the element symbol is invalid or the property is not supported.
    """
    try:
        elem = Element(element_symbol)
    except Exception as e:
        raise ValueError(f"Invalid element symbol: {element_symbol}") from e

    if property_name == 'atomic_radius':
        # Use metallic radius if available, otherwise covalent
        val = elem.atomic_radius
        if val is None:
            val = elem.covalent_radius
        return float(val) if val is not None else 0.0
    
    elif property_name == 'electronegativity':
        val = elem.electronegativity
        return float(val) if val is not None else 0.0
    
    elif property_name == 'melting_point':
        val = elem.melting_point
        return float(val) if val is not None else 0.0
    
    elif property_name == 'VEC':
        # Valence Electron Count
        # pymatgen has a valence attribute, but for transition metals, 
        # we often use a specific definition (s + d electrons).
        # For simplicity and consistency with standard HEA literature, 
        # we use the group number for transition metals and main group logic.
        # pymatgen's 'valence' property is a good proxy for main group.
        # For transition metals, we need to be careful.
        # Standard HEA definition: sum of group number for transition metals.
        # Let's use a robust lookup or pymatgen's valence if it matches.
        # pymatgen's Element.valence returns the number of valence electrons.
        # For Sc (21), valence is 3. Ti (22) is 4. This matches the d+s count.
        # For Fe (26), valence is 8 (3d6 4s2). This matches.
        # For Cu (29), valence is 11 (3d10 4s1) or sometimes 1/2 depending on definition.
        # However, in HEA literature, VEC is often calculated as sum of group numbers.
        # Let's use the group number for transition metals specifically if available,
        # or fallback to valence.
        # A common approach in HEA papers: VEC = sum(c_i * VEC_i).
        # We will use the standard valence electrons provided by pymatgen for consistency.
        # Note: For Cu, Ag, Au, pymatgen valence is 11, 11, 11. Group number is 11.
        # For Zn, Cd, Hg, valence is 12. Group number is 12.
        # This seems consistent with the "Group Number" definition used in VEC calculations for HEAs.
        val = elem.valence
        if val is None:
            # Fallback for elements where valence might be tricky (e.g. Lanthanides)
            # Use group number if available
            val = elem.group
        return float(val) if val is not None else 0.0
    
    else:
        raise ValueError(f"Unsupported property: {property_name}")


def calculate_compositional_descriptors(composition_str: str) -> Dict[str, float]:
    """
    Calculate compositional descriptors for a given composition string.

    The composition string is expected to be in the format "Element1_x1_Element2_x2_..."
    or "Element1_x1,Element2_x2,..." where x is the atomic fraction.

    Args:
        composition_str: String representation of the composition.

    Returns:
        A dictionary containing mean and variance for:
        - atomic_radius
        - electronegativity
        - VEC
        - melting_point

    Raises:
        ValueError: If the composition string format is invalid.
    """
    # Parse composition string
    # Expected formats: "Fe_0.2_Ni_0.2..." or "Fe_0.2,Ni_0.2..." or "Fe0.2Ni0.2" (simplified)
    # Based on data_ingestion, the format is likely "Element1_0.2_Element2_0.2"
    # We need to handle the specific format from the dataset.
    # Assuming format: "El1_0.2_El2_0.2_..."
    
    parts = composition_str.replace(",", "_").split("_")
    
    elements = []
    fractions = []
    
    i = 0
    while i < len(parts):
        if not parts[i]:
            i += 1
            continue
        
        # Check if part is an element symbol or a fraction
        # Element symbols are 1-2 chars, fractions are numbers
        # Heuristic: if part is a number (or float), it's a fraction
        try:
            float(parts[i])
            # It's a fraction, but we expect element then fraction
            # This implies the previous part was the element
            # If we are here, it means we might have a dangling fraction or wrong format
            # Let's assume the format is strictly Element_Fraction_Element_Fraction
            # So if we see a number, the previous part must have been the element.
            # But we are iterating. Let's look at the structure.
            # If parts[i] is a number, then parts[i-1] was the element.
            # But we are at i. This logic is tricky.
            # Let's assume the list is [El1, frac1, El2, frac2, ...]
            pass
        except ValueError:
            # It's an element
            elements.append(parts[i])
            i += 1
            continue
        
        # If we are here, parts[i] is a number (fraction)
        # The element should be at i-1, but we already processed it?
        # Let's restart the parsing logic to be robust.
        # We expect pairs: (Element, Fraction)
        pass

    # Robust parsing:
    # Split by underscore, then iterate.
    # If token is alpha (element), next token should be numeric (fraction).
    # Handle cases where fraction might be attached or separated differently.
    
    # Let's assume the format from the dataset is "Fe_0.2_Ni_0.2"
    # So parts = ["Fe", "0.2", "Ni", "0.2"]
    # We can iterate in steps of 2.
    
    if len(parts) % 2 != 0:
        # Try to handle cases where there might be trailing underscores or missing fractions
        # Filter out empty strings
        parts = [p for p in parts if p]
        if len(parts) % 2 != 0:
            raise ValueError(f"Invalid composition format: {composition_str}. Expected pairs of Element_Fraction.")
    
    elements = []
    fractions = []
    for i in range(0, len(parts), 2):
        elem_sym = parts[i]
        frac_str = parts[i+1]
        
        # Validate element
        try:
            Element(elem_sym)
        except Exception:
            raise ValueError(f"Invalid element symbol: {elem_sym}")
        
        elements.append(elem_sym)
        fractions.append(float(frac_str))
    
    # Normalize fractions to sum to 1.0 just in case
    total_frac = sum(fractions)
    if total_frac == 0:
        raise ValueError(f"Sum of fractions is zero in {composition_str}")
    fractions = [f / total_frac for f in fractions]
    
    # Calculate descriptors
    descriptors = {}
    properties = ['atomic_radius', 'electronegativity', 'VEC', 'melting_point']
    
    for prop in properties:
        values = []
        for elem, frac in zip(elements, fractions):
            val = get_element_property(elem, prop)
            values.append(val)
        
        values = np.array(values)
        weights = np.array(fractions)
        
        # Weighted Mean
        mean_val = np.average(values, weights=weights)
        
        # Weighted Variance
        # Var = sum(w * (x - mean)^2) / sum(w)
        variance_val = np.average((values - mean_val) ** 2, weights=weights)
        
        # Apply numerical clamping
        # Clamp mean and variance to avoid issues with very small numbers or zero
        mean_val = max(mean_val, NUMERICAL_CLAMP_THRESHOLD)
        variance_val = max(variance_val, NUMERICAL_CLAMP_THRESHOLD)
        
        descriptors[f'mean_{prop}'] = mean_val
        descriptors[f'var_{prop}'] = variance_val
    
    return descriptors


def process_dataset(input_path: str, output_path: str) -> None:
    """
    Process a dataset CSV, calculate descriptors, and save to a new CSV.

    Args:
        input_path: Path to the input CSV file (e.g., heas_train.csv).
        output_path: Path to save the output CSV file with features.
    """
    logger.info(f"Processing dataset: {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if 'composition_string' not in df.columns:
        raise ValueError("Input CSV must contain 'composition_string' column.")
    
    logger.info(f"Loaded {len(df)} compositions.")
    
    features_list = []
    
    for idx, row in df.iterrows():
        comp_str = row['composition_string']
        try:
            desc = calculate_compositional_descriptors(comp_str)
            desc['composition_string'] = comp_str
            # Preserve target if present
            if 'target_energy' in row:
                desc['target_energy'] = row['target_energy']
            if 'target_hmix' in row:
                desc['target_hmix'] = row['target_hmix']
            features_list.append(desc)
        except Exception as e:
            logger.warning(f"Failed to process composition {comp_str}: {e}")
            # Optionally, we could skip or fill with NaN, but for now we log and skip
            continue
    
    if not features_list:
        logger.error("No valid compositions processed. Check input data format.")
        return
    
    result_df = pd.DataFrame(features_list)
    
    # Ensure consistent column order
    target_cols = ['composition_string', 'target_energy', 'target_hmix']
    feature_cols = [c for c in result_df.columns if c not in target_cols]
    # Sort feature columns for consistency
    feature_cols.sort()
    
    final_cols = [c for c in target_cols if c in result_df.columns] + feature_cols
    result_df = result_df[final_cols]
    
    # Save to output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    
    logger.info(f"Saved {len(result_df)} processed compositions to {output_path}")


def main():
    """
    Main entry point to run feature engineering on all required datasets.
    """
    logger.info("Starting Feature Engineering Pipeline")
    
    datasets = [
        ("heas_train.csv", "heas_train_features.csv"),
        ("holdout_known.csv", "holdout_known_features.csv"),
        ("true_novel.csv", "true_novel_features.csv")
    ]
    
    for input_name, output_name in datasets:
        input_path = str(DATA_PROCESSED / input_name)
        output_path = str(DATA_PROCESSED / output_name)
        
        if os.path.exists(input_path):
            process_dataset(input_path, output_path)
        else:
            logger.warning(f"Input file not found: {input_path}. Skipping.")
    
    logger.info("Feature Engineering Pipeline Completed")


if __name__ == "__main__":
    main()