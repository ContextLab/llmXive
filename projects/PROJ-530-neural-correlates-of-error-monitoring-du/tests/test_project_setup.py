"""T004: verify the project declares Python 3.11 and all required dependencies."""
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "mne", "pandas", "numpy", "scipy", "statsmodels", "pymer4",
    "pingouin", "matplotlib", "seaborn", "pyyaml", "psutil",
    "pytest", "pygam",
]

def _parse_req(line):
    name = line.split("==")[0].split(">=")[0].split("<=")[0]
    return name.strip().lower().replace("-", "-")

def test_requirements_txt_lists_all_dependencies():
    req = (ROOT / "requirements.txt").read_text()
    names = {
        _parse_req(l.strip()) for l in req.splitlines()
        if l.strip() and not l.strip().startswith("#")
    }
    missing = [p for p in REQUIRED if p.lower() not in names]
    assert not missing, f"requirements.txt missing: {missing}"

def test_pyproject_requires_python_311():
    with open(ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    spec = data["project"]["requires-python"]
    assert "3.11" in spec
    deps = [d.split("==")[0].lower() for d in data["project"]["dependencies"]]
    missing = [p for p in REQUIRED if p.lower() not in deps]
    assert not missing, f"pyproject.toml missing: {missing}"

def test_core_packages_importable():
    import mne  # noqa: F401
    import pandas  # noqa: F401
    import numpy  # noqa: F401
    import scipy  # noqa: F401
    import statsmodels  # noqa: F401
    import pygam  # noqa: F401