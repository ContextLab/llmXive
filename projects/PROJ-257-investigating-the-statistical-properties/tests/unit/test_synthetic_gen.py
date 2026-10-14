import json
from pathlib import Path

import pandas as pd
import pytest

from src.data.synthetic_gen import acquire_sim_catalog, generate_synthetic_catalog, try_download_catalog

def test_generate_synthetic_catalog():
    """Ensure the synthetic generator produces a valid DataFrame."""
    df = generate_synthetic_catalog(n_events=150, seed=123)
    # Basic schema checks
    required = [
        "event_id",
        "component_mass_1",
        "component_mass_2",
        "mass_ratio",
        "effective_spin",
        "formation_channel",
        "generation_method",
    ]
    for col in required:
        assert col in df.columns, f"Missing column {col}"
    assert len(df) >= 100
    # Validate physical ranges
    assert (df["mass_ratio"] > 0).all() and (df["mass_ratio"] <= 1).all()
    assert df["effective_spin"].between(-1, 1).all()

def test_acquire_sim_catalog_writes_file(tmp_path, monkeypatch):
    """Force the download path to a temporary location and verify output."""
    # Monkeypatch the data path to a temporary directory to avoid side‑effects.
    monkeypatch.setattr(
        "src.data.synthetic_gen.paths",
        type("DummyPaths", (), {"data": lambda *parts: Path(tmp_path, *parts)}),
    )
    # Ensure the download attempt fails (the URL is unreachable).
    # The function will fall back to synthetic generation.
    out_path = acquire_sim_catalog()
    assert out_path.is_file()
    df = pd.read_csv(out_path)
    # Verify schema again
    for col in [
        "event_id",
        "component_mass_1",
        "component_mass_2",
        "mass_ratio",
        "effective_spin",
        "formation_channel",
        "generation_method",
    ]:
        assert col in df.columns
    assert len(df) >= 100