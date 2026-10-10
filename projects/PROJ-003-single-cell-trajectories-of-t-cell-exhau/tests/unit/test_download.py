import pytest
import yaml
from pathlib import Path

def test_state_yaml_exists():
    state_path = Path("data/state.yaml")
    assert state_path.exists(), "Project state YAML should exist after download"

def test_checksums_recorded():
    with open("data/state.yaml", "r") as f:
        state = yaml.safe_load(f)
    
    assert "datasets" in state, "State YAML must contain 'datasets' key"
    
    expected_gses = ["GSE136103", "GSE127465", "GSE111075", "GSE138852"]
    for gse in expected_gses:
        assert gse in state["datasets"], f"Dataset {gse} missing from state"
        data = state["datasets"][gse]
        assert "counts_checksum" in data, f"Checksum missing for {gse}"
        assert len(data["counts_checksum"]) == 64, f"Invalid SHA256 for {gse}"
        assert data["status"] == "available"

def test_raw_files_exist():
    project_root = Path("data/raw")
    expected_gses = ["GSE136103", "GSE127465", "GSE111075", "GSE138852"]
    for gse in expected_gses:
        gse_dir = project_root / gse
        assert gse_dir.exists(), f"Directory for {gse} should exist"
        # Check for at least one file in the counts directory
        counts_dir = gse_dir / "counts"
        assert any(counts_dir.iterdir()), f"No count files found for {gse}"