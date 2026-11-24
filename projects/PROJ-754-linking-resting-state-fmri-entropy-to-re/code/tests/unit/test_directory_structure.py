"""
Unit test ensuring that the expected source directories exist and contain
at least one Python file each.
"""

from pathlib import Path

def test_required_directories_and_modules():
    """
    Verify that each required package directory exists and that a
    non‑``__init__`` ``.py`` file is present.
    """
    root = Path(__file__).resolve().parents[2]  # project root
    src_root = root / "code" / "src"

    required_packages = [
        "data",
        "analysis",
        "stats",
        "config",
        "utils",
        "entities",
        "reporting",
    ]

    for pkg in required_packages:
        pkg_path = src_root / pkg
        assert pkg_path.is_dir(), f"Package directory missing: {pkg_path}"
        # There must be at least one .py file that is not __init__.py
        py_files = [p for p in pkg_path.glob("*.py") if p.name != "__init__.py"]
        assert py_files, f"No implementation file found in {pkg_path}"
