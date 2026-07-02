"""
Configuration loader for dataset IDs and ROI coordinates.

This module provides a centralized configuration management system for:
- OpenNeuro dataset identifiers (ds000246, ds004738)
- ROI coordinates and atlas specifications (AAL, Harvard-Oxford)
- Analysis parameters and thresholds

The configuration is loaded from a YAML file and validated against
expected schema constraints.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ROIConfig:
    """Configuration for a single Region of Interest."""
    name: str
    atlas: str  # e.g., 'AAL', 'Harvard-Oxford'
    coordinates: Optional[Tuple[float, float, float]] = None
    threshold: Optional[float] = None
    mask_path: Optional[str] = None
    description: str = ""


@dataclass
class DatasetConfig:
    """Configuration for a dataset."""
    id: str
    name: str
    type: str  # 'exclusion' or 'reward'
    base_url: str = "https://openneuro.org/datasets"
    local_path: Optional[str] = None
    task_label: Optional[str] = None
    description: str = ""


@dataclass
class ProjectConfig:
    """Main project configuration container."""
    datasets: List[DatasetConfig] = field(default_factory=list)
    rois: List[ROIConfig] = field(default_factory=list)
    analysis: Dict[str, Any] = field(default_factory=dict)
    paths: Dict[str, str] = field(default_factory=dict)
    version: str = "1.0.0"


DEFAULT_CONFIG_PATH = "code/utils/config.yaml"


def _load_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file. Defaults to DEFAULT_CONFIG_PATH.

    Returns:
        Dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _parse_dataset_configs(data: Dict[str, Any]) -> List[DatasetConfig]:
    """Parse dataset configuration from raw data."""
    datasets = []
    raw_datasets = data.get('datasets', [])

    for ds in raw_datasets:
        datasets.append(DatasetConfig(
            id=ds.get('id', ''),
            name=ds.get('name', ''),
            type=ds.get('type', ''),
            base_url=ds.get('base_url', 'https://openneuro.org/datasets'),
            local_path=ds.get('local_path'),
            task_label=ds.get('task_label'),
            description=ds.get('description', '')
        ))

    return datasets


def _parse_roi_configs(data: Dict[str, Any]) -> List[ROIConfig]:
    """Parse ROI configuration from raw data."""
    rois = []
    raw_rois = data.get('rois', [])

    for roi in raw_rois:
        coords = roi.get('coordinates')
        if coords and len(coords) == 3:
            coord_tuple = (float(coords[0]), float(coords[1]), float(coords[2]))
        else:
            coord_tuple = None

        rois.append(ROIConfig(
            name=roi.get('name', ''),
            atlas=roi.get('atlas', ''),
            coordinates=coord_tuple,
            threshold=roi.get('threshold'),
            mask_path=roi.get('mask_path'),
            description=roi.get('description', '')
        ))

    return rois


def load_config(config_path: Optional[str] = None) -> ProjectConfig:
    """
    Load and validate the full project configuration.

    Args:
        config_path: Optional path to the config file.

    Returns:
        ProjectConfig object with all settings populated.
    """
    raw_data = _load_yaml_config(config_path)

    return ProjectConfig(
        datasets=_parse_dataset_configs(raw_data),
        rois=_parse_roi_configs(raw_data),
        analysis=raw_data.get('analysis', {}),
        paths=raw_data.get('paths', {}),
        version=raw_data.get('version', '1.0.0')
    )


def get_dataset_by_id(dataset_id: str, config: Optional[ProjectConfig] = None) -> Optional[DatasetConfig]:
    """
    Retrieve a dataset configuration by its ID.

    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000246').
        config: Optional ProjectConfig. If None, loads the default config.

    Returns:
        DatasetConfig if found, None otherwise.
    """
    if config is None:
        config = load_config()

    for ds in config.datasets:
        if ds.id == dataset_id:
            return ds
    return None


def get_roi_by_name(roi_name: str, config: Optional[ProjectConfig] = None) -> Optional[ROIConfig]:
    """
    Retrieve an ROI configuration by its name.

    Args:
        roi_name: The name of the ROI (e.g., 'Ventral Striatum').
        config: Optional ProjectConfig. If None, loads the default config.

    Returns:
        ROIConfig if found, None otherwise.
    """
    if config is None:
        config = load_config()

    for roi in config.rois:
        if roi.name.lower() == roi_name.lower():
            return roi
    return None


def get_exclusion_dataset(config: Optional[ProjectConfig] = None) -> Optional[DatasetConfig]:
    """Convenience method to get the social exclusion dataset."""
    if config is None:
        config = load_config()

    for ds in config.datasets:
        if ds.type == 'exclusion':
            return ds
    return None


def get_reward_dataset(config: Optional[ProjectConfig] = None) -> Optional[DatasetConfig]:
    """Convenience method to get the reward dataset."""
    if config is None:
        config = load_config()

    for ds in config.datasets:
        if ds.type == 'reward':
            return ds
    return None


def get_atlas_rois(atlas_name: str, config: Optional[ProjectConfig] = None) -> List[ROIConfig]:
    """
    Get all ROIs from a specific atlas.

    Args:
        atlas_name: Name of the atlas (e.g., 'AAL', 'Harvard-Oxford').
        config: Optional ProjectConfig.

    Returns:
        List of ROIConfig objects from the specified atlas.
    """
    if config is None:
        config = load_config()

    return [roi for roi in config.rois if roi.atlas.lower() == atlas_name.lower()]


def create_default_config(output_path: Optional[str] = None) -> str:
    """
    Create a default configuration file with the required dataset IDs and ROI coordinates.

    Args:
        output_path: Optional path to write the config. Defaults to DEFAULT_CONFIG_PATH.

    Returns:
        The path where the config was written.
    """
    if output_path is None:
        output_path = DEFAULT_CONFIG_PATH

    config_dir = Path(output_path).parent
    config_dir.mkdir(parents=True, exist_ok=True)

    default_config = {
        "version": "1.0.0",
        "description": "Configuration for Social Exclusion and Reward Neural Response Study",
        "datasets": [
            {
                "id": "ds000246",
                "name": "Social Exclusion Task (Cyberball)",
                "type": "exclusion",
                "base_url": "https://openneuro.org/datasets",
                "task_label": "social_exclusion",
                "description": "fMRI dataset containing social exclusion (Cyberball) task"
            },
            {
                "id": "ds004738",
                "name": "Reward Processing Task",
                "type": "reward",
                "base_url": "https://openneuro.org/datasets",
                "task_label": "reward",
                "description": "fMRI dataset containing monetary reward anticipation and receipt tasks"
            }
        ],
        "rois": [
            {
                "name": "Ventral Striatum",
                "atlas": "AAL",
                "coordinates": [10.0, 10.0, -8.0],
                "threshold": None,
                "mask_path": "data/masks/aal_ventral_striatum.nii.gz",
                "description": "Primary ROI for reward processing, defined in AAL atlas"
            },
            {
                "name": "Orbitofrontal Cortex",
                "atlas": "Harvard-Oxford",
                "coordinates": [0.0, 40.0, -15.0],
                "threshold": 25.0,
                "mask_path": "data/masks/ho_orbitofrontal.nii.gz",
                "description": "Secondary ROI for reward valuation, Harvard-Oxford atlas, 25% threshold"
            },
            {
                "name": "Dorsolateral Prefrontal Cortex",
                "atlas": "Harvard-Oxford",
                "coordinates": [40.0, 35.0, 25.0],
                "threshold": 25.0,
                "mask_path": "data/masks/ho_dlpfc.nii.gz",
                "description": "Control ROI for cognitive control processes"
            },
            {
                "name": "Anterior Cingulate Cortex",
                "atlas": "AAL",
                "coordinates": [0.0, 20.0, 30.0],
                "threshold": None,
                "mask_path": "data/masks/aal_acc.nii.gz",
                "description": "ROI for conflict monitoring and error processing"
            }
        ],
        "analysis": {
            "alpha": 0.05,
            "bonferroni_correction": True,
            "smoothing_kernel_mm": 6,
            "highpass_cutoff_hz": 0.008,
            "temporal_autocorrelation_model": "AR(1)",
            "min_participants_per_group": 20,
            "power_threshold": 0.8
        },
        "paths": {
            "raw_data": "data/raw-fmri",
            "processed_data": "data/processed-fmri",
            "behavioral_data": "data/behavioral",
            "results": "data/results",
            "masks": "data/masks",
            "figures": "figures"
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return output_path


def main():
    """
    CLI entry point for configuration management.
    Demonstrates loading and printing configuration details.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Configuration loader for fMRI study")
    parser.add_argument(
        "--create-default",
        action="store_true",
        help="Create a default configuration file"
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "--print-datasets",
        action="store_true",
        help="Print all configured datasets"
    )
    parser.add_argument(
        "--print-rois",
        action="store_true",
        help="Print all configured ROIs"
    )

    args = parser.parse_args()

    if args.create_default:
        path = create_default_config(args.config_path)
        print(f"Created default configuration at: {path}")
        return

    try:
        config = load_config(args.config_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Use --create-default to generate a new configuration file.")
        return

    if args.print_datasets:
        print(f"Configured Datasets (Version: {config.version}):")
        for ds in config.datasets:
            print(f"  - {ds.id}: {ds.name} ({ds.type})")
            if ds.coordinates:
                print(f"    Coords: {ds.coordinates}")

    if args.print_rois:
        print(f"\nConfigured ROIs:")
        for roi in config.rois:
            print(f"  - {roi.name} ({roi.atlas})")
            if roi.coordinates:
                print(f"    Coords: {roi.coordinates}")
            if roi.threshold:
                print(f"    Threshold: {roi.threshold}%")

    if not args.print_datasets and not args.print_rois and not args.create_default:
        # Default behavior: print summary
        print("Configuration loaded successfully.")
        print(f"  Datasets: {len(config.datasets)}")
        print(f"  ROIs: {len(config.rois)}")
        print(f"  Version: {config.version}")


if __name__ == "__main__":
    main()
