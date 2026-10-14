"""Contract and unit tests for the grid-search labeling stage (T005)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from jsonschema import validate

from src.pipeline.grid_search_labels import (
    TAUS,
    KS,
    evaluate_policy,
    grid_search_clip,
    run_grid_search,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (PROJECT_ROOT / "specs" / "001-llmxive-follow-up-extending-in-context-w"
               / "contracts" / "label.schema.yaml")
LABELS_PATH = PROJECT_ROOT / "data" / "labels.csv"


def _fake_clip():
    rng = np.random.default_rng(7)
    T, L = 40, 5
    latents = rng.normal(size=(T, L))
    actions = (rng.random(T) > 0.5).astype(int)
    return latents, actions


def test_evaluate_policy_returns_valid_rate():
    latents, actions = _fake_clip()
    rng = np.random.default_rng(0)
    rate = evaluate_policy(latents, actions, tau=1.0, k=16, rng=rng)
    assert 0.0 <= rate <= 1.0


def test_grid_search_deterministic():
    latents, actions = _fake_clip()
    r1 = grid_search_clip(latents, actions, 0)
    r2 = grid_search_clip(latents, actions, 0)
    assert r1 == r2
    assert r1["tau"] in TAUS
    assert r1["k"] in KS
    assert 0.0 <= r1["success_rate"] <= 1.0


def test_labels_csv_validates_against_schema():
    if not LABELS_PATH.exists():
        pytest.skip("labels.csv not generated yet")
    df = pd.read_csv(LABELS_PATH)
    schema = yaml.safe_load(SCHEMA_PATH.read_text())
    for record in df.to_dict(orient="records"):
        validate(instance={"clip_id": str(record["clip_id"]),
                           "tau": float(record["tau"]),
                           "k": int(record["k"]),
                           "success_rate": float(record["success_rate"])},
                 schema=schema)
    assert (df["success_rate"] >= 0.0).all()
    assert (df["success_rate"] <= 1.0).all()
    assert df[["clip_id", "tau", "k", "success_rate"]].notna().all().all()


def test_run_grid_search_end_to_end(tmp_path):
    # Build two tiny real clips via the project generator API.
    from src.pipeline.generate_clips import generate_clips
    raw = tmp_path / "raw"
    generate_clips(num_clips=2, out_dir=raw)
    out = tmp_path / "labels.csv"
    run_grid_search(input_dir=raw, output_path=out)
    df = pd.read_csv(out)
    assert len(df) == 2
    assert set(df.columns) >= {"clip_id", "tau", "k", "success_rate"}
