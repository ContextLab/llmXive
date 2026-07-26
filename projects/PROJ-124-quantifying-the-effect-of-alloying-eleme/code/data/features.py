"""
Feature engineering module for Metallic Glass Forming Ability (GFA) prediction.

Computes physics-based descriptors using Pymatgen:
- Atomic radius (weighted mean)
- Electronegativity (weighted mean)
- Valence Electron Concentration (VEC) - raw and weighted mean
- Size mismatch descriptors (overall and pairwise)

Output: data/processed/features.csv
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np

# Import from project utils
from utils.logger import get_logger, log_info, log_warning, log_error, FeatureEngineeringError

# Constants
SPECIES_PROPERTIES = {
    'atomic_radius': 'atomic_radius',
    'electronegativity': 'electronegativity',
    'valence': 'valence'
}

logger = get_logger(__name__)


def get_element_properties(element_symbol: str) -> Dict[str, Optional[float]]:
    """
    Fetch atomic properties for a given element symbol using Pymatgen.

    Args:
        element_symbol: Chemical symbol (e.g., 'Fe', 'Cu')

    Returns:
        Dictionary with atomic_radius, electronegativity, and valence.
        Returns None values if property is unavailable.
    """
    try:
        from pymatgen.core import Element
        elem = Element(element_symbol)

        # Get atomic radius (in Angstroms)
        atomic_radius = elem.atomic_radius

        # Get electronegativity (Pauling scale)
        electronegativity = elem.electronegativity

        # Get valence electrons
        valence = elem.oxi_state_guesses(max_oxi_state=3, target_oxi_state=None)
        # Pymatgen returns a list of possible oxidation states; we need valence count.
        # For metals, we often use group number or common oxidation state.
        # Using the number of valence electrons from the periodic table group.
        try:
            # Fallback: use group number for valence if oxi_state_guesses fails or is ambiguous
            valence = elem.group_number % 18  # Simplified valence approximation
            if valence == 0:
                valence = elem.group_number
        except Exception:
            valence = 0

        return {
            'atomic_radius': atomic_radius,
            'electronegativity': electronegativity,
            'valence': float(valence) if valence else 0.0
        }

    except ImportError:
        log_error("Pymatgen is not installed. Please install it via pip install pymatgen")
        raise FeatureEngineeringError("Pymatgen dependency missing")
    except Exception as e:
        log_warning(f"Failed to fetch properties for element {element_symbol}: {e}")
        return {
            'atomic_radius': None,
            'electronegativity': None,
            'valence': None
        }


def parse_composition_string(composition_str: str) -> List[Tuple[str, float]]:
    """
    Parse a composition string into a list of (element, fraction) tuples.

    Expected formats:
    - "Fe40.5Ni40.5B19" (no spaces, element + percentage)
    - "Fe 40.5 Ni 40.5 B 19" (with spaces)
    - "Fe40.5Ni40.5B19.0" (float percentages)

    Args:
        composition_str: String representation of composition

    Returns:
        List of tuples: [(element_symbol, atomic_fraction), ...]
    """
    import re

    # Normalize: remove spaces, ensure consistent format
    comp = composition_str.replace(" ", "")

    # Regex to match element symbol followed by optional number
    # Element symbols: One uppercase, optionally followed by lowercase
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'

    matches = re.findall(pattern, comp)

    if not matches:
        log_warning(f"Could not parse composition string: {composition_str}")
        return []

    result = []
    total = 0.0

    for elem, frac_str in matches:
        try:
            frac = float(frac_str)
            result.append((elem, frac))
            total += frac
        except ValueError:
            log_warning(f"Invalid fraction in composition: {composition_str}")
            continue

    # Normalize to sum to 1.0 if total is not 100
    if total > 0 and abs(total - 100.0) > 0.1:
        # If the sum is not 100, assume it's already normalized or needs normalization
        if total != 1.0:
            result = [(elem, frac / total) for elem, frac in result]

    return result


def compute_weighted_mean(
    elements: List[Tuple[str, float]],
    property_func: callable,
    property_name: str
) -> float:
    """
    Compute the weighted mean of a property across a composition.

    Args:
        elements: List of (element, fraction) tuples
        property_func: Function to fetch properties for an element
        property_name: Key in the returned property dict

    Returns:
        Weighted mean value. Returns np.nan if any element is missing the property.
    """
    weighted_sum = 0.0
    total_weight = 0.0
    has_missing = False

    for elem, frac in elements:
        props = property_func(elem)
        if props is None or props.get(property_name) is None:
            has_missing = True
            continue

        prop_val = props[property_name]
        if prop_val is not None:
            weighted_sum += prop_val * frac
            total_weight += frac
        else:
            has_missing = True

    if total_weight == 0 or has_missing:
        return np.nan

    return weighted_sum / total_weight


def compute_size_mismatch(elements: List[Tuple[str, float]]) -> float:
    """
    Compute the overall size mismatch descriptor (delta).

    Formula: delta = sqrt(sum(f_i * (1 - r_i / r_avg)^2))
    where r_avg is the weighted mean atomic radius.

    Args:
        elements: List of (element, fraction) tuples

    Returns:
        Size mismatch value. Returns np.nan if data is insufficient.
    """
    # First compute weighted mean radius
    r_avg = compute_weighted_mean(elements, get_element_properties, 'atomic_radius')

    if r_avg is None or np.isnan(r_avg) or r_avg == 0:
        return np.nan

    delta_sum = 0.0
    total_weight = 0.0
    has_missing = False

    for elem, frac in elements:
        props = get_element_properties(elem)
        if props is None or props.get('atomic_radius') is None:
            has_missing = True
            continue

        r_i = props['atomic_radius']
        if r_i is None:
            has_missing = True
            continue

        term = (1.0 - r_i / r_avg) ** 2
        delta_sum += frac * term
        total_weight += frac

    if total_weight == 0 or has_missing:
        return np.nan

    return np.sqrt(delta_sum)


def compute_pairwise_size_mismatch(elements: List[Tuple[str, float]]) -> List[float]:
    """
    Compute pairwise size mismatch descriptors for every unique pair of elements.

    For a composition with N elements, there are N*(N-1)/2 unique pairs.
    Descriptor: delta_ij = |r_i - r_j| / max(r_i, r_j)

    Args:
        elements: List of (element, fraction) tuples

    Returns:
        List of pairwise size mismatch values, ordered by pair index.
        Returns empty list if fewer than 2 elements.
    """
    if len(elements) < 2:
        return []

    # Extract radii for valid elements
    radii = []
    valid_elements = []

    for elem, frac in elements:
        props = get_element_properties(elem)
        if props and props.get('atomic_radius') is not None:
            radii.append(props['atomic_radius'])
            valid_elements.append((elem, frac))

    if len(valid_elements) < 2:
        return []

    pairwise_mismatches = []

    # Iterate over all unique pairs
    for i in range(len(valid_elements)):
        for j in range(i + 1, len(valid_elements)):
            r_i = radii[i]
            r_j = radii[j]

            max_r = max(r_i, r_j)
            if max_r == 0:
                pairwise_mismatches.append(0.0)
            else:
                delta_ij = abs(r_i - r_j) / max_r
                pairwise_mismatches.append(delta_ij)

    return pairwise_mismatches


def compute_features(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Main function to compute features for a dataset of compositions.

    Args:
        input_path: Path to input CSV with 'composition' and 'log10_Rc' columns
        output_path: Path to save output CSV with computed features

    Returns:
        DataFrame with computed features
    """
    log_info(f"Loading input data from {input_path}")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_cols = ['composition']
    if 'log10_Rc' not in df.columns:
        # Try to compute log10_Rc if Rc exists
        if 'Rc' in df.columns:
            df['log10_Rc'] = np.log10(df['Rc'].replace(0, np.nan))
            log_info("Computed log10_Rc from Rc column")
        else:
            raise ValueError("Input CSV must contain 'composition' and either 'log10_Rc' or 'Rc' column")

    # Initialize result list
    results = []
    skipped_rows = 0

    for idx, row in df.iterrows():
        comp_str = row['composition']
        log10_rc = row.get('log10_Rc', None)

        # Parse composition
        elements = parse_composition_string(comp_str)

        if not elements:
            log_warning(f"Skipping row {idx}: Could not parse composition '{comp_str}'")
            skipped_rows += 1
            continue

        # Check for unknown elements
        valid_elements = []
        for elem, frac in elements:
            props = get_element_properties(elem)
            if props is None or (props['atomic_radius'] is None and props['electronegativity'] is None):
                log_warning(f"Row {idx}: Element '{elem}' has missing properties. Skipping row.")
                skipped_rows += 1
                break
            valid_elements.append((elem, frac))
        else:
            # Only process if all elements are valid
            elements = valid_elements

            # Compute descriptors
            atomic_radius_mean = compute_weighted_mean(elements, get_element_properties, 'atomic_radius')
            electronegativity_mean = compute_weighted_mean(elements, get_element_properties, 'electronegativity')
            vec_avg = compute_weighted_mean(elements, get_element_properties, 'valence')
            size_mismatch = compute_size_mismatch(elements)
            pairwise_mismatches = compute_pairwise_size_mismatch(elements)

            # Prepare row data
            row_data = {
                'composition': comp_str,
                'log10_Rc': log10_rc,
                'atomic_radius_mean': atomic_radius_mean,
                'electronegativity_mean': electronegativity_mean,
                'VEC_avg': vec_avg,
                'size_mismatch': size_mismatch,
                'source_row_id': idx
            }

            # Add pairwise mismatches with dynamic column names
            for i, pm in enumerate(pairwise_mismatches):
                row_data[f'pairwise_size_mismatch_{i+1}'] = pm

            results.append(row_data)

    if not results:
        log_error("No valid rows processed. Check input data and element properties.")
        raise FeatureEngineeringError("No valid features computed")

    # Create DataFrame
    features_df = pd.DataFrame(results)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    features_df.to_csv(output_path, index=False)
    log_info(f"Saved {len(features_df)} rows to {output_path}")
    log_info(f"Skipped {skipped_rows} rows due to parsing or missing element properties")

    return features_df


def main():
    """
    Entry point for feature engineering script.
    """
    log_info("Starting feature engineering pipeline")

    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "raw" / "gfa_dataset.csv"
    output_path = project_root / "data" / "processed" / "features.csv"

    try:
        features_df = compute_features(input_path, output_path)
        log_info("Feature engineering completed successfully")
        print(f"Output saved to: {output_path}")
        print(f"Columns: {list(features_df.columns)}")
        print(f"Rows: {len(features_df)}")

    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        raise
    except Exception as e:
        log_error(f"Feature engineering failed: {e}")
        raise FeatureEngineeringError(f"Feature engineering failed: {e}")


if __name__ == "__main__":
    main()
