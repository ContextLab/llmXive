"""
code/tests/test_run_fallback.py
--------------------------------
Simple integration test that ensures the ``run_fallback`` driver
executes without raising and produces the expected artefacts
when the ``fallback_needed`` flag is set.

The test creates a minimal ``performance.json`` with the flag set,
a dummy ``features_augmented.csv`` file, and then invokes the driver.
After execution it checks that:
  * ``features.csv`` exists and matches the augmented file.
  * The split CSVs, model artefacts and updated performance JSON are
    present.
  * The ``fallback_needed`` flag in the updated JSON is ``False``.

This test does **not** validate model quality – it only verifies the
orchestration logic required by task T016.
"""

import json
import shutil
from pathlib import Path

import pytest

from llmxive_toolkit import paths


@pytest.fixture
def dummy_environment(tmp_path: Path):
    """
    Set up a minimal environment required for the fallback driver:
    * A dummy ``performance.json`` with ``fallback_needed=True``.
    * A tiny but valid ``features_augmented.csv`` (the schema is not
      enforced here – the downstream scripts will handle any validation
      errors).
    * Placeholder raw data files so that downstream scripts do not fail
      on missing inputs.
    """
    # Ensure the project data directories exist.
    for sub in ["processed", "raw", "checksums"]:
        (paths.data(sub)).mkdir(parents=True, exist_ok=True)

    # 1) Dummy performance.json
    perf_path = paths.data("processed", "performance.json")
    perf_path.write_text(
        json.dumps(
            {
                "cv_metrics": {},
                "test_metrics": {},
                "bootstrap_ci": {},
                "paired_ttest": {},
                "fallback_needed": True,
            }
        )
    )

    # 2) Dummy augmented features CSV
    aug_path = paths.data("processed", "features_augmented.csv")
    aug_path.write_text(
        "composition,formation_energy,A_atomic_radius,B_atomic_radius,X_atomic_radius\n"
        "ABX3,1.0,1.0,2.0,3.0\n"
    )

    # 3) Minimal raw dataset – required by downstream scripts.
    raw_path = paths.data("raw", "materials_defects.csv")
    raw_path.write_text(
        "composition,defect_type,formation_energy\n"
        "ABX3,oxygen_vacancy,1.0\n"
    )

    # 4) Create a dummy checksum file so that checksum utilities succeed.
    (paths.checksums("raw_defects.sha256")).write_text(
        "d41d8cd98f00b204e9800998ecf8427e"
    )

    return {
        "perf_path": perf_path,
        "aug_path": aug_path,
        "raw_path": raw_path,
    }


def test_run_fallback_executes(dummy_environment, monkeypatch):
    """
    Execute the fallback driver and verify that the expected artefacts
    are produced.
    """
    # Import the driver lazily so that the fixture has created the files.
    from code.pipeline.run_fallback import main

    # Run the driver – it should complete without raising.
    main()

    # a) ``features.csv`` should now be a copy of the augmented file.
    features_path = paths.data("processed", "features.csv")
    assert features_path.is_file()
    assert features_path.read_text() == dummy_environment["aug_path"].read_text()

    # b) Split artefacts.
    assert paths.data("processed", "train.csv").is_file()
    assert paths.data("processed", "test.csv").is_file()
    assert paths.checksums("train.sha256").is_file()
    assert paths.checksums("test.sha256").is_file()

    # c) Model artefacts.
    assert Path("models/rf_cv.pkl").is_file()
    assert Path("models/gb_cv.pkl").is_file()
    assert paths.data("processed", "cv_metrics.json").is_file()

    # d) Updated performance JSON – flag must be cleared.
    updated_perf = json.loads(paths.data("processed", "performance.json").read_text())
    assert not updated_perf.get("fallback_needed", True)

    # e) Feature‑importance artefacts.
    assert paths.data("processed", "performance.json").is_file()
    assert Path("figures/feature_importance.png").is_file()
    assert Path("figures/pred_vs_actual.png").is_file()

# The integration test is marked as such to avoid running during the
# fast unit‑test pass; it will be executed when the full test suite
# runs.
@pytest.mark.integration
def test_run_fallback_integration(dummy_environment):
    # Re‑use the same driver – the integration marker signals the CI to
    # treat this as a longer‑running test.
    from code.pipeline.run_fallback import main

    main()
    # Basic sanity checks (same as above) – ensure no exceptions were raised.
    assert paths.data("processed", "features.csv").is_file()
    assert Path("models/rf_cv.pkl").is_file()
    assert Path("figures/pred_vs_actual.png").is_file()