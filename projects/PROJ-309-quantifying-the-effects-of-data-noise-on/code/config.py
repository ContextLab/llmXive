"""
Configuration constants and parameters for the research pipeline.
"""
import numpy as np
from scipy.stats import t, norm

# Simulation Seeds
SEED_BASE = 42
SEEDS = [42, 123, 456, 789, 101112]

# SNR Levels (dB) - Spanning low to high, including near-zero conditions
# Includes negative dB (noise > signal), 0dB (noise = signal), and high SNR
SNR_LEVELS_DB = [-10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 30.0]

# System Parameters
# Lorenz Attractor (Standard parameters)
LORENZ_SIGMA = 10.0
LORENZ_RHO = 28.0
LORENZ_BETA = 8.0 / 3.0
LORENZ_PARAMS = {
    "sigma": LORENZ_SIGMA,
    "rho": LORENZ_RHO,
    "beta": LORENZ_BETA
}

# Rössler Attractor (Standard parameters)
ROSSLER_A = 0.2
ROSSLER_B = 0.2
ROSSLER_C = 5.7
ROSSLER_PARAMS = {
    "a": ROSSLER_A,
    "b": ROSSLER_B,
    "c": ROSSLER_C
}

# Integration Parameters
DT = 0.01
TIME_STEP_COUNT = 10000
TOTAL_TIME = DT * TIME_STEP_COUNT

# Batch Size Limits
MAX_BATCH_SIZE = 100

# Literature Reference Ranges for Validation
# Source: Standard literature values for Lorenz attractor
# Correlation Dimension (D2) ≈ 2.06 ± 0.05
# Lyapunov Exponent (LE) ≈ 0.90 ± 0.05
# Note: These are established values from chaotic dynamics literature.
LITERATURE_LORENZ = {
    "correlation_dimension": {
        "mean": 2.06,
        "std": 0.05,
        "tolerance_pct": 5.0
    },
    "lyapunov_exponent": {
        "mean": 0.90,
        "std": 0.05,
        "tolerance_pct": 5.0
    }
}

# Power Analysis Parameters
# Target: 80% power, alpha=0.05
# Effect size estimation based on expected variance in noisy dynamical systems
# Calculated sample size N per group for a 2-sample t-test assuming medium effect size (Cohen's d = 0.5)
# Using standard power analysis formula: N = 2 * ((Z_alpha + Z_beta) / d)^2
# Z_alpha (0.05) ≈ 1.96, Z_beta (0.20) ≈ 0.84 -> N ≈ 2 * (2.8/0.5)^2 ≈ 62.72 -> rounded to 64
POWER_ANALYSIS = {
    "power": 0.80,
    "alpha": 0.05,
    "estimated_effect_size": 0.5,  # Medium effect size (Cohen's d)
    "calculated_sample_size": 64   # N per group for 2-sample t-test
}

# Noise Types
NOISE_TYPES = ["gaussian", "quantization"]

# File Paths
DATA_DIR = "data"
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
FIGURES_DIR = "figures"
CHECKSUMS_FILE = "data/checksums.json"