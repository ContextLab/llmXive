import os
import shutil
from pathlib import Path

from config import ensure_directories, get_raw_dir, get_processed_dir, get_stratified_dir, get_features_dir, get_results_dir, get_figures_dir

def test_ensure_directories_various_calls(tmp_path, monkeypatch):
    """
    Verify that ``ensure_directories`` works with the different call signatures
    required by the project.
    """
    # Patch the project‑root directories to a temporary location
    base = tmp_path / "proj"
    base.mkdir()
    monkeypatch.setattr("config.RAW_DIR", base / "data" / "raw")
    monkeypatch.setattr("config.PROCESSED_DIR", base / "data" / "processed")
    monkeypatch.setattr("config.STRATIFIED_DIR", base / "data" / "stratified")
    monkeypatch.setattr("config.FEATURES_DIR", base / "data" / "features")
    monkeypatch.setattr("config.RESULTS_DIR", base / "data" / "results")
    monkeypatch.setattr("config.FIGURES_DIR", base / "figures")

    # No‑arg call creates all standard dirs
    ensure_directories()
    for d in [
        get_raw_dir(),
        get_processed_dir(),
        get_stratified_dir(),
        get_features_dir(),
        get_results_dir(),
        get_figures_dir(),
    ]:
        assert d.is_dir()

    # Single custom path
    custom = base / "custom_dir"
    ensure_directories(custom)
    assert custom.is_dir()

    # List of paths
    lst = [base / "list1", base / "list2"]
    ensure_directories(lst)
    for p in lst:
        assert p.is_dir()

# Cleanup is handled by pytest's tmp_path fixture