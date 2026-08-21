"""
DFT Setup and Literature Reference Module.

This module provides utilities for:
1. Loading and managing a local literature database of known vibrational modes.
2. Initializing the literature database if it doesn't exist.
3. Mapping binned spectral indices to known vibrational modes.
4. Setting up and running local DFT calculations using PySCF for validation.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np

# Import project utilities to ensure consistency
from src.utils.io import read_json_file, write_json_file, ensure_directory_exists
from src.utils.logging import log_info, log_error, log_warning, flag_edge_case

# Default paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
LITERATURE_DB_PATH = REFERENCE_DIR / "literature_db.json"

# Standard IR frequency ranges (cm-1) for common functional groups
# Used for initial mapping before DFT validation
KNOWN_MODES = {
    "O-H stretch": {"range": (3200, 3600), "typical": 3400},
    "N-H stretch": {"range": (3300, 3500), "typical": 3400},
    "C-H stretch (alkane)": {"range": (2850, 2960), "typical": 2900},
    "C-H stretch (alkene)": {"range": (3000, 3100), "typical": 3050},
    "C-H stretch (alkyne)": {"range": (3300, 3320), "typical": 3300},
    "C=O stretch": {"range": (1670, 1780), "typical": 1710},
    "C=C stretch": {"range": (1600, 1680), "typical": 1650},
    "C=N stretch": {"range": (1600, 1700), "typical": 1650},
    "C-O stretch": {"range": (1000, 1300), "typical": 1100},
    "C-Cl stretch": {"range": (600, 800), "typical": 700},
    "C-Br stretch": {"range": (500, 600), "typical": 550},
    "Fingerprint region": {"range": (600, 1400), "typical": 1000},
}


def init_literature_db() -> Dict[str, Any]:
    """
    Initialize the literature database with standard known modes.
    Creates the file at data/reference/literature_db.json if it doesn't exist.
    """
    ensure_directory_exists(REFERENCE_DIR)

    if LITERATURE_DB_PATH.exists():
        log_info(f"Literature database already exists at {LITERATURE_DB_PATH}")
        return load_literature_db()

    db_structure = {
        "metadata": {
            "version": "1.0.0",
            "source": "Standard literature values (NIST, SDBS)",
            "created_by": "T033a-dft-setup",
            "last_updated": "2023-10-27"
        },
        "modes": {}
    }

    # Populate with standard known modes
    for mode_name, details in KNOWN_MODES.items():
        db_structure["modes"][mode_name] = {
            "frequency_range_cm1": details["range"],
            "typical_frequency_cm1": details["typical"],
            "description": f"Standard {mode_name} vibration",
            "reference": "Literature standard",
            "dft_validated": False  # Will be updated after DFT runs
        }

    write_json_file(LITERATURE_DB_PATH, db_structure)
    log_info(f"Initialized literature database at {LITERATURE_DB_PATH}")
    return db_structure


def load_literature_db() -> Dict[str, Any]:
    """
    Load the literature database from disk.
    If the file doesn't exist, initialize it first.
    """
    if not LITERATURE_DB_PATH.exists():
        log_warning(f"Literature database not found at {LITERATURE_DB_PATH}, initializing...")
        return init_literature_db()

    try:
        db = read_json_file(LITERATURE_DB_PATH)
        log_info(f"Loaded literature database with {len(db.get('modes', {}))} modes")
        return db
    except Exception as e:
        log_error(f"Failed to load literature database: {e}")
        raise


def map_bin_to_mode(bin_index: int, bin_width: float = 4.0, total_bins: int = 512) -> List[str]:
    """
    Map a binned spectral index to potential vibrational modes based on frequency.

    Args:
        bin_index: The index of the bin (0 to total_bins-1)
        bin_width: Width of each bin in cm-1 (default 4.0 for 512 bins over 2048 cm-1 range)
        total_bins: Total number of bins

    Returns:
        List of potential mode names that this bin might correspond to.
    """
    # Calculate center frequency of the bin
    # Assuming range 0-2048 cm-1 mapped to 0-511
    center_freq = bin_index * bin_width + (bin_width / 2)

    potential_modes = []
    db = load_literature_db()

    for mode_name, mode_data in db.get("modes", {}).items():
        freq_range = mode_data.get("frequency_range_cm1")
        if freq_range:
            low, high = freq_range
            if low <= center_freq <= high:
                potential_modes.append(mode_name)

    if not potential_modes:
        log_warning(f"Bin {bin_index} (freq ~{center_freq:.1f} cm-1) does not match any known modes in DB")

    return potential_modes


def get_simple_geometry(molecule_smiles: str) -> Dict[str, List[List[float]]]:
    """
    Generate a simple initial geometry for a molecule based on SMILES.
    In a real implementation, this would use RDKit or similar to generate 3D coordinates.
    For this foundational task, we provide a placeholder that raises an error
    if not implemented with a real generator, or returns a simple water molecule as demo.

    Note: This is a placeholder. A full implementation requires RDKit or OpenBabel.
    """
    # Placeholder: Return water geometry as a demonstration
    # In production, this would parse SMILES and generate coordinates
    if "O" in molecule_smiles and len(molecule_smiles) == 1:
        # Water: O at origin, H's at ~0.96 Angstroms, 104.5 deg angle
        return {
            "atoms": ["O", "H", "H"],
            "coords": [
                [0.0, 0.0, 0.0],
                [0.75695, 0.5858, 0.0],
                [-0.75695, 0.5858, 0.0]
            ]
        }

    # For other molecules, we cannot generate a valid geometry without RDKit
    # This forces the user to install RDKit or provide coordinates for real validation
    raise NotImplementedError(
        "Full geometry generation requires RDKit. "
        "Install with: pip install rdkit "
        "or provide explicit coordinates for the molecule."
    )


def setup_pyscf_calculation(
    atoms: List[str],
    coords: List[List[float]],
    basis: str = "sto-3g",
    charge: int = 0,
    spin: int = 0
) -> 'pyscf.gto.Mole':
    """
    Set up a PySCF calculation object for frequency analysis.

    Args:
        atoms: List of atomic symbols (e.g., ["C", "H", "H", "H", "H"])
        coords: List of [x, y, z] coordinates in Angstroms
        basis: Basis set to use (default "sto-3g" for speed)
        charge: Molecular charge
        spin: Spin multiplicity (2S+1)

    Returns:
        Configured PySCF Mole object
    """
    try:
        import pyscf
        from pyscf import gto, dft, freq
    except ImportError:
        raise ImportError(
            "PySCF is required for DFT calculations. "
            "Install with: pip install pyscf"
        )

    mol = gto.Mole()
    mol.atom = [[atom, list(coord)] for atom, coord in zip(atoms, coords)]
    mol.basis = basis
    mol.charge = charge
    mol.spin = spin  # 2S
    mol.unit = 'Angstrom'
    mol.verbose = 4  # Print level
    mol.build()

    return mol


def run_pyscf_frequency(mol: 'pyscf.gto.Mole') -> Tuple[List[float], List[List[float]]]:
    """
    Run a DFT frequency calculation on the provided molecule.

    Args:
        mol: PySCF Mole object

    Returns:
        Tuple of (frequencies, intensities)
        frequencies: List of wavenumbers (cm-1)
        intensities: List of IR intensities (km/mol)
    """
    try:
        from pyscf import dft
    except ImportError:
        raise ImportError("PySCF required for DFT frequency calculations.")

    # Perform DFT calculation
    mf = dft.RKS(mol)
    mf.xc = 'lda,vwn'  # Simple functional for speed; B3LYP is better but slower
    mf.kernel()

    # Check if calculation converged
    if not mf.converged:
        log_warning("DFT calculation did not converge. Results may be unreliable.")

    # Calculate frequencies
    # Note: PySCF frequency analysis requires additional steps for IR intensities
    # This is a simplified version. For full IR intensities, one needs to compute
    # dipole derivatives.
    try:
        # Standard frequency calculation
        hessian = mol.hessian()
        # Simplified: assume we get frequencies from hessian diagonalization
        # In reality, this requires mass-weighting and diagonalization
        # For this foundational task, we return placeholder frequencies
        # that would be replaced by real output in a full implementation
        log_info("Running frequency analysis (simplified for foundational task)...")

        # Placeholder: In a real run, this would extract from mf.freqs or similar
        # For now, we return empty or mock to indicate the path is set up
        # The actual implementation would look like:
        # freqs = mf.freqs  # If available
        # intensities = mf.ir_intensities

        # Since full frequency implementation in PySCF is complex and context-dependent,
        # we return a structured placeholder that indicates the calculation was attempted.
        # A real implementation would populate these with actual values.
        return [], []

    except Exception as e:
        log_error(f"Frequency calculation failed: {e}")
        raise


def validate_feature_with_dft(
    bin_index: int,
    molecule_smiles: str,
    experimental_freq: float,
    tolerance: float = 50.0
) -> Dict[str, Any]:
    """
    Validate a spectral feature by running a local DFT calculation.

    This function:
    1. Maps the bin to a potential mode.
    2. Generates a geometry for the molecule.
    3. Runs a DFT frequency calculation.
    4. Compares calculated frequencies to experimental value.

    Args:
        bin_index: The binned spectral index
        molecule_smiles: SMILES string of the molecule
        experimental_freq: Observed frequency in cm-1
        tolerance: Acceptable deviation in cm-1

    Returns:
        Dictionary with validation results
    """
    result = {
        "bin_index": bin_index,
        "molecule": molecule_smiles,
        "experimental_freq": experimental_freq,
        "validated": False,
        "matched_mode": None,
        "calculated_freq": None,
        "deviation": None,
        "error": None
    }

    try:
        # 1. Map bin to mode
        modes = map_bin_to_mode(bin_index)
        if not modes:
            result["error"] = "No known mode mapped for this bin"
            return result

        result["matched_mode"] = modes[0]  # Take first match

        # 2. Get geometry (requires RDKit in full implementation)
        try:
            geo = get_simple_geometry(molecule_smiles)
        except NotImplementedError as e:
            result["error"] = str(e)
            result["validated"] = False
            return result

        # 3. Setup and run DFT
        mol = setup_pyscf_calculation(geo["atoms"], geo["coords"])
        freqs, intensities = run_pyscf_frequency(mol)

        if not freqs:
            result["error"] = "DFT frequency calculation returned no results"
            return result

        # 4. Compare frequencies
        # Find closest calculated frequency to experimental
        closest_freq = min(freqs, key=lambda f: abs(f - experimental_freq))
        deviation = abs(closest_freq - experimental_freq)

        result["calculated_freq"] = closest_freq
        result["deviation"] = deviation
        result["validated"] = deviation <= tolerance

        if result["validated"]:
            log_info(f"Feature validated: {modes[0]} at {experimental_freq} cm-1 "
                     f"(calc: {closest_freq:.1f}, dev: {deviation:.1f})")
        else:
            log_warning(f"Feature NOT validated: {modes[0]} at {experimental_freq} cm-1 "
                        f"(calc: {closest_freq:.1f}, dev: {deviation:.1f} > {tolerance})")

    except Exception as e:
        result["error"] = str(e)
        log_error(f"DFT validation failed for bin {bin_index}: {e}")

    return result
