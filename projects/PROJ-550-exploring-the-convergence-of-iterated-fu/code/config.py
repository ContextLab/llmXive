"""
Configuration settings for the IFS convergence research project.

This module defines all global constants used across the research pipeline,
including simulation parameters, grid sizes, thresholds, and file paths.
"""

import os
from pathlib import Path

# Project root directory (assumes code/ is at projects/PROJ-.../code)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Random seed for reproducibility
SEED: int = 42

# Grid sizes for Lipschitz estimation
# Contractive maps: standard resolution
GRID_SIZE_CONTRACTIVE: int = 1000
# Non-contractive maps: denser grid for better validation of unstable dynamics
GRID_SIZE_NON_CONTRACTIVE: int = 5000

# Number of scale levels for box-counting dimension calculation
# Mandated by Constitution Principle VI
BOX_COUNTING_SCALES: int = 50

# Iteration counts for Chaos Game simulation
ITERATIONS_DEFAULT: int = 1_000_000
ITERATIONS_EDGE_CASE: int = 5_000_000  # For L ≈ 1.0 cases

# Bounding box for divergence detection and simulation domain
# Domain: [-1.0, 2.0] x [-1.0, 2.0]
BOUNDING_BOX_MIN: float = -1.0
BOUNDING_BOX_MAX: float = 2.0

# Convergence threshold for Wasserstein-2 distance
W2_THRESHOLD: float = 0.01

# File path mappings (relative to project root)
FILE_PATHS: dict = {
    "raw": str(_PROJECT_ROOT / "data" / "raw"),
    "derived": str(_PROJECT_ROOT / "data" / "derived"),
    "visualizations": str(_PROJECT_ROOT / "data" / "derived" / "visualizations"),
    "ruliad_samples": str(_PROJECT_ROOT / "data" / "derived" / "ruliad_samples"),
    "checksums": str(_PROJECT_ROOT / "data" / "checksums.json"),
    "benchmarks": str(_PROJECT_ROOT / "data" / "derived" / "benchmark_results.parquet"),
    "instances": str(_PROJECT_ROOT / "data" / "raw" / "ifs_instances.parquet"),
    "chaos_results": str(_PROJECT_ROOT / "data" / "derived" / "chaos_results.parquet"),
    "topology_results": str(_PROJECT_ROOT / "data" / "derived" / "topology_results.parquet"),
    "analysis_summary": str(_PROJECT_ROOT / "data" / "derived" / "analysis_summary.csv"),
    "excluded_log": str(_PROJECT_ROOT / "data" / "raw" / "excluded_instances.log"),
}