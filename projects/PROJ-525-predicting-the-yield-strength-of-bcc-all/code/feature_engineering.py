import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import from project API surface
from env_config import get_processed_data_path, get_raw_data_path, ensure_dirs, setup_logger
from utils.periodic_table import (
    get_element_properties,
    calculate_atomic_radius_mismatch,
    calculate_valence_electron_concentration,
    calculate_electronegativity_average,
)
from models import AlloyRecord, CompositionalDescriptor
from utils import DataIntegrityError, ValidationError

# Setup logger
logger = setup_logger(__name__)

THERMO_PARAMS_PATH = "data/raw/thermo_params.json"

def load_config() -> Dict[str, Any]:
    """Load configuration if needed (placeholder for future extensibility)."""
    return {}

def validate_thermo_params(filepath: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that thermo_params.json exists and contains valid float entries
    for all required binary pairs.

    Args:
        filepath: Path to the thermo_params.json file.

    Returns:
        Tuple of (is_valid, error_message).
    """
    path = Path(filepath)

    if not path.exists():
        return False, f"Thermodynamic parameters file not found at {filepath}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in thermo_params.json: {e}"

    if not isinstance(data, dict):
        return False, "Thermo params must be a dictionary mapping binary pairs to parameters."

    required_keys = ["delta", "omega", "entropy_correction"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        return False, f"Missing required keys in thermo_params: {missing_keys}"

    # Validate structure: each key should map to a dict of binary pairs -> float values
    for key in required_keys:
        sub_data = data[key]
        if not isinstance(sub_data, dict):
            return False, f"Key '{key}' in thermo_params must be a dictionary of binary pairs."

        for pair, value in sub_data.items():
            if not isinstance(value, (int, float)):
                return False, f"Invalid value type for pair '{pair}' in '{key}': expected float, got {type(value).__name__}"
            if not np.isfinite(value):
                return False, f"Non-finite value (NaN/Inf) for pair '{pair}' in '{key}': {value}"

    logger.info(f"Thermo parameters validated successfully: {len(data)} top-level keys, "
                f"{sum(len(v) for v in data.values())} binary pairs.")
    return True, None

def load_thermo_params(filepath: str) -> Dict[str, Any]:
    """
    Load and validate thermodynamic parameters. Raises ValidationError if invalid.

    Args:
        filepath: Path to the thermo_params.json file.

    Returns:
        The validated dictionary of thermodynamic parameters.

    Raises:
        ValidationError: If the file is missing, malformed, or contains invalid data.
    """
    is_valid, error_msg = validate_thermo_params(filepath)
    if not is_valid:
        raise ValidationError(f"Thermodynamic parameters validation failed: {error_msg}")

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_delta(composition: Dict[str, float], atomic_radii: Dict[str, float]) -> float:
    """Calculate atomic radius mismatch (δ)."""
    return calculate_atomic_radius_mismatch(composition, atomic_radii)

def calculate_vec(composition: Dict[str, float], valences: Dict[str, int]) -> float:
    """Calculate Valence Electron Concentration (VEC)."""
    return calculate_valence_electron_concentration(composition, valences)

def calculate_entropy(composition: Dict[str, float]) -> float:
    """Calculate mixing entropy."""
    entropy = 0.0
    for c in composition.values():
        if c > 0:
            entropy -= c * np.log(c)
    return entropy

def calculate_enhanced_features(
    row: Dict[str, Any],
    thermo_params: Dict[str, Any],
    atomic_radii: Dict[str, float],
    valences: Dict[str, int],
    electronegativities: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate enhanced features including mixing enthalpy using thermo_params.

    This function assumes thermo_params has been validated before calling.
    """
    composition = row.get("composition", {})
    if not composition:
        raise ValueError("Missing composition in alloy row")

    # Calculate scalar descriptors
    delta = calculate_delta(composition, atomic_radii)
    vec = calculate_vec(composition, valences)
    entropy = calculate_entropy(composition)

    # Calculate mixing enthalpy using thermo_params
    # Expected format: thermo_params['omega'] = { "A-B": value, ... }
    omega_params = thermo_params.get("omega", {})
    mixing_enthalpy = 0.0
    elements = list(composition.keys())

    for i, elem_a in enumerate(elements):
        for elem_b in elements[i+1:]:
            # Try both orderings for the pair key
            pair_key = f"{elem_a}-{elem_b}"
            if pair_key not in omega_params:
                pair_key = f"{elem_b}-{elem_a}"

            omega_val = omega_params.get(pair_key, 0.0)
            mixing_enthalpy += omega_val * composition[elem_a] * composition[elem_b]

    # Calculate electronegativity difference (standard deviation)
    en_vals = [electronegativities.get(e, 0.0) for e in elements if e in electronegativities]
    if len(en_vals) > 1:
        en_diff = float(np.std(en_vals))
    else:
        en_diff = 0.0

    return {
        "delta": delta,
        "vec": vec,
        "mixing_entropy": entropy,
        "mixing_enthalpy": mixing_enthalpy,
        "electronegativity_diff": en_diff
    }

def save_features_descriptors(
    df: pd.DataFrame,
    descriptors: List[CompositionalDescriptor],
    output_path: str
):
    """Save engineered features and descriptors to CSV."""
    # Implementation would merge descriptors with original data
    # For now, placeholder for the full pipeline
    pass

def main():
    """
    Main entry point for feature engineering pipeline.
    Includes validation of thermo_params.json before proceeding.
    """
    base_path = get_processed_data_path()
    raw_path = get_raw_data_path()

    # Ensure directories exist
    ensure_dirs()

    # Load and validate thermodynamic parameters (T025a output)
    thermo_path = raw_path / THERMO_PARAMS_PATH
    try:
        thermo_params = load_thermo_params(str(thermo_path))
    except ValidationError as e:
        logger.error(f"Pipeline halted: {e}")
        sys.exit(1)

    # Load processed data from US1
    input_file = base_path / "bcc_filtered.csv"
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} alloys from {input_file}")

    # Load periodic table data
    # Assuming these are populated from a standard source or cached
    atomic_radii = {}
    valences = {}
    electronegativities = {}

    # Populate from a simple mapping or external source
    # In a real implementation, this would load from a database or file
    # For now, we assume the periodic table utilities handle this internally
    # and we just call the calculation functions which handle the lookup.

    # Process each alloy
    descriptors = []
    for idx, row in df.iterrows():
        try:
            composition = row.get("composition")
            if isinstance(composition, str):
                composition = json.loads(composition)

            # Calculate features
            features = calculate_enhanced_features(
                {"composition": composition},
                thermo_params,
                atomic_radii,
                valences,
                electronegativities
            )

            # Create descriptor
            desc = CompositionalDescriptor(
                alloy_id=row.get("alloy_id", f"alloy_{idx}"),
                composition=composition,
                **features
            )
            descriptors.append(desc)

        except Exception as e:
            logger.warning(f"Failed to process alloy {idx}: {e}")
            continue

    # Save results
    output_file = base_path / "features_engineered.csv"
    # Convert descriptors to DataFrame for saving
    data_rows = []
    for d in descriptors:
        row_data = {
            "alloy_id": d.alloy_id,
            "composition": json.dumps(d.composition),
            "delta": d.delta,
            "vec": d.vec,
            "mixing_entropy": d.mixing_entropy,
            "mixing_enthalpy": d.mixing_enthalpy,
            "electronegativity_diff": d.electronegativity_diff,
            # Add ILR features if available (placeholder)
            "ilr_features": json.dumps(d.ilr_transformed_features) if d.ilr_transformed_features else "[]"
        }
        data_rows.append(row_data)

    pd.DataFrame(data_rows).to_csv(output_file, index=False)
    logger.info(f"Saved {len(data_rows)} engineered features to {output_file}")

    return 0

if __name__ == "__main__":
    sys.exit(main())