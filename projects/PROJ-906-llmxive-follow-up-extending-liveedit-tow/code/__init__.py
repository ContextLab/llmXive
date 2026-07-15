"""
llmXive research pipeline package.

This package contains modules for:
- Data models and processing
- Model implementations (baseline, flow-coherence)
- Metrics computation
- Analysis and reporting
- Configuration management
"""

from .config import ExperimentConfig, CUTOFFS, get_default_config, ensure_directories

__version__ = "0.1.0"
__all__ = [
    "ExperimentConfig",
    "CUTOFFS",
    "get_default_config",
    "ensure_directories",
]