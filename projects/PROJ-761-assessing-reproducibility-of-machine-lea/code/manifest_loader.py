"""
Manifest loader and validator for PROJ-761.

This module provides functionality to load and validate the data manifest
(data/manifest.yaml) ensuring required fields are present as per FR-001.

Required fields:
- doi: Digital Object Identifier
- repo_url: Source code repository URL
- dataset_name: Name of the dataset
- reported_metrics: Dictionary containing at least MAE, R2, and Spearman rho
"""

import os
import yaml
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


REQUIRED_TOP_LEVEL_KEYS = {
    "doi",
    "repo_url",
    "dataset_name",
    "reported_metrics"
}

REQUIRED_METRIC_KEYS = {
    "mae",
    "r2",
    "spearman_rho"
}

MANIFEST_PATH = Path("data/manifest.yaml")


class ManifestValidationError(Exception):
    """Raised when manifest validation fails."""
    pass


def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the manifest YAML file.

    Args:
        manifest_path: Path to the manifest file. Defaults to data/manifest.yaml.

    Returns:
        Dictionary containing the manifest contents.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    path = manifest_path if manifest_path else MANIFEST_PATH

    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found at: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if data is None:
        raise yaml.YAMLError("Manifest file is empty or contains only null values.")

    return data


def validate_manifest(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the manifest data against FR-001 requirements.

    Checks for:
    - Presence of required top-level keys (doi, repo_url, dataset_name, reported_metrics)
    - Presence of required metric keys within reported_metrics (mae, r2, spearman_rho)

    Args:
        data: The loaded manifest dictionary.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []

    # Check top-level keys
    missing_top_level = REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
    if missing_top_level:
        errors.append(f"Missing required top-level keys: {sorted(missing_top_level)}")

    # Check reported_metrics structure if present
    if "reported_metrics" in data:
        metrics = data["reported_metrics"]
        if not isinstance(metrics, dict):
            errors.append("reported_metrics must be a dictionary.")
        else:
            missing_metrics = REQUIRED_METRIC_KEYS - set(metrics.keys())
            if missing_metrics:
                errors.append(f"Missing required metric keys in reported_metrics: {sorted(missing_metrics)}")

    is_valid = len(errors) == 0
    return is_valid, errors


def load_and_validate_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load and validate the manifest in one step.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        The validated manifest dictionary.

    Raises:
        ManifestValidationError: If validation fails.
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file is invalid YAML.
    """
    data = load_manifest(manifest_path)
    is_valid, errors = validate_manifest(data)

    if not is_valid:
        raise ManifestValidationError(f"Manifest validation failed: {'; '.join(errors)}")

    return data


def main():
    """Entry point for CLI usage."""
    print(f"Loading manifest from: {MANIFEST_PATH}")
    try:
        manifest = load_and_validate_manifest()
        print("Manifest loaded and validated successfully.")
        print(f"  DOI: {manifest.get('doi')}")
        print(f"  Repo URL: {manifest.get('repo_url')}")
        print(f"  Dataset Name: {manifest.get('dataset_name')}")
        print(f"  Reported Metrics: {manifest.get('reported_metrics')}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ManifestValidationError as e:
        print(f"Validation Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
