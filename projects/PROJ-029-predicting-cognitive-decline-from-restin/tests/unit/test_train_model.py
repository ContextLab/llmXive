"""Basic unit test for the training script's core functions."""

import pandas as pd
import numpy as np
from pathlib import Path

# Import functions directly from the module under test
from code import (
    define_decline_label,
    CollinearityTransformer,
    make_inner_pipeline,
)


def test_define_decline_label():
    baseline = pd.Series([30, 28, 25, 27])
    followup = pd.Series([27, 25, 23, 27])
    labels = define_decline_label(baseline, followup, threshold=3)
    expected = pd.Series([1, 1, 1, 0])
    pd.testing.assert_series_equal(labels, expected)


def test_collinearity_transformer():
    # Create a dataframe with two perfectly correlated columns
    rng = np.random.RandomState(0)
    a = rng.normal(size=100)
    df = pd.DataFrame({"a": a, "b": a * 1.0, "c": rng.normal(size=100)})
    transformer = CollinearityTransformer(corr_thresh=0.99)
    transformer.fit(df)
    transformed = transformer.transform(df)
    # One of the correlated columns should be dropped, leaving 2 columns total
    assert transformed.shape[1] == 2
    assert "a" in transformed.columns or "b" in transformed.columns


def test_make_inner_pipeline():
    pipeline = make_inner_pipeline()
    # The pipeline should contain the expected named steps
    expected_steps = ["collinearity", "scale", "var_thresh", "rfe", "clf"]
    assert [name for name, _ in pipeline.steps] == expected_steps
    # Fit on tiny synthetic data to ensure no runtime errors
    X = pd.DataFrame(np.random.rand(10, 5), columns=[f"f{i}" for i in range(5)])
    y = np.random.randint(0, 2, size=10)
    pipeline.fit(X, y)
    # Predict should return an array of the correct length
    preds = pipeline.predict(X)
    assert len(preds) == 10


# The test suite will be discovered by pytest via the standard convention.