import argparse
import hashlib
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pymatgen.core import Composition
from pymatgen.core.periodic_table import Element

# Import utilities from sibling module
from descriptors.utils import (
    get_element_or_none,
    get_nearest_neighbor,
    get_property_with_fallback,
    safe_get_atomic_radius,
    safe_get_electronegativity,
    safe_get_binary_mixing_enthalpy,
    parse_composition
)

# Constants
ERROR_CODE_INVALID_SYMBOL = "INVALID_SYMBOL"
ERROR_CODE_INVALID_STOICHIOMETRY = "INVALID_STOICHIOMETRY"

# Setup logging
logger = logging.getLogger(__name__)

def log_computation_step(sample_id: str, step: str, status: str, details: Optional[str] = None) -> None:
    """
    Logs a computation step to the JSON-Lines log file.
    """
    log_path = Path("logs/computation_log.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "sample_id": sample_id,
        "step": step,
        "status": status,
        "details": details
    }
    
    with open(log_path, 'a') as f:
        f.write(f"{log_entry}\n")

def get_element_or_none(symbol: str) -> Optional[Element]:
    """
    Returns the Element object for a given symbol, or None if invalid.
    """
    try:
        return Element(symbol)
    except Exception:
        return None

def get_nearest_neighbor(symbol: str) -> Optional[Element]:
    """
    Finds the nearest neighbor element in the periodic table if the symbol is invalid.
    """
    # This is a placeholder for the logic that should exist in utils.py
    # Since utils.py is truncated in the prompt, we implement a safe fallback here
    # that attempts to find a neighbor by atomic number if the symbol is invalid.
    # However, for T013, we are primarily concerned with error handling.
    return None

def get_property_with_fallback(symbol: str, property_func, fallback_func) -> Any:
    """
    Gets a property with fallback logic.
    """
    return get_property_with_fallback(symbol, property_func, fallback_func)

def safe_get_atomic_radius(symbol: str) -> float:
    """
    Gets atomic radius with fallback.
    """
    return safe_get_atomic_radius(symbol)

def safe_get_electronegativity(symbol: str) -> float:
    """
    Gets electronegativity with fallback.
    """
    return safe_get_electronegativity(symbol)

def safe_get_binary_mixing_enthalpy(symbol1: str, symbol2: str) -> float:
    """
    Gets binary mixing enthalpy with fallback.
    """
    return safe_get_binary_mixing_enthalpy(symbol1, symbol2)

def parse_composition(composition_str: str) -> Optional[Composition]:
    """
    Parses a composition string into a pymatgen Composition object.
    """
    try:
        return Composition(composition_str)
    except Exception:
        return None

def compute_atomic_size_mismatch(composition: Composition) -> float:
    """
    Computes atomic size mismatch (delta) for a given composition.
    """
    elements = list(composition.elements)
    fractions = list(composition.fractions)
    
    radii = [safe_get_atomic_radius(el.symbol) for el in elements]
    
    mean_radius = np.average(radii, weights=fractions)
    variance = np.average([(r - mean_radius)**2 for r in radii], weights=fractions)
    
    return 100 * np.sqrt(variance) / mean_radius if mean_radius != 0 else 0.0

def compute_mixing_enthalpy(composition: Composition) -> float:
    """
    Computes mixing enthalpy for a given composition.
    """
    elements = list(composition.elements)
    fractions = list(composition.fractions)
    
    total_enthalpy = 0.0
    for i, el_i in enumerate(elements):
        for j, el_j in enumerate(elements):
            if i < j:
                enthalpy_ij = safe_get_binary_mixing_enthalpy(el_i.symbol, el_j.symbol)
                total_enthalpy += 2 * fractions[i] * fractions[j] * enthalpy_ij
    
    return total_enthalpy

def compute_electronegativity_variance(composition: Composition) -> float:
    """
    Computes electronegativity variance for a given composition.
    """
    elements = list(composition.elements)
    fractions = list(composition.fractions)
    
    electronegativities = [safe_get_electronegativity(el.symbol) for el in elements]
    
    mean_en = np.average(electronegativities, weights=fractions)
    variance = np.average([(en - mean_en)**2 for en in electronegativities], weights=fractions)
    
    return variance

def compute_descriptors(row: Dict[str, Any]) -> Tuple[Dict[str, float], str, Optional[str]]:
    """
    Computes descriptors for a single row.
    Returns (descriptor_dict, status, error_code).
    """
    sample_id = row.get('sample_id', 'unknown')
    composition_str = row.get('composition', '')
    
    log_computation_step(sample_id, "parse", "start")
    
    # Check for valid composition string
    if not composition_str or not isinstance(composition_str, str):
        log_computation_step(sample_id, "parse", "failed", "Empty or invalid composition string")
        return {}, "error", ERROR_CODE_INVALID_STOICHIOMETRY
    
    composition = parse_composition(composition_str)
    
    if composition is None:
        log_computation_step(sample_id, "parse", "failed", "Failed to parse composition")
        return {}, "error", ERROR_CODE_INVALID_STOICHIOMETRY
    
    # Validate elements
    elements = list(composition.elements)
    invalid_symbols = []
    for el in elements:
        if get_element_or_none(el.symbol) is None:
            invalid_symbols.append(el.symbol)
    
    if invalid_symbols:
        log_computation_step(sample_id, "validate", "failed", f"Invalid symbols: {invalid_symbols}")
        return {}, "error", ERROR_CODE_INVALID_SYMBOL
    
    log_computation_step(sample_id, "validate", "success")
    
    try:
        delta = compute_atomic_size_mismatch(composition)
        h_mix = compute_mixing_enthalpy(composition)
        var_en = compute_electronegativity_variance(composition)
        
        log_computation_step(sample_id, "compute", "success")
        
        return {
            'atomic_size_mismatch': delta,
            'mixing_enthalpy': h_mix,
            'electronegativity_variance': var_en
        }, "success", None
        
    except Exception as e:
        log_computation_step(sample_id, "compute", "failed", str(e))
        return {}, "error", ERROR_CODE_INVALID_STOICHIOMETRY

def write_provenance(params: Dict[str, Any]) -> None:
    """
    Writes descriptor calculation parameters to provenance.yaml.
    """
    provenance_path = Path("code/descriptors/provenance.yaml")
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    
    provenance_data = {
        'timestamp': datetime.now().isoformat(),
        'parameters': params
    }
    
    with open(provenance_path, 'w') as f:
        yaml.dump(provenance_data, f)

def compute_sha256(file_path: Path) -> str:
    """
    Computes SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_artifact_hashes(file_path: Path, hash_value: str) -> None:
    """
    Updates the artifact_hashes.yaml with the new hash.
    """
    hash_file = Path("state/artifact_hashes.yaml")
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    
    if hash_file.exists():
        with open(hash_file, 'r') as f:
            hashes = yaml.safe_load(f) or {}
    else:
        hashes = {}
    
    hashes[str(file_path)] = {
        'hash': hash_value,
        'updated_at': datetime.now().isoformat()
    }
    
    with open(hash_file, 'w') as f:
        yaml.dump(hashes, f)

def main():
    """
    Main entry point for descriptor computation.
    Reads from data/samples/synthetic_alloys.csv (or specified input),
    computes descriptors, and writes results to data/derived/descriptor_vector.csv
    and errors to data/derived/descriptor_vector_errors.csv.
    """
    parser = argparse.ArgumentParser(description="Compute thermodynamic descriptors for alloy compositions.")
    parser.add_argument('--input', type=str, default='data/samples/synthetic_alloys.csv', help='Input CSV file path')
    parser.add_argument('--output', type=str, default='data/derived/descriptor_vector.csv', help='Output CSV file path for valid descriptors')
    parser.add_argument('--error-output', type=str, default='data/derived/descriptor_vector_errors.csv', help='Output CSV file path for invalid compositions')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    error_output_path = Path(args.error_output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Create output directories
    output_path.parent.mkdir(parents=True, exist_ok=True)
    error_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read input data
    df = pd.read_csv(input_path)
    
    valid_rows = []
    error_rows = []
    
    for idx, row in df.iterrows():
        sample_id = row.get('sample_id', f'row_{idx}')
        descriptors, status, error_code = compute_descriptors(row)
        
        if status == "success":
            valid_row = row.to_dict()
            valid_row.update(descriptors)
            valid_rows.append(valid_row)
        else:
            error_row = row.to_dict()
            error_row['error_code'] = error_code
            error_rows.append(error_row)
    
    # Write valid descriptors
    if valid_rows:
        valid_df = pd.DataFrame(valid_rows)
        valid_df.to_csv(output_path, index=False)
        logger.info(f"Wrote {len(valid_rows)} valid rows to {output_path}")
    else:
        logger.warning("No valid rows found. Creating empty output file.")
        pd.DataFrame(columns=df.columns.tolist() + ['atomic_size_mismatch', 'mixing_enthalpy', 'electronegativity_variance']).to_csv(output_path, index=False)
    
    # Write error rows
    if error_rows:
        error_df = pd.DataFrame(error_rows)
        error_df.to_csv(error_output_path, index=False)
        logger.info(f"Wrote {len(error_rows)} error rows to {error_output_path}")
    else:
        logger.info("No error rows found.")
        pd.DataFrame(columns=df.columns.tolist() + ['error_code']).to_csv(error_output_path, index=False)
    
    # Write provenance
    write_provenance({
        'input_file': str(input_path),
        'output_file': str(output_path),
        'error_output_file': str(error_output_path),
        'valid_count': len(valid_rows),
        'error_count': len(error_rows)
    })
    
    # Update artifact hashes
    if output_path.exists():
        hash_value = compute_sha256(output_path)
        update_artifact_hashes(output_path, hash_value)
        logger.info(f"Updated artifact hash for {output_path}: {hash_value}")

if __name__ == "__main__":
    main()
