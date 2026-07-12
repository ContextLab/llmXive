"""
Unit tests for code/config.py
"""
import os
import tempfile
import pytest
from pathlib import Path
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    load_config,
    get_path,
    get_constant,
    get_data_raw_dir,
    get_data_processed_dir,
    get_filtered_csv_path,
    get_poses_estimated_json_path,
    get_reconstruction_results_csv_path,
    get_report_path,
    get_real_dataset_zip,
    get_synthetic_dataset_zip,
    get_radial_motion_threshold,
    get_z_velocity_threshold,
    get_max_memory_gb,
    get_max_frame_processing_ms,
    get_aspect_ratio_tolerance_pct,
    get_synthetic_depth_error_threshold_pct,
    get_hf_dataset_name,
    get_hf_dataset_revision,
    get_log_level,
    get_log_format,
    _deep_merge
)

def test_default_config_paths_exist():
    config = load_config()
    paths = config["paths"]
    assert "data_raw" in paths
    assert "data_processed" in paths
    assert "code" in paths
    assert "logs" in paths
    assert "figures" in paths

def test_default_constants():
    config = load_config()
    constants = config["constants"]
    assert constants["max_memory_gb"] == 6.0
    assert constants["radial_motion_threshold_deg"] == 15.0
    assert constants["z_velocity_threshold"] == 0.1
    assert constants["aspect_ratio_tolerance_pct"] == 5.0
    assert constants["synthetic_depth_error_threshold_pct"] == 50.0

def test_deep_merge():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 10, "e": 5}, "f": 6}
    _deep_merge(base, override)
    assert base["a"] == 1
    assert base["b"]["c"] == 10
    assert base["b"]["d"] == 3
    assert base["b"]["e"] == 5
    assert base["f"] == 6

def test_load_config_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        custom_config = {
            "constants": {
                "max_memory_gb": 8.0,
                "radial_motion_threshold_deg": 20.0
            },
            "paths": {
                "data_raw": "/custom/raw"
            }
        }
        yaml.dump(custom_config, f)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert config["constants"]["max_memory_gb"] == 8.0
        assert config["constants"]["radial_motion_threshold_deg"] == 20.0
        assert config["paths"]["data_raw"] == "/custom/raw"
    finally:
        os.unlink(temp_path)

def test_get_constant():
    assert get_radial_motion_threshold() == 15.0
    assert get_z_velocity_threshold() == 0.1
    assert get_max_memory_gb() == 6.0

def test_get_path():
    path = get_path("paths.data_raw")
    assert isinstance(path, Path)
    assert path.exists()

def test_get_constant_not_found():
    with pytest.raises(KeyError):
        get_constant("non_existent_constant")

def test_get_path_not_found():
    with pytest.raises(KeyError):
        get_path("paths.non_existent_path")
