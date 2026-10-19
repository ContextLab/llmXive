"""Tests for T004 sliding‑window connectivity and vertex‑block descriptors."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from jsonschema import validate

from llmxive_toolkit import paths

CODE_DIR = paths.root / "code"
sys.path.insert(0, str(CODE_DIR))

import connectivity  # noqa: E402
import config  # noqa: E402

SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-investigating-the-relationship-between-b"
    / "contracts"
    / "network_metrics.schema.yaml"
)

def _dummy_timeseries(subject_id: str, n_timepoints: int = 200):
    """Create a synthetic ROI timeseries CSV for testing."""
    block_ids = [f"roi_{i+1}" for i in range(config.N_VERTEX_BLOCKS)]
    timepoints = np.arange(n_timepoints)
    # Simple sinusoidal signal plus small noise.
    data = {
        "subject_id": [subject_id] * n_timepoints,
        "timepoint": timepoints,
    }
    for bid in block_ids:
        data[bid] = np.sin(0.01 * timepoints) + 0.01 * np.random.randn(n_timepoints)
    df = pd.DataFrame(data)
    # Melt to long format expected by extract_rois output.
    df_long = df.melt(
        id_vars=["subject_id", "timepoint"],
        var_name="roi_id",
        value_name="value",
    )
    out_path = paths.data("derived", f"roi_timeseries_{subject_id}.csv")
    df_long.to_csv(out_path, index=False)

def test_schema_compliance(tmp_path):
    """Run connectivity on a tiny synthetic subject and validate schema."""
    subject_id = "99"
    _dummy_timeseries(subject_id, n_timepoints=200)
    # Invoke the connectivity main with default window/step.
    exit_code = connectivity.main(["--window", "45", "--step", "10"])
    assert exit_code == 0

    metrics_path = paths.data("derived", f"metrics_{subject_id}.csv")
    assert metrics_path.is_file()
    df = pd.read_csv(metrics_path)
    # Check required columns and types.
    schema = yaml.safe_load(SCHEMA_PATH.read_text())
    for _, row in df.iterrows():
        validate(dict(row), schema)

    # Window indexing should start at 0 and be consecutive.
    assert list(df["window_id"]) == list(range(len(df)))
    assert all(df["window_seconds"] == 45)
    assert all(df["step_seconds"] == 10)

def test_ledoit_wolf_recovery():
    """Construct a known covariance, run Ledoit‑Wolf, and confirm correlation."""
    # Two perfectly correlated blocks plus noise.
    np.random.seed(0)
    n = 100
    block1 = np.random.randn(n)
    block2 = block1 * 2.0  # perfect linear relationship
    block3 = np.random.randn(n) * 0.1
    data = np.column_stack([block1, block2, block3])
    # Pad to 100 blocks with independent noise.
    noise = np.random.randn(n, config.N_VERTEX_BLOCKS - 3) * 0.01
    matrix = np.hstack([data, noise])

    # Use Ledoit‑Wolf directly.
    lw = connectivity.LedoitWolf()
    lw.fit(matrix)
    cov = lw.covariance_
    std = np.sqrt(np.diag(cov))
    corr = cov / np.outer(std, std)
    np.fill_diagonal(corr, 1.0)

    # Blocks 0 and 1 should have correlation very close to 1.
    assert np.isclose(corr[0, 1], 1.0, atol=1e-2)
    # Block 0 vs 2 should be near 0.
    assert abs(corr[0, 2]) < 0.1
