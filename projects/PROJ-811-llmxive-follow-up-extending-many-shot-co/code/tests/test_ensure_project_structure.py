"""Tests for code/scripts/ensure_project_structure.py (T001)."""
import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "code" / "scripts" / "ensure_project_structure.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "ensure_project_structure", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["ensure_project_structure"] = module
    spec.loader.exec_module(module)
    return module


def test_required_dirs_exist():
    mod = _load_module()
    mod.ensure_dirs()
    for rel in mod.REQUIRED_DIRS:
        assert (PROJECT_ROOT / rel).is_dir(), f"missing {rel}"


def test_verify_passes_after_setup(tmp_path, monkeypatch):
    mod = _load_module()
    # Point the module's PROJECT_ROOT at an isolated temp tree.
    for rel in mod.REQUIRED_DIRS:
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)
    assert mod.verify() is True


def test_relocate_root_tests_moves_files(tmp_path, monkeypatch):
    mod = _load_module()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_example.py").write_text(
        "def test_x():\n    assert True\n"
    )
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)
    mod.relocate_root_tests()
    assert (tmp_path / "code" / "tests" / "test_example.py").exists()
    assert not (tmp_path / "tests").exists()