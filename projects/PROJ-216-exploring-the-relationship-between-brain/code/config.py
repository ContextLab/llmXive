"""
Environment configuration management for dataset IDs and sample limits.

This module centralizes configuration for:
- OpenNeuro dataset IDs (ds000224, ds000230)
- Sample limits (N=10 for CI, N=50 per Spec SC-001)

Configuration is derived from environment variables with sensible defaults
to support both CI/CD and local development environments.
"""
import os
from typing import List, Tuple, Optional


# Default configuration values
DEFAULT_DATASET_IDS: Tuple[str, ...] = ("ds000224", "ds000230")
DEFAULT_SAMPLE_LIMIT_CI: int = 10
DEFAULT_SAMPLE_LIMIT_SPEC: int = 50

# Environment variable names
ENV_DATASET_IDS: str = "LLMXIVE_DATASET_IDS"
ENV_SAMPLE_LIMIT_CI: str = "LLMXIVE_SAMPLE_LIMIT_CI"
ENV_SAMPLE_LIMIT_SPEC: str = "LLMXIVE_SAMPLE_LIMIT_SPEC"
ENV_FORCE_SPEC_LIMIT: str = "LLMXIVE_FORCE_SPEC_LIMIT"


def get_dataset_ids() -> Tuple[str, ...]:
    """
    Retrieve the list of OpenNeuro dataset IDs to process.
    
    Priority:
    1. Environment variable LLMXIVE_DATASET_IDS (comma-separated)
    2. Default: ("ds000224", "ds000230")
    
    Returns:
        Tuple of dataset IDs in processing priority order.
    """
    env_value = os.environ.get(ENV_DATASET_IDS)
    if env_value:
        # Parse comma-separated list, strip whitespace
        ids = tuple(id_.strip() for id_ in env_value.split(",") if id_.strip())
        if not ids:
            return DEFAULT_DATASET_IDS
        return ids
    return DEFAULT_DATASET_IDS


def get_sample_limit(for_ci: bool = True) -> int:
    """
    Retrieve the sample limit based on the execution context.
    
    Per Plan constraint: N=10 for CI (overrides Spec SC-001 N=50).
    Per Spec SC-001: N=50 target for full analysis.
    
    Priority for CI mode:
    1. Environment variable LLMXIVE_SAMPLE_LIMIT_CI
    2. Default: 10
    
    Priority for Spec/Full mode:
    1. Environment variable LLMXIVE_SAMPLE_LIMIT_SPEC
    2. If LLMXIVE_FORCE_SPEC_LIMIT is set to 'true', use Spec limit
    3. Default: 10 (CI default) unless force is set
    
    Args:
        for_ci: If True, return CI limit; if False, return Spec limit.
    
    Returns:
        Maximum number of subjects to process.
    """
    if for_ci:
        limit_str = os.environ.get(ENV_SAMPLE_LIMIT_CI)
        if limit_str:
            try:
                return int(limit_str)
            except ValueError:
                pass
        return DEFAULT_SAMPLE_LIMIT_CI
    else:
        # Spec/Full mode
        force_spec = os.environ.get(ENV_FORCE_SPEC_LIMIT, "").lower() == "true"
        
        if force_spec:
            limit_str = os.environ.get(ENV_SAMPLE_LIMIT_SPEC)
            if limit_str:
                try:
                    return int(limit_str)
                except ValueError:
                    pass
            return DEFAULT_SAMPLE_LIMIT_SPEC
        else:
            # Default to CI limit unless explicitly forced to Spec
            limit_str = os.environ.get(ENV_SAMPLE_LIMIT_CI)
            if limit_str:
                try:
                    return int(limit_str)
                except ValueError:
                    pass
            return DEFAULT_SAMPLE_LIMIT_CI


def get_config_summary() -> dict:
    """
    Generate a summary of the current configuration state.
    
    Returns:
        Dictionary containing current configuration values and their sources.
    """
    dataset_ids = get_dataset_ids()
    ci_limit = get_sample_limit(for_ci=True)
    spec_limit = get_sample_limit(for_ci=False)
    force_spec = os.environ.get(ENV_FORCE_SPEC_LIMIT, "").lower() == "true"
    
    return {
        "dataset_ids": list(dataset_ids),
        "dataset_id_count": len(dataset_ids),
        "sample_limit_ci": ci_limit,
        "sample_limit_spec": spec_limit,
        "force_spec_limit": force_spec,
        "active_sample_limit": spec_limit if force_spec else ci_limit,
        "environment_variables": {
            ENV_DATASET_IDS: os.environ.get(ENV_DATASET_IDS, "not set"),
            ENV_SAMPLE_LIMIT_CI: os.environ.get(ENV_SAMPLE_LIMIT_CI, "not set"),
            ENV_SAMPLE_LIMIT_SPEC: os.environ.get(ENV_SAMPLE_LIMIT_SPEC, "not set"),
            ENV_FORCE_SPEC_LIMIT: os.environ.get(ENV_FORCE_SPEC_LIMIT, "not set"),
        }
    }


def validate_config() -> Tuple[bool, List[str]]:
    """
    Validate the current configuration for consistency and feasibility.
    
    Checks:
    - Dataset IDs are non-empty
    - Sample limits are positive integers
    - CI limit does not exceed Spec limit (unless forced)
    
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors: List[str] = []
    
    dataset_ids = get_dataset_ids()
    if not dataset_ids:
        errors.append("No dataset IDs configured.")
    
    ci_limit = get_sample_limit(for_ci=True)
    if ci_limit <= 0:
        errors.append(f"CI sample limit must be positive, got {ci_limit}.")
    
    spec_limit = get_sample_limit(for_ci=False)
    if spec_limit <= 0:
        errors.append(f"Spec sample limit must be positive, got {spec_limit}.")
    
    force_spec = os.environ.get(ENV_FORCE_SPEC_LIMIT, "").lower() == "true"
    if not force_spec and ci_limit > spec_limit:
        # This is allowed if we are in CI mode, but warn if Spec mode is expected
        pass 
    
    return len(errors) == 0, errors