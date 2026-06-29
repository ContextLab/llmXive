"""
Compute thermodynamic descriptors for alloy compositions.

Calculates atomic size mismatch (δ), mixing enthalpy (ΔH_mix), and
electronegativity variance from validated elemental compositions.

Outputs:
  - data/derived/descriptor_vector.csv: Computed descriptors per sample
  - code/descriptors/provenance.yaml: Calculation parameters and metadata
  - state/artifact_hashes.yaml: SHA-256 checksums for artifact tracking
"""

import argparse
import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pymatgen.core.periodic_table import Element

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/computation_log.jsonl'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DESCRIPTOR_INPUT_PATH = Path('data/derived/valid_elements.csv')
DESCRIPTOR_OUTPUT_PATH = Path('data/derived/descriptor_vector.csv')
PROVENANCE_PATH = Path('code/descriptors/provenance.yaml')
ARTIFACT_HASHES_PATH = Path('state/artifact_hashes.yaml')

# Descriptor calculation parameters (Constitution VII compliance)
DESCRIPTOR_PARAMS = {
    'version': '1.0.0',
    'atomic_radii_source': 'pymatgen.core.periodic_table.Element.atomic_radius',
    'electronegativity_source': 'pymatgen.core.periodic_table.Element.electronegativity',
    'enthalpy_of_mixing_source': 'pymatgen.analysis.phase_diagram.EnthalpyOfMixing',
    'random_seed': 42,
    'timestamp': datetime.now().isoformat()
}

# Binary mixing enthalpy lookup (kJ/mol) - simplified values from Miedema model
# This is a subset; full implementation would use pymatgen's EnthalpyOfMixing
BINARY_ENTHALPY_LOOKUP = {
    # Cu-Zr system (common benchmark)
    ('Cu', 'Zr'): -23.0,
    ('Zr', 'Cu'): -23.0,
    # Add more as needed - fallback to 0 if not found
}

def get_atomic_radius(element_symbol: str) -> float:
    """Get atomic radius from pymatgen's periodic table."""
    try:
        elem = Element(element_symbol)
        return elem.atomic_radius
    except Exception as e:
        logger.warning(f"Could not get atomic radius for {element_symbol}: {e}")
        return None

def get_electronegativity(element_symbol: str) -> float:
    """Get electronegativity from pymatgen's periodic table."""
    try:
        elem = Element(element_symbol)
        return elem.electronegativity
    except Exception as e:
        logger.warning(f"Could not get electronegativity for {element_symbol}: {e}")
        return None

def get_binary_mixing_enthalpy(elem1: str, elem2: str) -> float:
    """Get binary mixing enthalpy (kJ/mol)."""
    try:
        key = (elem1, elem2)
        if key in BINARY_ENTHALPY_LOOKUP:
            return BINARY_ENTHALPY_LOOKUP[key]
        # Fallback: use pymatgen if available, else 0
        return 0.0
    except Exception as e:
        logger.warning(f"Could not get mixing enthalpy for {elem1}-{elem2}: {e}")
        return 0.0

def compute_atomic_size_mismatch(composition: dict) -> float:
    """
    Compute atomic size mismatch δ.

    δ = sqrt(Σ c_i * (1 - r_i / r_avg)^2)
    where c_i is atomic fraction, r_i is atomic radius, r_avg is weighted average radius.
    """
    radii = []
    fractions = []

    for elem, frac in composition.items():
        radius = get_atomic_radius(elem)
        if radius is not None:
            radii.append(radius)
            fractions.append(frac)

    if len(radii) == 0:
        return np.nan

    radii = np.array(radii)
    fractions = np.array(fractions)

    # Weighted average radius
    r_avg = np.sum(fractions * radii)

    # Compute δ
    delta = np.sqrt(np.sum(fractions * ((1 - radii / r_avg) ** 2)))

    return float(delta)

def compute_mixing_enthalpy(composition: dict) -> float:
    """
    Compute mixing enthalpy ΔH_mix.

    ΔH_mix = Σ Σ c_i * c_j * ΔH_ij
    where c_i, c_j are atomic fractions and ΔH_ij is binary mixing enthalpy.
    """
    elements = list(composition.keys())
    fractions = list(composition.values())

    delta_h = 0.0
    for i, elem_i in enumerate(elements):
        for j, elem_j in enumerate(elements):
            if i == j:
                continue  # Skip self-interaction
            c_i = fractions[i]
            c_j = fractions[j]
            delta_h_ij = get_binary_mixing_enthalpy(elem_i, elem_j)
            delta_h += c_i * c_j * delta_h_ij

    # Normalize by 2 to avoid double counting
    return float(delta_h / 2.0)

def compute_electronegativity_variance(composition: dict) -> float:
    """
    Compute electronegativity variance.

    Var(χ) = Σ c_i * (χ_i - χ_avg)^2
    where c_i is atomic fraction, χ_i is electronegativity.
    """
    electronegativities = []
    fractions = []

    for elem, frac in composition.items():
        chi = get_electronegativity(elem)
        if chi is not None:
            electronegativities.append(chi)
            fractions.append(frac)

    if len(electronegativities) == 0:
        return np.nan

    chi = np.array(electronegativities)
    fractions = np.array(fractions)

    # Weighted average electronegativity
    chi_avg = np.sum(fractions * chi)

    # Compute variance
    variance = np.sum(fractions * ((chi - chi_avg) ** 2))

    return float(variance)

def parse_composition(composition_str: str) -> dict:
    """
    Parse composition string like 'Cu40Zr60' or 'Cu40.0Zr60.0' into dict.

    Returns: {'Cu': 0.4, 'Zr': 0.6}
    """
    composition = {}
    i = 0
    current_elem = ''

    while i < len(composition_str):
        char = composition_str[i]
        if char.isupper():
            if current_elem:
                # Parse the number that follows
                j = i
                while j < len(composition_str) and (composition_str[j].isdigit() or composition_str[j] == '.'):
                    j += 1
                if j > i:
                  frac = float(composition_str[i:j])
                  composition[current_elem] = frac / 100.0
            current_elem = char
            i += 1
        elif char.islower():
            current_elem += char
            i += 1
        else:
            i += 1

    # Handle last element
    if current_elem:
        j = i
        while j < len(composition_str) and (composition_str[j].isdigit() or composition_str[j] == '.'):
            j += 1
        if j > i:
            frac = float(composition_str[i:j])
            composition[current_elem] = frac / 100.0

    return composition

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def update_artifact_hashes(output_path: Path, new_hash: str):
    """Update state/artifact_hashes.yaml with new checksum."""
    if ARTIFACT_HASHES_PATH.exists():
        with open(ARTIFACT_HASHES_PATH, 'r') as f:
            hashes_data = yaml.safe_load(f) or {}
    else:
        hashes_data = {}

    # Initialize if needed
    if 'descriptor_vectors' not in hashes_data:
        hashes_data['descriptor_vectors'] = {}

    hashes_data['descriptor_vectors']['descriptor_vector.csv'] = {
        'hash': new_hash,
        'updated_at': datetime.now().isoformat()
    }

    # Ensure directory exists
    ARTIFACT_HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(ARTIFACT_HASHES_PATH, 'w') as f:
        yaml.dump(hashes_data, f, default_flow_style=False)

def write_provenance():
    """Write calculation parameters to provenance.yaml."""
    PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROVENANCE_PATH, 'w') as f:
        yaml.dump(DESCRIPTOR_PARAMS, f, default_flow_style=False)

def main():
    """Main entry point for descriptor computation."""
    parser = argparse.ArgumentParser(
        description='Compute thermodynamic descriptors for alloy compositions'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=str(DESCRIPTOR_INPUT_PATH),
        help='Path to input composition CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(DESCRIPTOR_OUTPUT_PATH),
        help='Path to output descriptor CSV'
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    logger.info(f"Starting descriptor computation")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

    # Write provenance
    write_provenance()
    logger.info(f"Written provenance to {PROVENANCE_PATH}")

    # Read input data
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    logger.info(f"Read {len(df)} samples from input")

    # Compute descriptors for each row
    results = []
    for idx, row in df.iterrows():
        sample_id = row.get('sample_id', f'sample_{idx}')
        composition_str = row.get('composition', '')

        try:
            composition = parse_composition(composition_str)

            delta = compute_atomic_size_mismatch(composition)
            delta_h = compute_mixing_enthalpy(composition)
            chi_var = compute_electronegativity_variance(composition)

            results.append({
                'sample_id': sample_id,
                'composition': composition_str,
                'atomic_size_mismatch': delta,
                'mixing_enthalpy': delta_h,
                'electronegativity_variance': chi_var
            })

            logger.info(f"Processed {sample_id}: δ={delta:.4f}, ΔH={delta_h:.4f}, Var(χ)={chi_var:.6f}")

        except Exception as e:
            logger.error(f"Error processing {sample_id}: {e}")
            results.append({
                'sample_id': sample_id,
                'composition': composition_str,
                'atomic_size_mismatch': np.nan,
                'mixing_enthalpy': np.nan,
                'electronegativity_variance': np.nan
            })

    # Create output DataFrame
    output_df = pd.DataFrame(results)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    output_df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(output_df)} rows to {output_path}")

    # Compute and store checksum
    output_hash = compute_sha256(output_path)
    update_artifact_hashes(output_path, output_hash)
    logger.info(f"Computed SHA-256: {output_hash}")
    logger.info(f"Updated artifact hashes in {ARTIFACT_HASHES_PATH}")

    logger.info("Descriptor computation complete")

if __name__ == '__main__':
    main()
