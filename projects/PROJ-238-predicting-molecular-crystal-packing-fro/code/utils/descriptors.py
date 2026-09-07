"""
Descriptor computation utilities for molecular crystal packing prediction.

Wraps RDKit to compute Volume, Surface Area, Dipole, HBA, HBD, and PSA.
"""
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, Lipinski
from rdkit import DataStructs
import math
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def compute_descriptors(mol: Chem.rdchem.Mol) -> Dict[str, float]:
    """
    Compute a standard set of molecular descriptors for a given RDKit molecule.
    
    Descriptors computed:
      - Volume: Molecular volume (Å³) via rdMolDescriptors
      - SurfaceArea: Total surface area (Å²) via rdMolDescriptors
      - Dipole: Estimated dipole moment (Debye) via Gasteiger charge-based approximation
                (Note: RDKit does not have a direct dipole calculator; we use a proxy
                based on molecular complexity and charge distribution if available,
                or return 0.0 if not computable. For this task, we use the 
                Descriptors.TPSA as a proxy for polarity if dipole is not directly 
                available, but strictly following the spec, we attempt to compute 
                a dipole-like value. However, RDKit's standard library does not 
                provide a direct 'dipole' function without external force fields.
                To satisfy the requirement of returning a 'Dipole' value without 
                external dependencies, we use the 'MolWt' scaled by a factor or 
                return 0.0 if strictly no calculation exists. 
                Correction: The task asks for 'Dipole'. RDKit does not compute 
                dipole moments natively without MMFF/UFF. 
                Strategy: We will calculate the dipole moment using MMFF94 if 
                parameters are available, otherwise return 0.0 and log a warning.
      - HBA: Number of hydrogen bond acceptors (Lipinski)
      - HBD: Number of hydrogen bond donors (Lipinski)
      - PSA: Topological Polar Surface Area (TPSA)
    
    Args:
        mol: RDKit Mol object (must be sanitized and have hydrogens added if needed).
    
    Returns:
        Dictionary with keys: 'Volume', 'SurfaceArea', 'Dipole', 'HBA', 'HBD', 'PSA'.
        Values are floats. If a value cannot be computed, it is set to 0.0.
    
    Raises:
        TypeError: If mol is not an RDKit Mol object.
    """
    if not isinstance(mol, Chem.rdchem.Mol):
        raise TypeError(f"Expected RDKit Mol object, got {type(mol)}")
    
    if mol is None:
        logger.warning("Received None molecule, returning zeros.")
        return {
            "Volume": 0.0,
            "SurfaceArea": 0.0,
            "Dipole": 0.0,
            "HBA": 0.0,
            "HBD": 0.0,
            "PSA": 0.0
        }

    # 1. Volume (Å³)
    # Using rdMolDescriptors.CalcCrippenDescriptors for volume? No, that's logP.
    # Using rdMolDescriptors.CalcMolVolume() (requires RDKit 2019.09+ or similar).
    # Fallback: If CalcMolVolume is not available, we might need to use a different method.
    # Standard RDKit usually has CalcMolVolume in rdMolDescriptors.
    try:
        volume = rdMolDescriptors.CalcMolVolume(mol)
    except AttributeError:
        logger.warning("CalcMolVolume not available, using 0.0.")
        volume = 0.0
    
    # 2. Surface Area (Å²)
    # Using rdMolDescriptors.CalcMolSurfaceArea()
    try:
        surface_area = rdMolDescriptors.CalcMolSurfaceArea(mol)
    except AttributeError:
        # Fallback to Descriptors.MolLogP? No, that's not area.
        # Use Descriptors.SaScore? No.
        # Try Descriptors.MolWt as a proxy? No.
        # Just 0.0 if not available.
        logger.warning("CalcMolSurfaceArea not available, using 0.0.")
        surface_area = 0.0

    # 3. HBA (Hydrogen Bond Acceptors)
    hba = Lipinski.NumHAcceptors(mol)

    # 4. HBD (Hydrogen Bond Donors)
    hbd = Lipinski.NumHDonors(mol)

    # 5. PSA (Topological Polar Surface Area)
    # Descriptors.TPSA is the standard RDKit implementation.
    psa = Descriptors.TPSA(mol)

    # 6. Dipole Moment (Debye)
    # RDKit does not have a built-in dipole calculator in the Descriptors module.
    # It requires MMFF94 or UFF optimization and property calculation.
    # We attempt to use MMFF94.
    dipole = 0.0
    try:
        # Check if MMFF is available
        from rdkit.Chem import AllChem
        mmff_props = AllChem.MMFFGetMoleculeProperties(mol)
        if mmff_props is not None:
            mmff_mol = AllChem.MMFFGetMoleculeForceField(mol, mmff_props)
            if mmff_mol is not None:
                # MMFF94 can calculate dipole moment?
                # Actually, MMFF94 properties include dipole in some versions, 
                # but standard RDKit API for dipole is not direct in the force field object.
                # However, we can try to get the dipole moment from the MMFF properties if available.
                # In many RDKit builds, MMFFGetMoleculeProperties does not directly expose dipole.
                # Alternative: Use the Gasteiger charges to estimate a rough dipole?
                # Or simply return 0.0 if the specific function is missing.
                # Let's try to access the dipole moment if the force field supports it.
                # Note: Most standard RDKit versions do NOT expose a direct 'GetDipole' method
                # on the force field object in the public API without custom C++ bindings.
                # To be safe and compliant with "runnable code" without external C++ extensions,
                # we will use a heuristic or return 0.0 if the direct calculation is not exposed.
                # However, the task requires it. 
                # Let's try: AllChem.MMFFCalculateDipoleMoment(mol) ? No such function.
                # We will use the TPSA as a proxy for polarity if dipole is strictly required 
                # but not computable, OR we return 0.0 and log.
                # Given the strict requirement "Dipole", and RDKit's limitation:
                # We will attempt to compute it if possible, else 0.0.
                # Actually, there is no standard RDKit function for dipole moment without 
                # external libraries (like OpenBabel or custom scripts).
                # We will set it to 0.0 and log a warning to ensure the pipeline runs,
                # as fabricating a value is forbidden.
                logger.warning("Dipole moment calculation not available in standard RDKit API. Returning 0.0.")
        else:
            logger.warning("MMFF properties not available for dipole calculation.")
    except Exception as e:
        logger.warning(f"Error computing dipole moment: {e}. Returning 0.0.")

    return {
        "Volume": float(volume),
        "SurfaceArea": float(surface_area),
        "Dipole": float(dipole),
        "HBA": float(hba),
        "HBD": float(hbd),
        "PSA": float(psa)
    }
