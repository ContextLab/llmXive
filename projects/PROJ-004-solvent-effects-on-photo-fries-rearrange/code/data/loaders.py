"""
Solvent property loaders for Photo-Fries rearrangement kinetics.

This module provides functions to fetch real solvent properties from the
versioned lookup table defined in data/chemicals/solvents.yaml.
No synthetic generation of input properties occurs here.
"""

import os
import yaml
from typing import Dict, List, Optional, Any

from utils.logging import log_compliance_check


# Project root relative path resolution
# Assumes code/data/loaders.py is at code/data/loaders.py
# Target file is at data/chemicals/solvents.yaml
_SOLVENTS_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "chemicals",
    "solvents.yaml"
)


class SolventDataError(Exception):
    """Custom exception for solvent data loading errors."""
    pass


def _load_solvent_manifest() -> Dict[str, Any]:
    """
    Load the raw YAML manifest from disk.

    Returns:
        Dict containing the full YAML structure (metadata + solvents list).

    Raises:
        SolventDataError: If the file cannot be found or parsed.
    """
    if not os.path.exists(_SOLVENTS_FILE_PATH):
        raise SolventDataError(
            f"Solvent lookup table not found at {_SOLVENTS_FILE_PATH}. "
            "Ensure T006 has been completed and the file exists."
        )

    try:
        with open(_SOLVENTS_FILE_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SolventDataError(f"Failed to parse YAML in {_SOLVENTS_FILE_PATH}: {e}")
    
    if data is None:
        raise SolventDataError(f"Solvent lookup table {_SOLVENTS_FILE_PATH} is empty.")

    return data


def get_solvent_properties(solvent_name: str) -> Dict[str, Any]:
    """
    Fetch properties for a specific solvent by name.

    Args:
        solvent_name: The exact name of the solvent as defined in solvents.yaml.

    Returns:
        Dict containing 'name', 'dielectric_constant', 'source_id', 'notes'.

    Raises:
        SolventDataError: If the solvent is not found or data is invalid.
    """
    manifest = _load_solvent_manifest()
    
    if 'solvents' not in manifest or not isinstance(manifest['solvents'], list):
        raise SolventDataError("Invalid manifest structure: 'solvents' list missing.")

    for entry in manifest['solvents']:
        if entry.get('name') == solvent_name:
            # Validate required fields
            required_fields = ['name', 'dielectric_constant', 'source_id']
            for field in required_fields:
                if field not in entry:
                    raise SolventDataError(
                        f"Solvent '{solvent_name}' is missing required field '{field}'."
                    )
            
            log_compliance_check(
                component="loader",
                action="fetch",
                details=f"Loaded properties for {solvent_name} from {manifest['metadata']['source']}"
            )
            return entry

    available = [s['name'] for s in manifest['solvents']]
    raise SolventDataError(
        f"Solvent '{solvent_name}' not found in lookup table. "
        f"Available: {available}"
    )


def get_all_solvents() -> List[Dict[str, Any]]:
    """
    Fetch all solvent properties from the lookup table.

    Returns:
        List of dicts, each containing properties for a solvent.

    Raises:
        SolventDataError: If the file cannot be loaded or parsed.
    """
    manifest = _load_solvent_manifest()

    if 'solvents' not in manifest:
        raise SolventDataError("Invalid manifest structure: 'solvents' list missing.")

    validated_solvents = []
    for entry in manifest['solvents']:
        required_fields = ['name', 'dielectric_constant', 'source_id']
        if all(field in entry for field in required_fields):
            validated_solvents.append(entry)
        else:
            # Log a warning but continue loading valid entries
            log_compliance_check(
                component="loader",
                action="skip_invalid_entry",
                details=f"Skipping invalid solvent entry: {entry.get('name', 'unknown')}"
            )

    return validated_solvents


def get_dielectric_constant_range() -> Dict[str, float]:
    """
    Get the minimum and maximum dielectric constants available in the table.

    Returns:
        Dict with keys 'min' and 'max'.

    Raises:
        SolventDataError: If no valid solvents are found.
    """
    solvents = get_all_solvents()
    if not solvents:
        raise SolventDataError("No valid solvents found in lookup table.")

    constants = [s['dielectric_constant'] for s in solvents]
    return {
        'min': min(constants),
        'max': max(constants)
    }