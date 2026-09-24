"""
Data module initialization.
Exports public interfaces for data processing, descriptor computation, and alloy system tagging.
"""
from .download import download_bulk_configs, load_schema, validate_dataset_schema
from .gb_builder import build_gb_supercell, insert_impurity, save_structure
from .descriptors import (
    get_interface_atoms,
    compute_rdf_peak,
    compute_pair_correlation,
    compute_voronoi_neighbor_counts,
    run_descriptor_computation
)
from .alloy_systems import (
    get_crystal_system,
    generate_alloy_system_id,
    extract_alloy_systems_from_descriptors,
    save_alloy_systems,
    run_alloy_system_extraction
)
from .descriptor_filter import compute_vif, generate_report
from .simulate_energy import apply_structural_perturbation, calculate_segregation_energy, run_simulation
from .preprocessing import filter_zero_impurity_configs

__all__ = [
    "download_bulk_configs",
    "load_schema",
    "validate_dataset_schema",
    "build_gb_supercell",
    "insert_impurity",
    "save_structure",
    "get_interface_atoms",
    "compute_rdf_peak",
    "compute_pair_correlation",
    "compute_voronoi_neighbor_counts",
    "run_descriptor_computation",
    "get_crystal_system",
    "generate_alloy_system_id",
    "extract_alloy_systems_from_descriptors",
    "save_alloy_systems",
    "run_alloy_system_extraction",
    "compute_vif",
    "generate_report",
    "apply_structural_perturbation",
    "calculate_segregation_energy",
    "run_simulation",
    "filter_zero_impurity_configs"
]