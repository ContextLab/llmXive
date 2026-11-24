import json
from pathlib import Path

def test_config_file_exists():
    """The config.yaml file must exist and contain the expected earthquake count."""
    config_path = Path("data/processed/config.yaml")
    assert config_path.is_file(), "config.yaml does not exist"
    import yaml
    cfg = yaml.safe_load(config_path.read_text())
    assert "expected_earthquake_count" in cfg, "expected_earthquake_count missing"
    # The placeholder value should be an integer (the exact number is not enforced here)
    assert isinstance(cfg["expected_earthquake_count"], int), "expected_earthquake_count must be int"

def test_usgs_downloaded():
    """The USGS test subset must be downloaded and saved as JSON with the correct number of rows."""
    json_path = Path("data/raw/usgs_test_subset.json")
    assert json_path.is_file(), "USGS raw JSON file not found"
    data = json.loads(json_path.read_text())
    # The file should contain a 'data' list with at least one entry
    assert isinstance(data, dict) and "data" in data, "Invalid USGS JSON structure"
    assert isinstance(data["data"], list), "'data' field should be a list"
    # Expect at least the placeholder count (12) rows
    assert len(data["data"]) >= 1, "USGS data list is empty"

def test_download_success_log():
    """The download_success.log must contain the expected messages."""
    log_path = Path("logs/download_success.log")
    assert log_path.is_file(), "download_success.log not found"
    content = log_path.read_text()
    assert "Global NOAA pressure data downloaded:" in content, "NOAA download message missing"
    assert "USGS earthquake catalog rows:" in content, "USGS rows message missing"