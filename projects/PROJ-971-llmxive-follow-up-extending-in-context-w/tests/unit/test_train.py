"""Unit tests for the Auto-ICWM regressor training (Task T006)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.pipeline.train_regressor import (
    FEATURES,
    TARGETS,
    load_dataset,
    make_split,
    train_regressor,
)


def _make_frame(n: int = 40, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    variance = rng.uniform(0.1, 1.0, size=n)
    # tau depends on the descriptors so a regressor can beat the mean baseline.
    tau = 0.5 + 1.5 * variance / 1.0 + 0.01 * rng.standard_normal(n)
    k = np.where(variance > 0.55, 64, np.where(variance > 0.3, 32, 16))
    return pd.DataFrame(
        {
            "clip_id": [f"clip_{i:03d}" for i in range(n)],
            "variance": variance,
            "autocorr_lag1": rng.uniform(0.0, 1.0, size=n),
            "spectral_density": rng.uniform(0.0, 1.0, size=n),
            "tau": tau,
            "k": k,
        }
    )


def test_load_dataset_merges_on_clip_id(tmp_path):
    desc = _make_frame(10, seed=1)[["clip_id"] + FEATURES]
    lab = _make_frame(10, seed=1)[["clip_id"] + TARGETS]
    desc.to_csv(tmp_path / "d.csv", index=False)
    lab.to_csv(tmp_path / "l.csv", index=False)
    df = load_dataset(tmp_path / "d.csv", tmp_path / "l.csv")
    assert len(df) == 10
    assert set(FEATURES + TARGETS).issubset(df.columns)


def test_load_dataset_empty_join_raises(tmp_path):
    desc = _make_frame(5, seed=1)[["clip_id"] + FEATURES]
    lab = _make_frame(5, seed=2)[["clip_id"] + TARGETS]
    lab["clip_id"] = ["other_%d" % i for i in range(5)]
    desc.to_csv(tmp_path / "d.csv", index=False)
    lab.to_csv(tmp_path / "l.csv", index=False)
    with pytest.raises(ValueError):
        load_dataset(tmp_path / "d.csv", tmp_path / "l.csv")


def test_make_split_stratified_by_k():
    df = _make_frame(40, seed=3)
    X_train, X_val, y_train, y_val = make_split(df)
    assert len(X_val) == 8
    assert len(X_train) == 32
    # every k class present in the small split must also appear in training
    for kv in np.unique(y_val[:, 1]):
        assert kv in np.unique(y_train[:, 1])


def test_train_regressor_beats_mean_baseline():
    df = _make_frame(60, seed=5)
    model, metrics = train_regressor(df, seed=42)
    assert metrics["n_train"] + metrics["n_val"] == 60
    assert metrics["val_mse"] < 0.9 * metrics["baseline_mse"]
    assert metrics["meets_sc006"] is True
    # predictions stay within the valid operational range
    preds = model.predict(df[FEATURES].to_numpy(dtype=float))
    assert np.all(preds[:, 0] >= 0.1) and np.all(preds[:, 0] <= 2.0)


def test_train_regressor_degenerate_single_k():
    df = _make_frame(20, seed=7)
    df["k"] = 32
    model, metrics = train_regressor(df, seed=42)
    assert metrics["n_val"] == 4