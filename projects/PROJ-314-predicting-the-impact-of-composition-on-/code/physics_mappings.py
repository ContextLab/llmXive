"""
Physics Mappings Module.
Maps descriptors to physical mechanisms in fracture mechanics.
"""
from typing import Dict, Any

DESCRIPTOR_MAPPINGS = {
    "mean_atomic_radius": {
        "mechanism": "Atomic packing density",
        "description": "Larger atoms may lead to lower packing density and reduced fracture toughness."
    },
    "electronegativity_std": {
        "mechanism": "Bond ionicity variance",
        "description": "Higher variance in electronegativity indicates mixed bonding character."
    },
    "valence_electron_concentration": {
        "mechanism": "Electronic bonding strength",
        "description": "Higher VEC often correlates with stronger metallic/covalent bonding."
    },
    "cation_size_variance": {
        "mechanism": "Grain boundary stability",
        "description": "Variance in cation sizes affects grain boundary cohesion."
    },
    "range_uncertainty": {
        "mechanism": "Measurement uncertainty",
        "description": "Higher uncertainty indicates less reliable data."
    }
}

def get_mechanism(descriptor: str) -> str:
    """Get the physical mechanism for a descriptor."""
    return DESCRIPTOR_MAPPINGS.get(descriptor, {}).get("mechanism", "Unknown")

def get_mechanism_metadata(descriptor: str) -> Dict[str, Any]:
    """Get full metadata for a descriptor's mechanism."""
    return DESCRIPTOR_MAPPINGS.get(descriptor, {"mechanism": "Unknown", "description": "No mapping found."})

def list_all_descriptors() -> List[str]:
    """List all mapped descriptors."""
    return list(DESCRIPTOR_MAPPINGS.keys())

def describe_all_mappings() -> Dict[str, Dict[str, str]]:
    """Describe all mappings."""
    return DESCRIPTOR_MAPPINGS
