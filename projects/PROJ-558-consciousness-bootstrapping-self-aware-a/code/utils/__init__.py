"""
Utility functions for logging, configuration, and validation.
"""
from .logging import get_logger, setup_logging, ConsciousnessBootstrappingError
from .config import validate_config, Config
from .memory_profiler import get_current_memory_mb, get_peak_memory_mb