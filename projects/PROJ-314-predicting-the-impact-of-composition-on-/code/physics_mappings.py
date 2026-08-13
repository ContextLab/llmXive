"""
Mapping of descriptors to physical mechanisms for ceramic reliability prediction.

This module provides a dictionary mapping computed elemental descriptors to their
corresponding physical mechanisms in the context of fracture mechanics and 
Weibull modulus prediction.

Used by User Story 3 (US3) for mechanistic interpretation of model features.
"""

from typing import Dict, Any

# Mapping of descriptor names to physical mechanism descriptions
MAPPINGS: Dict[str, str] = {
    "cation_size_variance": "Grain boundary stability - Variance in cation radii affects grain boundary cohesion and crack propagation resistance",
    "mean_atomic_radius": "Lattice distortion - Average atomic size influences lattice strain and defect formation energy",
    "electronegativity_std": "Bond ionicity - Standard deviation of electronegativity indicates bond character and charge distribution heterogeneity",
    "valence_electron_concentration": "Electronic structure stability - VEC correlates with phase stability and electronic bonding strength",
    "primary_anion_cation_group": "Chemical bonding class - Primary anion-cation pairing determines fundamental ceramic family properties",
    "range_uncertainty": "Measurement confidence - Uncertainty in composition ranges affects reliability estimation precision",
    "sintering_temp": "Microstructural development - Sintering temperature controls grain growth and pore elimination kinetics",
    "sample_count": "Statistical reliability - Number of tested specimens affects Weibull modulus confidence intervals"
}

# Additional metadata for each mapping
METADATA: Dict[str, Dict[str, Any]] = {
    "cation_size_variance": {
        "category": "structural",
        "mechanism_class": "grain_boundary",
        "theoretical_basis": "Hertzian contact theory and grain boundary energy models",
        "expected_correlation": "negative"
    },
    "mean_atomic_radius": {
        "category": "structural",
        "mechanism_class": "lattice",
        "theoretical_basis": "Lattice strain theory and defect formation energy",
        "expected_correlation": "negative"
    },
    "electronegativity_std": {
        "category": "electronic",
        "mechanism_class": "bonding",
        "theoretical_basis": "Pauling's bond electronegativity and ionicity models",
        "expected_correlation": "positive"
    },
    "valence_electron_concentration": {
        "category": "electronic",
        "mechanism_class": "stability",
        "theoretical_basis": "Electron concentration rules for phase stability",
        "expected_correlation": "positive"
    },
    "primary_anion_cation_group": {
        "category": "chemical",
        "mechanism_class": "family",
        "theoretical_basis": "Ceramic family classification and property trends",
        "expected_correlation": "categorical"
    },
    "range_uncertainty": {
        "category": "measurement",
        "mechanism_class": "uncertainty",
        "theoretical_basis": "Propagation of composition uncertainty to property estimates",
        "expected_correlation": "negative"
    },
    "sintering_temp": {
        "category": "processing",
        "mechanism_class": "microstructure",
        "theoretical_basis": "Sintering kinetics and grain growth models",
        "expected_correlation": "positive"
    },
    "sample_count": {
        "category": "statistical",
        "mechanism_class": "reliability",
        "theoretical_basis": "Weibull statistics and confidence interval theory",
        "expected_correlation": "positive"
    }
}

def get_mechanism(descriptor: str) -> str:
    """
    Retrieve the physical mechanism description for a given descriptor.
    
    Args:
        descriptor: The name of the descriptor (e.g., 'cation_size_variance')
        
    Returns:
        The physical mechanism description string
        
    Raises:
        KeyError: If the descriptor is not found in the mappings
    """
    if descriptor not in MAPPINGS:
        raise KeyError(f"Descriptor '{descriptor}' not found in physics mappings. "
                     f"Available descriptors: {list(MAPPINGS.keys())}")
    return MAPPINGS[descriptor]

def get_mechanism_metadata(descriptor: str) -> Dict[str, Any]:
    """
    Retrieve detailed metadata for a given descriptor's physical mechanism.
    
    Args:
        descriptor: The name of the descriptor
        
    Returns:
        Dictionary containing category, mechanism_class, theoretical_basis, 
        and expected_correlation
        
    Raises:
        KeyError: If the descriptor is not found in the metadata
    """
    if descriptor not in METADATA:
        raise KeyError(f"Descriptor '{descriptor}' not found in physics metadata. "
                     f"Available descriptors: {list(METADATA.keys())}")
    return METADATA[descriptor]

def list_all_descriptors() -> list:
    """
    List all available descriptors in the physics mappings.
    
    Returns:
        List of descriptor names
    """
    return list(MAPPINGS.keys())

def describe_all_mappings() -> str:
    """
    Generate a formatted description of all descriptor-to-mechanism mappings.
    
    Returns:
        Formatted string describing all mappings and their metadata
    """
    output = []
    output.append("Physics Mappings: Descriptor to Physical Mechanism")
    output.append("=" * 50)
    
    for descriptor, mechanism in MAPPINGS.items():
        meta = METADATA.get(descriptor, {})
        output.append(f"\n{descriptor}:")
        output.append(f"  Mechanism: {mechanism}")
        output.append(f"  Category: {meta.get('category', 'N/A')}")
        output.append(f"  Mechanism Class: {meta.get('mechanism_class', 'N/A')}")
        output.append(f"  Theoretical Basis: {meta.get('theoretical_basis', 'N/A')}")
        output.append(f"  Expected Correlation: {meta.get('expected_correlation', 'N/A')}")
        
    return "\n".join(output)