import json
import pathlib

import pytest

import analysis  # noqa: E402

def test_power_computation(tmp_path, monkeypatch):
    # Prepare a fake column inventory with 30 subjects
    inventory = {
        "available_subject_count": 30,
        "columns": ["subject_id", "expert_rating"]
    }
    inv_path = tmp_path / "column_inventory.json"
    inv_path.write_text(json.dumps(inventory))

    # Patch paths to use the temporary directory
    from llmxive_toolkit import paths
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / pathlib.Path(*parts))

    # Run power analysis
    result = analysis._run_power_analysis(inventory)

    # Verify fields
    assert "required_n" in result
    assert "available_n" in result
    assert result["available_n"] == 30
    # With r≈0.243 the required N should be >30, leading to insufficient status
    assert result["power_status"] == "insufficient"

def test_association_halts_when_no_proxy(tmp_path, monkeypatch, caplog):
    # Inventory without any skill proxy columns
    inventory = {"available_subject_count": 20, "columns": ["subject_id"]}
    inv_path = tmp_path / "column_inventory.json"
    inv_path.write_text(json.dumps(inventory))

    from llmxive_toolkit import paths
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / pathlib.Path(*parts))
    monkeypatch.setattr(paths, "results", lambda *parts: tmp_path / pathlib.Path(*parts))

    # Run analysis main – it should not raise and should log the halt message
    exit_code = analysis.main([])
    assert exit_code == 0
    # Check that the log contains the expected message
    assert any("No skill‑proxy column present; association stage halted" in rec.message for rec in caplog.records)
