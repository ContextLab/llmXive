import pathlib
import yaml
import json

def test_config_updated():
    """After running 01_discover_data.py the config.yaml must contain at least one DOI."""
    config_path = pathlib.Path("code") / "config.yaml"
    with config_path.open() as f:
        cfg = yaml.safe_load(f)
    assert isinstance(cfg.get("dataset_ids"), list)
    assert len(cfg["dataset_ids"]) > 0, "dataset_ids list should not be empty after discovery"

def test_json_artifact():
    """The JSON file produced by the discovery step must exist and be non‑empty."""
    json_path = pathlib.Path("data") / "raw" / "dryad_dataset_ids.json"
    assert json_path.is_file()
    with json_path.open() as jf:
        data = json.load(jf)
    assert isinstance(data, list)
    assert len(data) > 0, "Discovery JSON should contain at least one dataset entry"