"""
Utility module for the regression sensitivity analysis pipeline.

This package provides shared utilities including:
- Configuration management (loading datasets, seeds, sample size tiers)
- Data validation and checksumming
- Logging infrastructure
- Checkpointing mechanisms
"""

from .config import (
    load_config,
    get_dataset_list,
    get_random_seed,
    SAMPLE_SIZE_TIERS,
)
from .validation import (
    compute_checksum,
    validate_checksum,
    validate_dataframe,
)
from .logger import (
    setup_logger,
    get_logger,
)
from .checkpoint import (
    CheckpointManager,
    load_checkpoint,
    save_checkpoint,
)

__all__ = [
    # Config
    "load_config",
    "get_dataset_list",
    "get_random_seed",
    "SAMPLE_SIZE_TIERS",
    # Validation
    "compute_checksum",
    "validate_checksum",
    "validate_dataframe",
    # Logging
    "setup_logger",
    "get_logger",
    # Checkpointing
    "CheckpointManager",
    "load_checkpoint",
    "save_checkpoint",
]