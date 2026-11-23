import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from pymatgen.core import Composition
from matminer.featurizers.composition import ElementProperty

from config import get_processed_data_dir, get_raw_data_dir
from exceptions import FeaturizationError, raise_loudly
from utils import setup_logging

logger = logging.getLogger(__name__)

# Network former and modifier elements as per domain definition
NETWORK_FORMERS = {'Si', 'B', 'P'}
MODIFIERS = {'Na', 'K', 'Ca'}

# Matminer ElementProperty featurizer instance configured for the required properties
# We use standard elemental properties: Electronegativity, Atomic Mass, Valence
_element_prop_featurizer = ElementProperty.from_preset('magpie')

def parse_formula(formula_str: str) -> Composition:
    """
    Parse a chemical formula string into a pymatgen Composition object.

    Args:
        formula_str: Chemical formula string (e.g., "SiO2", "Na2O", "Si0.5B0.5O2")

    Returns:
        Composition object

    Raises:
        FeaturizationError: If the formula cannot be parsed
    """
    try:
        return Composition(formula_str)
    except Exception as e:
        raise_loudly(FeaturizationError(f"Failed to parse formula '{formula_str}': {e}"))

def calculate_atomic_fractions(composition: Composition) -> Dict[str, float]:
    """
    Calculate atomic fractions for network formers and modifiers.

    Args:
        composition: pymatgen Composition object

    Returns:
        Dictionary with keys:
            - 'network_former_fraction': Sum of atomic fractions of Si, B, P
            - 'modifier_fraction': Sum of atomic fractions of Na, K, Ca
    """
    elements = composition.elements
    atomic_fractions = composition.atomic_fraction_dict

    nf_sum = sum(atomic_fractions.get(el.symbol, 0.0) for el in elements if el.symbol in NETWORK_FORMERS)
    mod_sum = sum(atomic_fractions.get(el.symbol, 0.0) for el in elements if el.symbol in MODIFIERS)

    return {
        'network_former_fraction': float(nf_sum),
        'modifier_fraction': float(mod_sum)
    }

def calculate_network_former_ratio(composition: Composition) -> float:
    """
    Calculate the ratio of network former to modifier content.

    Args:
        composition: pymatgen Composition object

    Returns:
        Network former / modifier ratio. Returns 0.0 if modifier fraction is 0.
    """
    fractions = calculate_atomic_fractions(composition)
    nf = fractions['network_former_fraction']
    mod = fractions['modifier_fraction']

    if mod == 0.0:
        return float(nf) if nf > 0 else 0.0
    return float(nf / mod)

def calculate_average_electronegativity(composition: Composition) -> float:
    """
    Calculate average electronegativity weighted by atomic fraction.

    Args:
        composition: pymatgen Composition object

    Returns:
        Weighted average electronegativity
    """
    try:
        # Use ElementProperty to get electronegativity
        # magpie preset includes electronegativity as one of the features
        featurized = _element_prop_featurizer.featurize(composition)
        # Magpie features are ordered; we need to extract electronegativity specifically
        # To be robust, we re-calculate manually using ElementProperty with specific props
        props = ElementProperty(['electronegativity'])
        vals = props.featurize(composition)
        return float(vals[0])
    except Exception as e:
        # Fallback: manual calculation if magpie fails
        logger.warning(f"ElementProperty failed for {composition}, falling back to manual calc: {e}")
        total_weight = 0.0
        weighted_sum = 0.0
        for el, amt in composition.items():
            # Manual lookup using pymatgen's Element class
            from pymatgen.core import Element
            elem = Element(el)
            electroneg = elem.Electronegativity
            weight = amt / composition.num_atoms
            weighted_sum += electroneg * weight
            total_weight += weight
        return float(weighted_sum / total_weight) if total_weight > 0 else 0.0

def calculate_average_atomic_mass(composition: Composition) -> float:
    """
    Calculate average atomic mass weighted by atomic fraction.

    Args:
        composition: pymatgen Composition object

    Returns:
        Weighted average atomic mass
    """
    try:
        props = ElementProperty(['atomic_mass'])
        vals = props.featurize(composition)
        return float(vals[0])
    except Exception:
        # Fallback: manual calculation
        total_weight = 0.0
        weighted_sum = 0.0
        for el, amt in composition.items():
            from pymatgen.core import Element
            elem = Element(el)
            mass = elem.AtomicMass
            weight = amt / composition.num_atoms
            weighted_sum += mass * weight
            total_weight += weight
        return float(weighted_sum / total_weight) if total_weight > 0 else 0.0

def calculate_valence_electron_count(composition: Composition) -> float:
    """
    Calculate total valence electron count weighted by atomic fraction.

    Args:
        composition: pymatgen Composition object

    Returns:
        Weighted average valence electron count
    """
    try:
        props = ElementProperty(['num_valence'])
        vals = props.featurize(composition)
        return float(vals[0])
    except Exception:
        # Fallback: manual calculation
        total_weight = 0.0
        weighted_sum = 0.0
        for el, amt in composition.items():
            from pymatgen.core import Element
            elem = Element(el)
            valence = elem.Valence
            weight = amt / composition.num_atoms
            weighted_sum += valence * weight
            total_weight += weight
        return float(weighted_sum / total_weight) if total_weight > 0 else 0.0

def featurize_sample(formula_str: str, tg_value: Optional[float] = None) -> Dict[str, Any]:
    """
    Featurize a single glass sample.

    Args:
        formula_str: Chemical formula string
        tg_value: Optional glass transition temperature value

    Returns:
        Dictionary containing formula, Tg, and all compositional features
    """
    composition = parse_formula(formula_str)

    fractions = calculate_atomic_fractions(composition)
    nf_ratio = calculate_network_former_ratio(composition)
    avg_electroneg = calculate_average_electronegativity(composition)
    avg_mass = calculate_average_atomic_mass(composition)
    valence_count = calculate_valence_electron_count(composition)

    result = {
        'formula': formula_str,
        'network_former_fraction': fractions['network_former_fraction'],
        'modifier_fraction': fractions['modifier_fraction'],
        'network_former_ratio': nf_ratio,
        'avg_electronegativity': avg_electroneg,
        'avg_atomic_mass': avg_mass,
        'valence_electron_count': valence_count,
        'Tg': tg_value
    }

    return result

def featurize_dataset(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Load raw glass data, featurize each sample, and save to CSV.

    Args:
        input_path: Path to raw CSV data file
        output_path: Path to save featurized CSV

    Returns:
        DataFrame containing featurized data
    """
    if not input_path.exists():
        raise_loudly(FeaturizationError(f"Input file not found: {input_path}"))

    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_csv(input_path)

    # Identify columns: expect 'formula' and optionally 'Tg' or 'T_g'
    formula_col = None
    tg_col = None

    for col in df.columns:
        if 'formula' in col.lower():
            formula_col = col
        if 'tg' in col.lower() or 'T_g' in col or 'Tg' in col:
            tg_col = col

    if formula_col is None:
        raise_loudly(FeaturizationError("Could not find 'formula' column in input data"))

    logger.info(f"Found formula column: {formula_col}, Tg column: {tg_col}")

    featurized_rows = []
    failed_count = 0

    for idx, row in df.iterrows():
        formula = row[formula_col]
        tg = row[tg_col] if tg_col else None

        try:
            features = featurize_sample(formula, tg)
            featurized_rows.append(features)
        except Exception as e:
            failed_count += 1
            logger.warning(f"Failed to featurize sample at index {idx}: {e}")

    if failed_count > 0:
        logger.warning(f"Failed to featurize {failed_count} samples out of {len(df)}")

    result_df = pd.DataFrame(featurized_rows)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving featurized data to {output_path}")
    result_df.to_csv(output_path, index=False)

    return result_df

def main():
    """Main entry point for the featurization script."""
    setup_logging()
    logger.info("Starting featurization pipeline...")

    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_data_dir()

    input_path = raw_dir / "glass_data.csv"
    output_path = processed_dir / "glass_features.csv"

    if not input_path.exists():
        # Check for alternative names
        possible_names = ['glass_data.csv', 'raw_glass.csv', 'nist_glass.csv']
        for name in possible_names:
            alt_path = raw_dir / name
            if alt_path.exists():
                input_path = alt_path
                logger.info(f"Found alternative input file: {alt_path}")
                break

    if not input_path.exists():
        raise_loudly(FeaturizationError(
            f"No raw data file found in {raw_dir}. "
            "Please run download_data.py first to fetch the dataset."
        ))

    df = featurize_dataset(input_path, output_path)
    logger.info(f"Featurization complete. Processed {len(df)} samples.")
    logger.info(f"Output saved to: {output_path}")

    # Print summary statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    logger.info("Feature summary statistics:")
    logger.info(df[numeric_cols].describe())

    return df

if __name__ == "__main__":
    main()