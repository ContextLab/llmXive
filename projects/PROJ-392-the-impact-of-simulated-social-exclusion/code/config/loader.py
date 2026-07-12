"""
Configuration loader for dataset IDs and ROI coordinates.

This module provides a centralized configuration management system for the
social exclusion and reward neural response study. It handles:
- Dataset identification (ds000246 for exclusion, ds004738 for reward)
- ROI definitions (AAL atlas for Ventral Striatum, Harvard-Oxford for OFC)
- Coordinate mappings for mask creation
- Path resolution for project directories
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


# Default configuration values
DEFAULT_CONFIG = {
    "datasets": {
        "exclusion": {
            "id": "ds000246",
            "name": "Social Exclusion Task",
            "description": "Cyberball paradigm for social exclusion",
            "source": "openneuro"
        },
        "reward": {
            "id": "ds004738",
            "name": "Reward Task",
            "description": "Monetary incentive delay task",
            "source": "openneuro"
        }
    },
    "rois": {
        "ventral_striatum": {
            "atlas": "AAL",
            "label": "AAL_VentralStriatum",
            "coordinates": {
                "x": 12,
                "y": 12,
                "z": -6
            },
            "description": "Ventral Striatum from AAL atlas"
        },
        "orbitofrontal_cortex": {
            "atlas": "Harvard-Oxford",
            "label": "HarvardOxford-Cortical-Orbital",
            "probability_threshold": 0.25,
            "coordinates": {
                "x": 0,
                "y": 45,
                "z": -12
            },
            "description": "Orbitofrontal Cortex from Harvard-Oxford atlas"
        }
    },
    "paths": {
        "raw_fmri": "data/raw-fmri",
        "processed_fmri": "data/processed-fmri",
        "behavioral": "data/behavioral",
        "results": "data/results",
        "figures": "figures",
        "code": "code"
    },
    "analysis": {
        "smoothing_kernels": [4, 6, 8],
        "mask_probabilities": [0.25, 0.50],
        "alpha_level": 0.05,
        "min_subjects_per_group": 20
    }
}


def _load_yaml_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or return default configuration.

    Args:
        config_path: Optional path to a custom configuration file.

    Returns:
        Dictionary containing the configuration.
    """
    if config_path and config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG.copy()


def get_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get the full configuration dictionary.

    Args:
        config_path: Optional path to a custom configuration file.

    Returns:
        Complete configuration dictionary.
    """
    return _load_yaml_config(config_path)


def get_all_dataset_ids(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Retrieve all dataset IDs from the configuration.

    Args:
        config: Optional configuration dictionary. If None, loads defaults.

    Returns:
        List of dataset IDs (e.g., ['ds000246', 'ds004738']).
    """
    if config is None:
        config = get_config()
    datasets = config.get('datasets', {})
    return [ds.get('id') for ds in datasets.values() if ds.get('id')]


def get_dataset_id(dataset_type: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get a specific dataset ID by type.

    Args:
        dataset_type: Type of dataset ('exclusion' or 'reward').
        config: Optional configuration dictionary.

    Returns:
        The dataset ID string.

    Raises:
        ValueError: If the dataset type is not found.
    """
    if config is None:
        config = get_config()
    datasets = config.get('datasets', {})
    if dataset_type not in datasets:
        raise ValueError(f"Dataset type '{dataset_type}' not found in configuration. "
                       f"Available: {list(datasets.keys())}")
    dataset = datasets[dataset_type]
    dataset_id = dataset.get('id')
    if not dataset_id:
        raise ValueError(f"Dataset '{dataset_type}' has no ID configured.")
    return dataset_id


def get_roi_definition(roi_name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get the full definition of an ROI including atlas, label, and coordinates.

    Args:
        roi_name: Name of the ROI (e.g., 'ventral_striatum', 'orbitofrontal_cortex').
        config: Optional configuration dictionary.

    Returns:
        Dictionary containing ROI definition.

    Raises:
        ValueError: If the ROI name is not found.
    """
    if config is None:
        config = get_config()
    rois = config.get('rois', {})
    if roi_name not in rois:
        raise ValueError(f"ROI '{roi_name}' not found in configuration. "
                       f"Available: {list(rois.keys())}")
    return rois[roi_name].copy()


def get_roi_coordinates(roi_name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """
    Get the MNI coordinates for a specific ROI.

    Args:
        roi_name: Name of the ROI.
        config: Optional configuration dictionary.

    Returns:
        Dictionary with 'x', 'y', 'z' integer coordinates.

    Raises:
        ValueError: If the ROI is not found or has no coordinates.
    """
    roi_def = get_roi_definition(roi_name, config)
    coords = roi_def.get('coordinates')
    if not coords:
        raise ValueError(f"ROI '{roi_name}' has no coordinates defined.")
    return {
        'x': int(coords.get('x', 0)),
        'y': int(coords.get('y', 0)),
        'z': int(coords.get('z', 0))
    }


def get_roi_atlas(roi_name: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the atlas source for a specific ROI.

    Args:
        roi_name: Name of the ROI.
        config: Optional configuration dictionary.

    Returns:
        Atlas name (e.g., 'AAL', 'Harvard-Oxford').
    """
    roi_def = get_roi_definition(roi_name, config)
    return roi_def.get('atlas', 'Unknown')


def get_roi_label(roi_name: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the atlas label for a specific ROI.

    Args:
        roi_name: Name of the ROI.
        config: Optional configuration dictionary.

    Returns:
        Atlas label string.
    """
    roi_def = get_roi_definition(roi_name, config)
    return roi_def.get('label', '')


def get_all_roi_names(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Get a list of all configured ROI names.

    Args:
        config: Optional configuration dictionary.

    Returns:
        List of ROI names.
    """
    if config is None:
        config = get_config()
    return list(config.get('rois', {}).keys())


def get_path(path_key: str, config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get a project path by key.

    Args:
        path_key: Key for the path (e.g., 'raw_fmri', 'results').
        config: Optional configuration dictionary.

    Returns:
        Path object pointing to the directory.

    Raises:
        ValueError: If the path key is not found.
    """
    if config is None:
        config = get_config()
    paths = config.get('paths', {})
    if path_key not in paths:
        raise ValueError(f"Path key '{path_key}' not found in configuration. "
                       f"Available: {list(paths.keys())}")
    return Path(paths[path_key])


def get_analysis_params(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get analysis parameters from configuration.

    Args:
        config: Optional configuration dictionary.

    Returns:
        Dictionary of analysis parameters.
    """
    if config is None:
        config = get_config()
    return config.get('analysis', {}).copy()


def ensure_paths_exist(config: Optional[Dict[str, Any]] = None, base_dir: Optional[Path] = None) -> List[Path]:
    """
    Ensure all configured paths exist, creating them if necessary.

    Args:
        config: Optional configuration dictionary.
        base_dir: Base directory for path resolution. Defaults to project root.

    Returns:
        List of Path objects that were created or verified.
    """
    if config is None:
        config = get_config()
    if base_dir is None:
        base_dir = Path.cwd()

    paths = config.get('paths', {})
    created_paths = []

    for key, path_str in paths.items():
        full_path = base_dir / path_str
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(full_path)

    return created_paths


def main():
    """
    Command-line interface for testing the configuration loader.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Configuration loader for dataset IDs and ROI coordinates'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to custom configuration YAML file'
    )
    parser.add_argument(
        '--list-datasets',
        action='store_true',
        help='List all dataset IDs'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        choices=['exclusion', 'reward'],
        help='Get specific dataset ID'
    )
    parser.add_argument(
        '--list-rois',
        action='store_true',
        help='List all ROI names'
    )
    parser.add_argument(
        '--roi',
        type=str,
        help='Get specific ROI definition or coordinates'
    )
    parser.add_argument(
        '--roi-coords',
        type=str,
        help='Get MNI coordinates for a specific ROI'
    )
    parser.add_argument(
        '--ensure-paths',
        action='store_true',
        help='Ensure all configured paths exist'
    )

    args = parser.parse_args()
    config = get_config(args.config)

    if args.list_datasets:
        ids = get_all_dataset_ids(config)
        print("Dataset IDs:")
        for ds_id in ids:
            print(f"  - {ds_id}")

    if args.dataset:
        ds_id = get_dataset_id(args.dataset, config)
        print(f"Dataset ID for '{args.dataset}': {ds_id}")

    if args.list_rois:
        names = get_all_roi_names(config)
        print("ROI Names:")
        for name in names:
            print(f"  - {name}")

    if args.roi:
        try:
            roi_def = get_roi_definition(args.roi, config)
            print(f"ROI Definition for '{args.roi}':")
            print(f"  Atlas: {roi_def.get('atlas')}")
            print(f"  Label: {roi_def.get('label')}")
            print(f"  Coordinates: {roi_def.get('coordinates')}")
        except ValueError as e:
            print(f"Error: {e}")

    if args.roi_coords:
        try:
            coords = get_roi_coordinates(args.roi_coords, config)
            print(f"MNI Coordinates for '{args.roi_coords}': ({coords['x']}, {coords['y']}, {coords['z']})")
        except ValueError as e:
            print(f"Error: {e}")

    if args.ensure_paths:
        paths = ensure_paths_exist(config)
        print("Ensured paths:")
        for p in paths:
            print(f"  - {p}")

    if not any([args.list_datasets, args.dataset, args.list_rois, args.roi, args.roi_coords, args.ensure_paths]):
        parser.print_help()


if __name__ == '__main__':
    main()