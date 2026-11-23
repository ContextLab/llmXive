"""
Unit tests for the simulation mechanisms (code/simulation.py).

The tests verify:
* MCAR missingness achieves the target rate within ±0.5 %.
* MAR missingness probability correlates with the designated covariate (Spearman rho > 0.4).
* MNAR missingness depends jointly on the permuted outcome and permuted treatment
  (Spearman rho > 0.4 for both predictors).
"""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

# Ensure the project ``code`` directory is on the import path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from simulation import (
    simulate_mcar,
    simulate_mar,
    simulate_mnar,
    permute_treatment_labels,
)

def _create_dummy_data(n=1000, seed=123):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "treatment": rng.integers(0, 2, size=n),
        "outcome": rng.normal(0, 1, size=n),
        "age": rng.integers(18, 80, size=n),
        "sex": rng.choice([0, 1], size=n),
    })
    return df

def test_mcar_rate():
    df = _create_dummy_data()
    rate = 0.20
    df_mcar = simulate_mcar(df.copy(), rate=rate, target_cols=["outcome", "treatment"])
    missing_fraction = df_mcar.isna().mean().mean()
    assert abs(missing_fraction - rate) <= 0.005

def test_mar_correlation():
    df = _create_dummy_data()
    rate = 0.15
    df_mar = simulate_mar(df.copy(), rate=rate, target_cols=["outcome"], covariate="age")
    # Missingness indicator for outcome
    missing_indicator = df_mar["outcome"].isna().astype(int)
    rho, _ = spearmanr(missing_indicator, df["age"])
    assert rho > 0.4

def test_mnar_joint_dependence():
    df = _create_dummy_data()
    # Permute both treatment and outcome first
    df_perm = permute_treatment_labels(df.copy(), seed=999)
    df_perm["outcome"] = np.random.permutation(df_perm["outcome"].values)
    rate = 0.25
    df_mnar = simulate_mnar(df_perm.copy(), rate=rate, target_cols=["outcome"])
    missing_indicator = df_mnar["outcome"].isna().astype(int)
    rho_treat, _ = spearmanr(missing_indicator, df_perm["treatment"])
    rho_outcome, _ = spearmanr(missing_indicator, df_perm["outcome"])
    assert rho_treat > 0.4
    assert rho_outcome > 0.4
