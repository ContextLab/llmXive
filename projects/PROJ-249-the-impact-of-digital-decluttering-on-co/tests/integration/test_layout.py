"""
Integration test for project layout (T001).

The test invokes the pipeline setup script and then verifies that all
required directories exist.
"""

import pytest
from pathlib import Path

from code.pipeline.run_all import main, REQUIRED_KEYS, REQUIRED_METRICS

def test_layout_creation(tmp_path, monkeypatch):
    """
    Run the pipeline with a temporary configuration file and ensure that
    the expected directories are created.
    """
    # Copy the existing config to a temporary location
    orig_cfg = Path(__file__).parents[3] / "code" / "config" / "study_config.yaml"
    tmp_cfg = tmp_path / "study_config.yaml"
    tmp_cfg.write_text(orig_cfg.read_text(encoding="utf-8"), encoding="utf-8")

    # Monkey‑patch the paths.root to the temporary directory so that all
    # created folders live under tmp_path.
    monkeypatch.setattr("llmxive_toolkit.paths.root", tmp_path)

    # Run the pipeline
    rc = main(["--config", str(tmp_cfg)])
    assert rc == 0

    # Expected directories (relative to the temporary root)
    expected_dirs = [
        "code/scoring",
        "code/analysis",
        "code/compliance",
        "code/viz",
        "code/validation",
        "code/pipeline",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/results",
        "figures",
    ]

    for rel in expected_dirs:
        assert (tmp_path / rel).is_dir(), f"Missing directory: {rel}"

    # Verify that the config contains exactly the required keys
    import yaml
    cfg = yaml.safe_load(tmp_cfg.read_text(encoding="utf-8"))
    assert set(cfg.keys()) == set(REQUIRED_KEYS.keys())
    assert set(cfg["effect_sizes"].keys()) == set(REQUIRED_METRICS)      
