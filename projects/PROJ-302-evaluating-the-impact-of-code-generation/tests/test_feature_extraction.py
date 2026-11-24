"""
Integration test for ``code/feature_extraction.py`` (T005).

The test runs the ``main`` function and then checks that:
  * ``data/processed/merged_features.parquet`` exists,
  * it contains the five required covariate columns,
  * the ``semantic_similarity`` values lie in the interval [-1, 1],
  * ``data/processed/covariate_config.json`` lists exactly the expected
    covariates in order.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from code.feature_extraction import main as feature_extraction_main
from llmxive_toolkit import paths

@pytest.mark.parametrize("skip_if_missing", [True])
def test_feature_extraction_outputs(tmp_path, monkeypatch):
    """
    Run the feature extraction script and validate its outputs.

    The test is deliberately lightweight – it does **not** fabricate any
    input data.  If the required upstream artefacts are missing the
    ``main`` function will raise an informative exception, causing the
    test to fail (which is the correct behaviour for an incomplete pipeline).
    """
    # Ensure that the paths used by the script point inside the temporary
    # test directory so we do not interfere with the real project data.
    # The ``paths`` helper creates directories on demand; we only need to
    # make sure the base ``project`` root points to the temporary location.
    # ``llmxive_toolkit.paths`` resolves relative to the real project root,
    # which is fine for this test because we only check that files are
    # created – they will be written under the real ``data/processed`` folder.
    # No monkey‑patching of the filesystem is required.

    # Run the feature extraction pipeline.
    feature_extraction_main()

    # 1. Verify merged_features.parquet exists and has required columns.
    merged_path = paths.data("processed", "merged_features.parquet")
    assert merged_path.is_file(), f"{merged_path} was not created"

    df = pd.read_parquet(merged_path)
    required_cols = {
        "file_size_loc",
        "complexity_score",
        "repo_activity_level",
        "ci_build_time",
        "semantic_similarity",
    }
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing required columns in merged_features.parquet: {missing}"

    # 2. Semantic similarity must be within [-1, 1].
    sims = df["semantic_similarity"].dropna()
    assert sims.between(-1.0, 1.0).all(), "Semantic similarity out of bounds"

    # 3. Verify covariate_config.json content.
    config_path = paths.data("processed", "covariate_config.json")
    assert config_path.is_file(), f"{config_path} was not created"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    expected_config = [
        "file_size_loc",
        "complexity_score",
        "repo_activity_level",
        "ci_build_time",
        "semantic_similarity",
    ]
    assert config == expected_config, "Covariate config does not match expected list"