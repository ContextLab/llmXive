"""
Configuration constants and path resolution for the llmXive pipeline.

This module defines all project paths, seeds, model configurations, and
placeholder values for deferred parameters. All None values must be
resolved at runtime via CLI arguments or environment variables.
"""

import os
import argparse
from pathlib import Path
from typing import Final, Dict, Any, List, Optional

# Project Root
PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent

# Directory Paths
CODE_DIR: Final = PROJECT_ROOT / "code"
DATA_DIR: Final = PROJECT_ROOT / "data"
DATA_RAW: Final = DATA_DIR / "raw"
DATA_CURATED: Final = DATA_DIR / "curated"
DATA_RESULTS: Final = DATA_DIR / "results"
FIGURES_DIR: Final = PROJECT_ROOT / "figures"
SPECS_DIR: Final = PROJECT_ROOT / "specs" / "001-llmxive-follow-up-extending-swe-explore"
CONTRACTS_DIR: Final = SPECS_DIR / "contracts"
STATE_DIR: Final = PROJECT_ROOT / "state"
PAPER_DIR: Final = PROJECT_ROOT / "paper"
DOCS_DIR: Final = PROJECT_ROOT / "docs"

# Ensure directories exist
def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    dirs = [
        CODE_DIR, DATA_DIR, DATA_RAW, DATA_CURATED, DATA_RESULTS,
        FIGURES_DIR, SPECS_DIR, CONTRACTS_DIR, STATE_DIR, PAPER_DIR, DOCS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# --- Configuration Constants ---

# Deferred Parameters (Must be resolved at runtime)
HARD_INSTANCE_PERCENTILE: Optional[float] = None  # [deferred] - set at runtime or via CLI
SWEEP_SAMPLE_SIZE: Optional[int] = None  # [deferred] - validated by T024a
MIN_SYNTHETIC_ISSUES: Optional[int] = None  # [deferred]
VALIDATION_SAMPLE_SIZE: Optional[int] = None  # [deferred]

# Concrete Constants
COVERAGE_COLUMN_NAME: Final = 'initial_coverage'
SWEEP_SEED: Final = 42
TURN_LIMITS: Final = [1, 2, 3]
TIE_THRESHOLD: Final = 0.50  # Concrete threshold for statistical routing (FR-006)
MAX_RUNTIME_HOURS: Final = 6
MODEL_PRECISION: Final = '8-bit'

# Model Configuration
MODEL_NAME: Final = "Qwen/Qwen1.5-1.8B-Chat"  # Default model
MAX_TOKENS: Final = 2048

# --- Runtime Resolution ---

def resolve_deferred_config(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Resolve deferred configuration values from CLI arguments or environment variables.
    
    Args:
        args: Parsed command line arguments.
    
    Returns:
        Dictionary of resolved configuration values.
    """
    resolved = {}
    
    # Resolve HARD_INSTANCE_PERCENTILE
    if hasattr(args, 'hard_percentile') and args.hard_percentile is not None:
        resolved['HARD_INSTANCE_PERCENTILE'] = float(args.hard_percentile)
    elif os.getenv('HARD_INSTANCE_PERCENTILE'):
        resolved['HARD_INSTANCE_PERCENTILE'] = float(os.getenv('HARD_INSTANCE_PERCENTILE'))
    else:
        resolved['HARD_INSTANCE_PERCENTILE'] = None  # Will fail later if not provided
    
    # Resolve SWEEP_SAMPLE_SIZE
    if hasattr(args, 'sweep_size') and args.sweep_size is not None:
        resolved['SWEEP_SAMPLE_SIZE'] = int(args.sweep_size)
    elif os.getenv('SWEEP_SAMPLE_SIZE'):
        resolved['SWEEP_SAMPLE_SIZE'] = int(os.getenv('SWEEP_SAMPLE_SIZE'))
    else:
        resolved['SWEEP_SAMPLE_SIZE'] = None
    
    # Resolve MIN_SYNTHETIC_ISSUES
    if hasattr(args, 'min_synthetic') and args.min_synthetic is not None:
        resolved['MIN_SYNTHETIC_ISSUES'] = int(args.min_synthetic)
    elif os.getenv('MIN_SYNTHETIC_ISSUES'):
        resolved['MIN_SYNTHETIC_ISSUES'] = int(os.getenv('MIN_SYNTHETIC_ISSUES'))
    else:
        resolved['MIN_SYNTHETIC_ISSUES'] = None
    
    # Resolve VALIDATION_SAMPLE_SIZE
    if hasattr(args, 'validation_size') and args.validation_size is not None:
        resolved['VALIDATION_SAMPLE_SIZE'] = int(args.validation_size)
    elif os.getenv('VALIDATION_SAMPLE_SIZE'):
        resolved['VALIDATION_SAMPLE_SIZE'] = int(os.getenv('VALIDATION_SAMPLE_SIZE'))
    else:
        resolved['VALIDATION_SAMPLE_SIZE'] = None
        
    return resolved

def get_path(key: str) -> Path:
    """
    Retrieve a project path by key name.
    
    Args:
        key: One of 'code', 'raw', 'curated', 'results', 'figures', 'specs', 'contracts', 'state', 'paper', 'docs'.
    
    Returns:
        Path object.
    
    Raises:
        ValueError: If key is unknown.
    """
    mapping = {
        'code': CODE_DIR,
        'raw': DATA_RAW,
        'curated': DATA_CURATED,
        'results': DATA_RESULTS,
        'figures': FIGURES_DIR,
        'specs': SPECS_DIR,
        'contracts': CONTRACTS_DIR,
        'state': STATE_DIR,
        'paper': PAPER_DIR,
        'docs': DOCS_DIR
    }
    if key not in mapping:
        raise ValueError(f"Unknown path key: {key}")
    return mapping[key]

def get_config_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current configuration state.
    
    Returns:
        Dictionary containing all configuration values.
    """
    return {
        'project_root': str(PROJECT_ROOT),
        'hard_instance_percentile': HARD_INSTANCE_PERCENTILE,
        'coverage_column_name': COVERAGE_COLUMN_NAME,
        'sweep_sample_size': SWEEP_SAMPLE_SIZE,
        'sweep_seed': SWEEP_SEED,
        'turn_limits': TURN_LIMITS,
        'min_synthetic_issues': MIN_SYNTHETIC_ISSUES,
        'validation_sample_size': VALIDATION_SAMPLE_SIZE,
        'tie_threshold': TIE_THRESHOLD,
        'max_runtime_hours': MAX_RUNTIME_HOURS,
        'model_precision': MODEL_PRECISION,
        'model_name': MODEL_NAME,
        'max_tokens': MAX_TOKENS
    }

# Initialize directories on module import
ensure_directories()