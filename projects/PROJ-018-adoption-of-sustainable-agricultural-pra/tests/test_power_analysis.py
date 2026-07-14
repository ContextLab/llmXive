"""Simple test to ensure that the power‑analysis routine writes to the log."""

import json
from pathlib import Path

import yaml

from code.logging_config import get_logger, update_log_section
from code.config import get_modeling_log_path

def test_power_analysis_logged(tmp_path, monkeypatch):
    # Ensure a fresh log file.
    log_file = tmp_path / "modeling_log.yaml"
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    # Patch the config to point to our temporary log location.
    from code import config as cfg
    cfg.set_config("modeling_log_path", str(log_file))

    # Simulate a tiny dataset.
    import pandas as pd
    df = pd.DataFrame(
        {
            "age": [30, 45],
            "education": [12, 16],
            "farm_size": [1.2, 3.5],
            "credit": [0, 1],
            "adoption_binary": [1, 0],
            "membership": [1, 0],
            "extension_contact": [0, 1],
            "collective_action": [1, 1],
            "knowledge_exchange": [0, 0],
        }
    )

    # Directly call the power‑analysis function.
    from code import _02_clean_data as clean_mod
    result = clean_mod.calculate_power_analysis(df)

    # Verify the log file now contains the section.
    assert log_file.is_file()
    with log_file.open("r", encoding="utf-8") as fh:
        content = yaml.safe_load(fh)
    assert "power_analysis" in content
    assert content["power_analysis"]["ratio"] == result["ratio"]