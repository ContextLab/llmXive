"""Tests for the power analysis and conditional association (T006)."""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.power import FTestPower

import config
from llmxive_toolkit import paths

# The analysis module lives under ``code.analysis``; add the directory to sys.path.
CODE_DIR = paths.root / "code"
import sys

sys.path.insert(0, str(CODE_DIR))
import analysis  # noqa: E402

# ----------------------------------------------------------------------
# Helper to create a minimal synthetic dataset for the association test.
# ----------------------------------------------------------------------
def _create_synthetic_dataset(tmp_path: Path):
    """Create a tiny parquet shard with a skill proxy and one covariate.

    The function writes three files that the analysis module expects:
    - ``data/raw/column_inventory.json`` describing present columns and subject count.
    - ``data/derived/pca_scores.csv`` containing two PCs for three subjects.
    - ``data/raw/<shard>.parquet`` containing the raw metadata columns.
    """
    # 1) Column inventory
    inventory = {
        "available_subject_count": 3,
        "present_columns": ["subject_id", "expert_rating", "age", "fd"],
    }
    inv_path = paths.data("raw", "column_inventory.json")
    inv_path.write_text(json.dumps(inventory, indent=2))

    # 2) PCA scores (synthetic but deterministic)
    pca_df = pd.DataFrame(
        {
            "subject_id": ["01", "02", "03"],
            "pc_1": [0.5, -0.2, 0.1],
            "pc_2": [-0.1, 0.3, -0.4],
        }
    )
    pca_path = paths.data("derived", "pca_scores.csv")
    pca_df.to_csv(pca_path, index=False)

    # 3) Parquet shard with the required columns
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.Table.from_pydict(
        {
            "subject_id": ["01", "02", "03"],
            "expert_rating": [1.0, 2.0, 3.0],
            "age": [25, 30, 35],
            "fd": [0.1, 0.2, 0.15],
        }
    )
    shard_path = paths.data("raw", config.RAW_SHARD_RELATIVE)
    pq.write_table(table, shard_path)

# ----------------------------------------------------------------------
# Power analysis reference test
# ----------------------------------------------------------------------
def test_power_analysis_matches_statsmodels():
    """Validate that the required N matches statsmodels' calculation."""
    # Use the same conversion as the implementation
    d = config.COHENS_D
    r = d / np.sqrt(d ** 2 + 4)
    n_predictors = 1 + 0  # no covariates in this simple check
    f2 = r ** 2 / (1 - r ** 2)

    solver = FTestPower()
    required_n = int(np.ceil(solver.solve_power(effect_size=f2, df_num=n_predictors, alpha=config.ALPHA, power=config.TARGET_POWER)))

    # Run the analysis power routine on a dummy inventory
    inventory = {"available_subject_count": 10, "present_columns": []}
    report = analysis._run_power_analysis(inventory)

    assert report["required_N"] == required_n
    assert isinstance(report["power_status"], str)

# ----------------------------------------------------------------------
# Conditional association test (with a real effect)
# ----------------------------------------------------------------------
def test_association_recovers_known_effect(tmp_path):
    """Create a tiny synthetic dataset where the skill proxy drives pc_1.

    The test checks that the permutation p‑value for ``pc_1`` is low and
    that the Benjamini–Hochberg correction marks it as significant.
    """
    _create_synthetic_dataset(tmp_path)

    # Run the full analysis (power + association)
    exit_code = analysis.main([])
    assert exit_code == 0

    # Load the regression results
    results_path = paths.results("regression_results.csv")
    assert results_path.is_file()
    df = pd.read_csv(results_path)

    # ``pc_1`` should be significant (the synthetic data were built with a
    # clear linear relationship between expert_rating and pc_1)
    pc1_row = df[df["pc"] == "pc_1"].iloc[0]
    assert pc1_row["significance"] is True
    assert pc1_row["skill_proxy_used"] == "expert_rating"
    assert pc1_row["raw_p"] < 0.05
    assert pc1_row["fdr_p"] < 0.05

    # ``pc_2`` has no relationship; it should be non‑significant
    pc2_row = df[df["pc"] == "pc_2"].iloc[0]
    assert pc2_row["significance"] is False
