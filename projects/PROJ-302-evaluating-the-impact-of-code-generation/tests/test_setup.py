"""Tests for T001: project skeleton and pinned dependencies."""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PACKAGES = [
    "datasets", "scikit-learn", "pandas", "numpy", "scipy", "statsmodels",
    "radon", "torch", "transformers", "matplotlib", "seaborn", "pyyaml",
    "requests", "gitpython", "pytest", "ruff", "black", "pyarrow",
    "codecarbon", "tenacity",
]

SKELETON_DIRS = [
    "code", "data/raw", "data/processed", "data/synthetic", "data/reports",
    "tests/unit", "tests/integration", "docs",
]


def test_skeleton_directories_exist():
    for d in SKELETON_DIRS:
        assert (PROJECT_ROOT / d).is_dir(), f"missing directory: {d}"


def test_requirements_exist_and_pinned():
    req = PROJECT_ROOT / "requirements.txt"
    assert req.exists()
    pins = {}
    for line in req.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert re.match(r"^[A-Za-z0-9_.\-]+==\S+$", line), f"not pinned: {line}"
        name, _ = line.split("==", 1)
        pins[name.lower().replace("_", "-")] = True
    for pkg in REQUIRED_PACKAGES:
        assert pkg in pins, f"{pkg} not pinned in requirements.txt"


def test_statsmodels_pinned():
    content = (PROJECT_ROOT / "requirements.txt").read_text()
    assert re.search(r"^statsmodels==[\d.]+$", content, re.MULTILINE)


def test_quickstart_has_run_command():
    qs = PROJECT_ROOT / "docs" / "quickstart.md"
    assert qs.exists()
    text = qs.read_text()
    assert "Run-the-pipeline" in text
    assert "python code/main.py --full-run" in text


def test_core_dependencies_importable():
    import pandas  # noqa: F401
    import numpy  # noqa: F401
    import scipy  # noqa: F401
    import sklearn  # noqa: F401
    import statsmodels  # noqa: F401
    import matplotlib  # noqa: F401
    import seaborn  # noqa: F401