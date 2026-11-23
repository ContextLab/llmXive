import pytest
from pathlib import Path
from config import (
    get_project_root,
    get_data_path,
    ensure_directories_exist,
    validate_config,
    OPENNEURO_DATASET_IDS,
    PIPELINE_A_BANDPASS,
    PIPELINE_B_BANDPASS,
    ALPHA_BAND_LOW,
    ALPHA_BAND_HIGH,
    POWER_THRESHOLD
)

def test_get_project_root_is_absolute():
    root = get_project_root()
    assert root.is_absolute()
    # Should end with 'code' if run from code directory, or project root
    assert root.name == "PROJ-785-cross-dataset-consistency-of-alpha-peak-" or root.parent.name == "PROJ-785-cross-dataset-consistency-of-alpha-peak-"

def test_get_data_path():
    data_path = get_data_path()
    assert data_path.exists() or data_path.parent.exists() # Parent should exist
    assert data_path.name == "data"

def test_ensure_directories_exist_creates_folders(tmp_path, monkeypatch):
    # Monkeypatch the global paths to use a temp directory for safety
    import config
    original_root = config._PROJECT_ROOT
    config._PROJECT_ROOT = tmp_path
    
    try:
        ensure_directories_exist()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "derivatives").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "state").exists()
    finally:
        config._PROJECT_ROOT = original_root

def test_validate_config_returns_ok():
    result = validate_config()
    assert result["status"] == "ok"
    assert len(result["issues"]) == 0
    assert len(result["datasets"]) >= 3

def test_dataset_ids_list():
    assert len(OPENNEURO_DATASET_IDS) >= 3
    assert all(isinstance(d, str) for d in OPENNEURO_DATASET_IDS)
    assert "ds003865" in OPENNEURO_DATASET_IDS
    assert "ds003392" in OPENNEURO_DATASET_IDS
    assert "ds003775" in OPENNEURO_DATASET_IDS

def test_pipeline_parameters_valid():
    assert PIPELINE_A_BANDPASS[0] < PIPELINE_A_BANDPASS[1]
    assert PIPELINE_B_BANDPASS[0] < PIPELINE_B_BANDPASS[1]
    assert ALPHA_BAND_LOW < ALPHA_BAND_HIGH
    assert 0.0 <= POWER_THRESHOLD <= 1.0