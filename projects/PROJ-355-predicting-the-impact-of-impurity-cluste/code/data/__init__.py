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
from .descriptors import compute_rdf, compute_pair_correlation, compute_voronoi_counts
from .simulate_energy import run_simulation

__all__ = [
    "download_bulk_configs",
    "build_gb_supercell",
    "insert_impurity",
    "compute_rdf",
    "compute_pair_correlation",
    "compute_voronoi_counts",
    "run_simulation",
]
