"""Basic sanity test that the main pipeline runs without raising.

The test imports the public ``run_pipeline`` function from ``code.main`` and
asserts that it completes successfully.  The heavy‑weight steps (model
loading) are mocked to keep CI fast.
"""

import builtins
from unittest import mock

import pytest

from code.main import run_pipeline

@mock.patch("code.model_metrics.main")
@mock.patch("code.ast_cloner.compute_clone_density_batch")
@mock.patch("code.data_loader.download_and_save_sample")
def test_pipeline_runs(
    mock_download,
    mock_clone,
    mock_model,
):
    # Arrange – make the mocked functions behave like the real ones.
    mock_download.return_value = "data/raw/github-code-sample.csv"
    mock_clone.return_value = None
    mock_model.return_value = None

    # Act – should not raise.
    run_pipeline()