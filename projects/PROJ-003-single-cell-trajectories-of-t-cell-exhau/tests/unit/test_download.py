import pytest
import yaml
import pandas as pd
from pathlib import Path
import gzip

def load_matrix(path: Path):
    """Helper to load common GEO matrix formats."""
    if path.suffix == '.gz':
        with gzip.open(path, 'rt') as f:
            # Try to detect delimiter
            first_line = f.readline()
            f.seek(0)
            sep = '\t' if '\t' in first_line else ','
            return pd.read_csv(f, sep=sep, index_col=0)
    else:
        return pd.read_csv(path, sep=None, engine='python', index_col=0)

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
        assert data["status"] == "available"

def test_sc005_data_sufficiency():
    """Verify datasets contain PD-1, metabolic, and exhaustion markers (SC-005)."""
    with open("data/state.yaml", "r") as f:
        state = yaml.safe_load(f)

    # Markers to check (case-insensitive)
    required_markers = {
        "pd1": ["PDCD1", "Pdcd1"],
        "metabolic": ["LDHA", "Ldha", "SLC2A1", "Slc2a1"],
        "exhaustion": ["LAG3", "Lag3", "HAVCR2", "Havcr2", "TOX", "Tox"]
    }

    for gse, data in state["datasets"].items():
        if data["status"] != "available":
            continue
        
        matrix_path = Path(data["raw_counts_path"])
        assert matrix_path.exists(), f"Matrix file missing for {gse}"
        
        try:
            df = load_matrix(matrix_path)
            genes = df.index.tolist()
            
            # Check for each category
            for cat, names in required_markers.items():
                found = any(name in genes for name in names)
                assert found, f"Dataset {gse} missing {cat} markers. Checked: {names}"
            
            # Special check for therapy response labels in GSE138852
            if gse == "GSE138852":
                # Labels are often in a separate metadata file or the matrix columns/index
                # We check if 'responder' or 'response' appears in the file content
                with open(matrix_path, 'rb') as f:
                    content = f.read().lower()
                    assert any(x in content for x in [b'responder', b'response', b'treatment']), \
                        f"GSE138852 missing therapy response labels"
                        
        except Exception as e:
            pytest.fail(f"Could not validate content for {gse}: {e}")

def test_raw_files_exist():
    project_root = Path("data/raw")
    expected_gses = ["GSE136103", "GSE127465", "GSE111075", "GSE138852"]
    for gse in expected_gses:
        gse_dir = project_root / gse
        assert gse_dir.exists(), f"Directory for {gse} should exist"
        # Verify SRA tools actually produced files
        sra_dir = gse_dir / "sra"
        assert sra_dir.exists(), f"SRA directory missing for {gse}"
        assert any(sra_dir.iterdir()), f"No SRA files found for {gse}"
