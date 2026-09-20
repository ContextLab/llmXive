"""
Data pipeline modules for impurity clustering and grain boundary segregation.

This package provides utilities for:
- Downloading bulk configurations from external databases (MP/OQMD).
- Building grain boundary supercells and inserting impurities.
- Computing clustering descriptors (RDF, pair correlation, Voronoi).
- Simulating segregation energies using EAM potentials.
"""
from .download import download_bulk_configs
from .gb_builder import build_gb_supercell, insert_impurity
from .descriptors import compute_rdf_peak, compute_pair_correlation, compute_voronoi_neighbor_counts
from .simulate_energy import run_simulation
from .preprocessing import filter_zero_impurity_configs, generate_preprocessing_report
from .descriptor_filter import compute_vif, generate_report

__all__ = [
    "download_bulk_configs",
    "build_gb_supercell",
    "insert_impurity",
    "compute_rdf_peak",
    "compute_pair_correlation",
    "compute_voronoi_neighbor_counts",
    "run_simulation",
    "filter_zero_impurity_configs",
    "generate_preprocessing_report",
    "compute_vif",
    "generate_report",
]
