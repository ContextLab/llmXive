# Data module
"""
This module contains utilities for data handling, including:
- Downloading bulk configurations
- Building GB supercells
- Computing clustering descriptors
- Simulating segregation energies
- Preprocessing and filtering data
"""

from .download import load_schema, validate_dataset, download_bulk_configs, main as download_main
from .gb_builder import insert_impurity, build_gb_supercell, save_structure, main as gb_builder_main
from .descriptors import (
    get_interface_atoms,
    compute_rdf_peak,
    compute_pair_correlation,
    compute_voronoi_neighbor_counts,
    run_descriptor_computation,
    main as descriptors_main,
)
from .simulate_energy import (
    get_project_potential_path,
    get_simulation_config,
    apply_structural_perturbation,
    calculate_segregation_energy,
    run_simulation,
    main as simulate_main,
)
from .preprocessing import (
    filter_zero_impurity_configs,
    generate_preprocessing_report,
    run_preprocessing_filter,
    main as preprocessing_main,
)
from .descriptor_filter import (
    load_descriptors,
    compute_vif,
    generate_report,
    run_vif_analysis,
    main as descriptor_filter_main,
)

__all__ = [
    "load_schema",
    "validate_dataset",
    "download_bulk_configs",
    "download_main",
    "insert_impurity",
    "build_gb_supercell",
    "save_structure",
    "gb_builder_main",
    "get_interface_atoms",
    "compute_rdf_peak",
    "compute_pair_correlation",
    "compute_voronoi_neighbor_counts",
    "run_descriptor_computation",
    "descriptors_main",
    "get_project_potential_path",
    "get_simulation_config",
    "apply_structural_perturbation",
    "calculate_segregation_energy",
    "run_simulation",
    "simulate_main",
    "filter_zero_impurity_configs",
    "generate_preprocessing_report",
    "run_preprocessing_filter",
    "preprocessing_main",
    "load_descriptors",
    "compute_vif",
    "generate_report",
    "run_vif_analysis",
    "descriptor_filter_main",
]
