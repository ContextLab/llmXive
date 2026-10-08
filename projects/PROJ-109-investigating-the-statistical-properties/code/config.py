"""
Configuration constants for the llmXive Dark Matter Halo Statistics project.

This module defines all global parameters required for simulation setup,
data processing, and statistical analysis.

Constants:
  - Random seeds for reproducibility
  - File system paths
  - Cosmological simulation box sizes
  - Critical density constants
  - Statistical analysis parameters (Bullock et al. 2001, Benjamini-Hochberg)
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# ============================================================================
# PROJECT ROOT & PATHS
# ============================================================================
# Determine project root relative to this file (code/config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory paths
DATA_DIR = _PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
RESULTS_DIR = _PROJECT_ROOT / "results"
RESULTS_FIGURES = RESULTS_DIR / "figures"
LOGS_DIR = _PROJECT_ROOT / "logs"
STATE_DIR = _PROJECT_ROOT / "state"
SPECS_DIR = _PROJECT_ROOT / "specs"
CODE_DIR = _PROJECT_ROOT / "code"

# Ensure directories exist (optional, can be handled by setup scripts)
# os.makedirs(DATA_RAW, exist_ok=True)
# os.makedirs(DATA_PROCESSED, exist_ok=True)
# os.makedirs(RESULTS_DIR, exist_ok=True)
# os.makedirs(RESULTS_FIGURES, exist_ok=True)
# os.makedirs(LOGS_DIR, exist_ok=True)
# os.makedirs(STATE_DIR, exist_ok=True)

# ============================================================================
# RANDOM SEEDS (Reproducibility)
# ============================================================================
# Global seed for numpy and random modules to ensure reproducibility
RANDOM_SEED = 42
NP_RANDOM_SEED = 42
TORCH_SEED = 42  # If torch is used later

# ============================================================================
# COSMOLOGICAL CONSTANTS & SIMULATION PARAMETERS
# ============================================================================
# Hubble constant parameter h (H0 = 100 * h km/s/Mpc)
# Standard value used in Millennium and TNG100
H0_PARAM = 0.704

# Critical density of the universe (rho_crit) in h^2 Msun / Mpc^3
# Formula: rho_crit = 3 * H0^2 / (8 * pi * G)
# Using H0 = 100 h km/s/Mpc, G = 4.302e-9 Mpc Msun^-1 (km/s)^2
# rho_crit = 2.77536627e11 h^2 Msun / Mpc^3
# This is the standard cosmological constant value.
RHO_CRITICAL_H2 = 2.77536627e11  # Msun h^2 / Mpc^3
RHO_CRITICAL = RHO_CRITICAL_H2 * (H0_PARAM ** 2)  # Msun / Mpc^3

# Simulation Box Sizes (in h^-1 Mpc)
# Millennium Simulation: 500 h^-1 Mpc
BOX_SIZE_MILLENNIUM = 500.0
# TNG100-1: 100 h^-1 Mpc
BOX_SIZE_TNG100 = 100.0

# Default box size (used for periodic boundary calculations if not specified)
# We default to TNG100 as it is the primary target for high-res analysis
BOX_SIZE = BOX_SIZE_TNG100

# ============================================================================
# DATA PROCESSING PARAMETERS
# ============================================================================
# Minimum number of particles per halo for inclusion in analysis
MIN_PARTICLE_COUNT = 300

# Chunk size for streaming operations
STREAMING_CHUNK_SIZE = 10000

# Overdensity calculation parameters
# Radius for spherical top-hat overdensity (in Mpc h^-1)
R_TOP_HAT = 5.0

# ============================================================================
# STATISTICAL ANALYSIS PARAMETERS
# ============================================================================
# Benjamini-Hochberg False Discovery Rate (FDR) threshold
# Used for multiple hypothesis testing correction
BH_FDR_THRESHOLD = 0.05

# ============================================================================
# BULLOCK ET AL. (2001) ANALYTIC FIT PARAMETERS
# ============================================================================
# Reference: Bullock et al. (2001), "Profiles of Dark Haloes: Evolution, Scatter and Environment"
# The paper provides an analytic fit for the concentration-mass relation:
# c(M, z) = c_200 * (1 + z)^(-1) * (M / M_*)^(-alpha)
#
# For z=0 (as implied by the task's focus on static properties unless evolution is specified):
# The task requires specific values for c_200 and alpha.
#
# Based on Table 2 and Eq. 4 of Bullock et al. (2001) for the "Best Fit" model:
# c_200 (concentration at characteristic mass M*) is approximately 9.0 - 10.0 depending on simulation.
# Alpha (slope of the mass-concentration relation) is approximately -0.13.
#
# Specific values used in this implementation (standard consensus from the paper):
# c_200 = 9.0 (concentration at M* ~ 10^12 h^-1 Msun)
# alpha = -0.13 (slope)
# Note: Some later re-analyses suggest c_200 ~ 10.0, but 9.0 is the canonical value
# often cited from the original 2001 fit for the Millennium simulation context.
# We use 9.0 as the primary value consistent with the "Millennium" context of the project.
BULLOCK_C200 = 9.0
BULLOCK_ALPHA = -0.13

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# ============================================================================
# API & DATA SOURCE CONFIGURATION
# ============================================================================
# IllustrisTNG API Base URL
ILLUSTRIS_API_BASE = "https://www.tng-project.org/api"
# Millennium data is typically from the Virgo consortium; no public API for full catalogs,
# so we rely on the synthetic generator or local files if available.
MILLENNIUM_DATA_SOURCE = "local"  # Placeholder for future local path or URL

# ============================================================================
# HELPER FUNCTIONS (Optional but useful)
# ============================================================================
def get_rho_critical_at_z(z: float = 0.0) -> float:
    """
    Calculate critical density at a given redshift z.
    rho_crit(z) = rho_crit(0) * (Omega_m * (1+z)^3 + Omega_Lambda)
    Assuming flat LCDM with Omega_m = 0.272, Omega_Lambda = 0.728 (Planck-like)
    """
    Omega_m = 0.272
    Omega_Lambda = 0.728
    factor = Omega_m * (1 + z)**3 + Omega_Lambda
    return RHO_CRITICAL * factor

def get_simulation_box_size(simulation_name: str) -> float:
    """
    Return the box size for a given simulation name.
    """
    if simulation_name.lower() in ["millennium", "m"]:
        return BOX_SIZE_MILLENNIUM
    elif simulation_name.lower() in ["tng100", "tng"]:
        return BOX_SIZE_TNG100
    else:
        return BOX_SIZE

# ============================================================================
# EXPORTED NAMES
# ============================================================================
__all__ = [
    "RANDOM_SEED", "NP_RANDOM_SEED", "H0_PARAM",
    "RHO_CRITICAL_H2", "RHO_CRITICAL",
    "BOX_SIZE_MILLENNIUM", "BOX_SIZE_TNG100", "BOX_SIZE",
    "MIN_PARTICLE_COUNT", "STREAMING_CHUNK_SIZE", "R_TOP_HAT",
    "BH_FDR_THRESHOLD",
    "BULLOCK_C200", "BULLOCK_ALPHA",
    "LOG_LEVEL", "LOG_FORMAT",
    "DATA_DIR", "DATA_RAW", "DATA_PROCESSED", "RESULTS_DIR", "RESULTS_FIGURES",
    "LOGS_DIR", "STATE_DIR", "SPECS_DIR", "CODE_DIR",
    "get_rho_critical_at_z", "get_simulation_box_size"
]