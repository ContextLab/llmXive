"""Unit tests for the LOGO jackknife module (Task T016)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Make the project's code/ package importable when pytest runs from the
# project root or from tests/unit.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
for candidate in (str(CODE_DIR),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from preprocess.logo_jackknife import (  # noqa: E402
    compute_cv,
    compute_variance,
    cross_layer_logo_split,
    disjoint_generation_split,
    logo_folds,
    logo_jackknife_from_long,
    logo_jackknife_variance,
)


class TestLogoFolds:
    def test_each_generation_held_out_once(self):
        labels = [1, 1, 2, 2, 3, 3]
        folds = logo_folds(labels)
        assert len(folds) == 3
        held_out_gens = [set(labels[i] for i in held) for _, held in folds]
        assert held_out_gens == [{1}, {2}, {3}]

    def test_folds_are_disjoint(self):
        labels = ["G1", "G2", "G3", "G4"]
        folds = logo_folds(labels)
        for train, held in folds:
            assert len(set(train.tolist()) & set(held.tolist())) == 0

    def test_train_covers_all_other_samples(self):
        labels = [1, 2, 3]
        folds = logo_folds(labels)
        for (train, held), gen in zip(folds, [1, 2, 3]):
            assert len(train) == 2
            assert labels[held[0]] == gen

    def test_empty_input(self):
        assert logo_folds([]) == []


class TestDisjointSplit:
    def test_odd_even_generation_partition(self):
        labels = [1, 1, 2, 3, 4, 5]
        a, b = disjoint_generation_split(labels)
        gens_a = {labels[i] for i in a}
        gens_b = {labels[i] for i in b}
        assert gens_a == {1, 3, 5}
        assert gens_b == {2, 4}
        assert not (set(a) & set(b))

    def test_single_generation_all_in_layer_a(self):
        labels = [7, 7, 7]
        a, b = disjoint_generation_split(labels)
        assert sorted(a) == [0, 1, 2]
        assert b == []


class TestVarianceStatistics:
    def test_cv_known_value(self):
        assert compute_cv([1.0, 3.0]) == pytest.approx(0.5)

    def test_cv_zero_mean_is_zero(self):
        assert compute_cv([0.0, 0.0, 0.0]) == 0.0

    def test_cv_handles_nan(self):
        assert compute_cv([np.nan, 2.0, 4.0]) == pytest.approx(0.5)

    def test_variance_known_value(self):
        assert compute_variance([1.0, 2.0, 3.0]) == pytest.approx(2.0 / 3.0)


class TestLogoJackknifeVariance:
    def test_constant_series_zero_variance(self):
        res = logo_jackknife_variance(
            [5.0, 5.0, 5.0, 5.0], [1, 1, 2, 2], variance_fn=compute_variance
        )
        assert res["estimate"] == pytest.approx(0.0)
        assert res["std_error"] == pytest.approx(0.0)

    def test_jackknife_recovers_positive_variance(self):
        values = [1.0, 2.0, 3.0, 4.0]
        labels = [1, 1, 2, 2]
        res = logo_jackknife_variance(values, labels, variance_fn=compute_variance)
        assert res["estimate"] > 0
        assert res["n_folds"] == 2
        assert res["n_samples"] == 4
        assert res["ci_lower"] <= res["estimate"] <= res["ci_upper"]

    def test_single_generation_no_uncertainty(self):
        res = logo_jackknife_variance(
            [1.0, 2.0], [1, 1], variance_fn=compute_variance
        )
        assert res["n_folds"] == 1
        assert res["estimate"] == pytest.approx(0.25)
        assert res["std_error"] is None

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            logo_jackknife_variance([1.0, 2.0], [1, 2, 3])


class TestLogoJackknifeFromLong:
    def _make_long_df(self):
        rng = np.random.default_rng(42)
        rows = []
        for gene in ["geneA", "geneB"]:
            for gen in [1, 2, 3, 4]:
                for _ in range(3):
                    rows.append(
                        {
                            "gene": gene,
                            "generation": gen,
                            "sample": f"{gene}_G{gen}_{rng.integers(1e6)}",
                            "value": rng.normal(10, 1),
                        }
                    )
        return pd.DataFrame(rows)

    def test_output_structure(self):
        df = self._make_long_df()
        out = logo_jackknife_from_long(df, feature_col="gene")
        assert set(out["gene"]) == {"geneA", "geneB"}
        for col in [
            "variance_estimate",
            "variance_std_error",
            "variance_ci_lower",
            "variance_ci_upper",
            "n_folds",
            "n_samples",
        ]:
            assert col in out.columns
        assert (out["n_folds"] == 4).all()
        assert (out["n_samples"] == 12).all()

    def test_missing_column_raises(self):
        df = pd.DataFrame({"gene": ["a"], "value": [1.0]})
        with pytest.raises(ValueError):
            logo_jackknife_from_long(df, feature_col="gene")


class TestCrossLayerSplit:
    def test_disjoint_layers(self):
        df = pd.DataFrame(
            {
                "generation": [1, 1, 2, 3, 4, 4, 5],
                "value": range(7),
            }
        )
        a, b = cross_layer_logo_split(df)
        assert set(a["generation"]) == {1, 3, 5}
        assert set(b["generation"]) == {2, 4}
        assert len(a) + len(b) == len(df)

    def test_missing_generation_column_raises(self):
        df = pd.DataFrame({"value": [1, 2]})
        with pytest.raises(ValueError):
            cross_layer_logo_split(df)