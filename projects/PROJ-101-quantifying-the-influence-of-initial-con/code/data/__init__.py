"""
Data subpackage for generating and loading chaotic trajectory data.

Provides:
- Trajectory generation from coupled Lorenz oscillators
- Noise injection utilities
- Data loading and saving with checksums
"""
from .generator import (
    generate_trajectory,
    generate_coupled_oscillators,
    inject_noise,
    HighNoiseWarning,
    UnphysicalTrajectoryError
)
from .loader import (
    save_trajectory,
    load_trajectory,
    verify_checksum
)

__all__ = [
    'generate_trajectory',
    'generate_coupled_oscillators',
    'inject_noise',
    'HighNoiseWarning',
    'UnphysicalTrajectoryError',
    'save_trajectory',
    'load_trajectory',
    'verify_checksum'
]
