"""Tests for T001: config schema, layout, and checksum."""
import hashlib
from pathlib import Path

import pytest
import yaml

from code.pipeline.run_all import (
    REQUIRED_KEYS,
    load_and_validate_config,
    main,
    sha256_of,
    write_checksum_manifest,
)
from llmxive_toolkit import paths

CONFIG = paths.path("code", "config", "study_config.yaml")


def test_config_contains_all_required_keys():
    assert CONFIG.is_file(), f"missing config: {CONFIG}"
    with open(CONFIG, encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    assert set(config.keys()) == set(REQUIRED_KEYS.keys())
    assert set(config["effect_sizes"].keys()) == {
        "SART", "Ospan", "PSS-10", "PANAS-PA", "PANAS-NA"
    }
    assert config["practice_effect_grid"] == [0.0, 0.2, 0.4]
    assert config["bootstrap_resamples"] == 10000
    assert config["pilot_n"] == 5
    assert isinstance(config["seed"], int)


def test_load_config_rejects_missing_key(tmp_path):
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    del cfg["seed"]
    tmp = tmp_path / "_tmp_bad_config.yaml"
    tmp.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required keys"):
        load_and_validate_config(str(tmp))


def test_load_config_rejects_bad_grid(tmp_path):
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    cfg["practice_effect_grid"] = [0.0, 0.1]
    tmp = tmp_path / "_tmp_bad_config.yaml"
    tmp.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ValueError, match="practice_effect_grid"):
        load_and_validate_config(str(tmp))


def test_load_config_rejects_bad_date(tmp_path):
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    cfg["start_date"] = "21-05-2024"
    tmp = tmp_path / "_tmp_bad_config.yaml"
    tmp.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ValueError, match="start_date"):
        load_and_validate_config(str(tmp))


def test_run_all_executes_and_writes_outputs():
    rc = main(["--config", str(CONFIG)])
    assert rc == 0
    status = paths.data("results", "pipeline_status.json")
    assert status.is_file()
    manifest = paths.data("checksums.sha256")
    assert manifest.is_file()
    text = manifest.read_text(encoding="utf-8")
    assert "pipeline_status.json" in text


def test_manifest_checksums_match_files():
    main(["--config", str(CONFIG)])
    manifest = paths.data("checksums.sha256")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        path = paths.root / rel
        assert path.is_file(), f"manifest references missing file {rel}"
        assert sha256_of(path) == digest


def test_requirements_pinned():
    req = paths.path("code", "requirements.txt")
    assert req.is_file()
    for line in req.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert "==" in line, f"unpinned dependency: {line}"