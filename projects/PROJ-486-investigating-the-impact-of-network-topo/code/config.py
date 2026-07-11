"""
Configuration settings for the network topology entrainment analysis.

This module defines immutable constants and configuration parameters
used throughout the research pipeline.
"""

import os
from typing import Dict, Optional

# Atlas types supported by the analysis pipeline
# These correspond to standard brain parcellation schemes
# Defined as a tuple for immutability as per task requirement
ATLAS_TYPES = ('Schaefer', 'AAL', 'Power 264')

# Random seed for reproducibility across simulations and analyses
RANDOM_SEED = 42

# Default paths relative to project root
DATA_DIR = "data"
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
DATA_VIS_DIR = "data/visualizations"
CODE_DIR = "code"
TESTS_DIR = "tests"
DOCS_DIR = "docs"

# Analysis parameters
DEFAULT_CORRELATION_THRESHOLD = 0.0
MIN_SAMPLE_SIZE = 30
VIF_COLLINEARITY_THRESHOLD = 5.0

# Statistical correction methods
MULTIPLE_COMPARISON_METHOD = 'holm'

# File extensions
CSV_EXT = '.csv'
JSON_EXT = '.json'
PNG_EXT = '.png'
YAML_EXT = '.yaml'

# Atlas-specific configuration
# Maps atlas names to their specific data path suffixes and expected node counts
ATLAS_CONFIG: Dict[str, Dict] = {
    'Schaefer': {
        'path_suffix': 'schaefer',
        'node_count': 400,
        'description': 'Schaefer 2018 400 Parcellation'
    },
    'AAL': {
        'path_suffix': 'aal',
        'node_count': 116,
        'description': 'Automated Anatomical Labeling (AAL)'
    },
    'Power 264': {
        'path_suffix': 'power264',
        'node_count': 264,
        'description': 'Power 2011 264 ROI'
    }
}

def get_atlas_path(atlas_type: str, sub_dir: str = "raw") -> str:
    """
    Construct the full path for a specific atlas data directory.

    Args:
        atlas_type: One of 'Schaefer', 'AAL', or 'Power 264'
        sub_dir: Subdirectory within the data folder (default: 'raw')

    Returns:
        Full relative path string

    Raises:
        ValueError: If atlas_type is not in ATLAS_TYPES
    """
    if atlas_type not in ATLAS_TYPES:
        raise ValueError(f"Unsupported atlas type: {atlas_type}. "
                       f"Must be one of {ATLAS_TYPES}")

    config = ATLAS_CONFIG[atlas_type]
    base_dir = DATA_RAW_DIR if sub_dir == "raw" else (
        DATA_PROCESSED_DIR if sub_dir == "processed" else DATA_VIS_DIR
    )
    return os.path.join(base_dir, config['path_suffix'])

def get_atlas_node_count(atlas_type: str) -> int:
    """
    Retrieve the expected number of nodes for a given atlas.

    Args:
        atlas_type: One of 'Schaefer', 'AAL', or 'Power 264'

    Returns:
        Integer node count

    Raises:
        ValueError: If atlas_type is not in ATLAS_TYPES
    """
    if atlas_type not in ATLAS_TYPES:
        raise ValueError(f"Unsupported atlas type: {atlas_type}. "
                       f"Must be one of {ATLAS_TYPES}")
    return ATLAS_CONFIG[atlas_type]['node_count']