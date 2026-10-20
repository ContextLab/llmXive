"""Verify that the data/processed/ directory exists (task T002b)."""
from pathlib import Path

from llmxive_toolkit import paths

def test_data_processed_dir_exists():
    processed = Path(paths.root) / "data" / "processed"
    assert processed.is_dir(), f"{processed} does not exist"

def test_setup_script_creates_dir(tmp_path):
    import importlib.util
    script = Path(paths.code("setup_data_dirs.py"))
    assert script.is_file(), "setup script missing"
    spec = importlib.util.spec_from_file_location("setup_data_dirs", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
    assert (Path(paths.root) / "data" / "processed").is_dir()