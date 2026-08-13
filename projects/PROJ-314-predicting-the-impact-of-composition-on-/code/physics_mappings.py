"""
Mapping of descriptors to physical mechanisms.

This module provides a dictionary mapping computed chemical/structural descriptors
to their underlying physical mechanisms in ceramic fracture mechanics. This mapping
is used by the interpretability pipeline (US3) to explain model predictions in
terms of established materials science principles.
"""

from typing import Dict, Optional

# Primary mapping: descriptor name -> physical mechanism description
MAPPINGS: Dict[str, str] = {
    # Structural descriptors
    "cation_size_variance": "Grain boundary stability",
    "mean_atomic_radius": "Lattice distortion",
    "electronegativity_std": "Bond ionicity",
    "valence_electron_concentration": "Electronic structure stability",
    "range_uncertainty": "Composition measurement confidence",
    
    # Derived from primary anion/cation group
    "primary_anion_cation_group": "Material class-specific fracture behavior",
    
    # Additional descriptors that may be computed
    "atomic_packing_factor": "Density and void distribution",
    "bond_ionicity_index": "Charge transfer and bond strength",
    "covalency_score": "Directional bonding characteristics",
    "melting_point_normalized": "Thermal stability influence",
    "hardness_estimate": "Resistance to plastic deformation",
}

# Reverse mapping: mechanism -> list of descriptors
_REVERSE_MAPPINGS: Optional[Dict[str, list]] = None

def get_physics_mapping() -> Dict[str, str]:
    """
    Retrieve the complete descriptor-to-mechanism mapping.
    
    Returns:
        Dict mapping descriptor names to their physical mechanism descriptions.
    """
    return MAPPINGS.copy()

def get_descriptor_mechanism(descriptor_name: str) -> Optional[str]:
    """
    Get the physical mechanism for a specific descriptor.
    
    Args:
        descriptor_name: The name of the descriptor (e.g., 'cation_size_variance').
    
    Returns:
        The physical mechanism description, or None if not found.
    """
    return MAPPINGS.get(descriptor_name)

def get_mechanism_descriptors(mechanism: str) -> list:
    """
    Get all descriptors associated with a specific physical mechanism.
    
    Args:
        mechanism: The physical mechanism name (e.g., 'Grain boundary stability').
    
    Returns:
        List of descriptor names associated with this mechanism.
    """
    global _REVERSE_MAPPINGS
    if _REVERSE_MAPPINGS is None:
        _REVERSE_MAPPINGS = {}
        for desc, mech in MAPPINGS.items():
            if mech not in _REVERSE_MAPPINGS:
                _REVERSE_MAPPINGS[mech] = []
            _REVERSE_MAPPINGS[mech].append(desc)
    
    return _REVERSE_MAPPINGS.get(mechanism, [])

def validate_descriptor_exists(descriptor_name: str) -> bool:
    """
    Check if a descriptor has a defined physical mechanism mapping.
    
    Args:
        descriptor_name: The descriptor name to check.
    
    Returns:
        True if the descriptor is mapped, False otherwise.
    """
    return descriptor_name in MAPPINGS