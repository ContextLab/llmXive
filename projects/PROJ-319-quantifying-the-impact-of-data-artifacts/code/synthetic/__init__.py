"""
Synthetic data generation and artifact injection.
"""
from .generator import generate_nebula_base, calculate_true_ellipticity, calculate_true_asymmetry, generate_synthetic_nebula, main
from .artifacts import inject_noise, clip_saturation

__all__ = [
    "generate_nebula_base",
    "calculate_true_ellipticity",
    "calculate_true_asymmetry",
    "generate_synthetic_nebula",
    "main",
    "inject_noise",
    "clip_saturation",
]
