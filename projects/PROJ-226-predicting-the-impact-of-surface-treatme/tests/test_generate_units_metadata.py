import pytest
import pandas as pd
import json
from pathlib import Path
from llmxive_toolkit import paths
from code.generate_units_metadata import (
    main, 
    UnitMismatchError, 
    REQUIRED_COLUMNS, 
    UNITS_MAP
)

def test_generate_units_metadata_success(tmp_path, monkeypatch):
    # Setup: create a dummy raw CSV
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    csv_path = raw_dir / "test_source.csv"
    
    df = pd.DataFrame({
        "plasma_power_w": [100, 200],
        "exposure_time_s": [10, 20],
        "chemical_concentration_pct": [1, 2],
        "polymer_surface_energy": [40, 41],
        "substrate_roughness_nm": [100, 110],
        "adhesion_strength_mj_m2": [1.5, 2.5],
        "treatment_type": ["Oxygen", "Nitrogen"],
        "pair_id": ["A", "B"]
    })
    df.to_csv(csv_path, index=False)

    # Monkeypatch paths.data to return our tmp_path
    def mock_data(*args):
        if args[0] == "raw":
            return raw_dir
        return tmp_path / args[0]
    
    monkeypatch.setattr("llmxive_toolkit.paths.data", mock_data)

    # Run
    main()

    # Verify
    json_path = raw_dir / "test_source_units.json"
    assert json_path.exists()
    with open(json_path, "r") as f:
        units = json.load(f)
    
    for col in REQUIRED_COLUMNS:
        assert units[col] == UNITS_MAP[col]

def test_generate_units_metadata_missing_column(tmp_path, monkeypatch):
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    csv_path = raw_dir / "bad_source.csv"
    
    # Missing 'pair_id'
    df = pd.DataFrame({
        "plasma_power_w": [100],
        "exposure_time_s": [10],
        "chemical_concentration_pct": [1],
        "polymer_surface_energy": [40],
        "substrate_roughness_nm": [100],
        "adhesion_strength_mj_m2": [1.5],
        "treatment_type": ["Oxygen"],
    })
    df.to_csv(csv_path, index=False)

    def mock_data(*args):
        if args[0] == "raw":
            return raw_dir
        return tmp_path / args[0]
    
    monkeypatch.setattr("llmxive_toolkit.paths.data", mock_data)

    with pytest.raises(UnitMismatchError, match="missing required columns"):
        main()

def test_generate_units_metadata_non_numeric(tmp_path, monkeypatch):
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    csv_path = raw_dir / "non_numeric.csv"
    
    # 'plasma_power_w' contains a string
    df = pd.DataFrame({
        "plasma_power_w": [100, "ERROR"],
        "exposure_time_s": [10, 20],
        "chemical_concentration_pct": [1, 2],
        "polymer_surface_energy": [40, 41],
        "substrate_roughness_nm": [100, 110],
        "adhesion_strength_mj_m2": [1.5, 2.5],
        "treatment_type": ["Oxygen", "Nitrogen"],
        "pair_id": ["A", "B"]
    })
    df.to_csv(csv_path, index=False)

    def mock_data(*args):
        if args[0] == "raw":
            return raw_dir
        return tmp_path / args[0]
    
    monkeypatch.setattr("llmxive_toolkit.paths.data", mock_data)

    with pytest.raises(UnitMismatchError, match="contains non‑numeric values"):
        main()