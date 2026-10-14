"""Unit tests for code/config.py (T001a)."""
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _import_config():
    import code.config as cfg
    return cfg


def test_seed_constant():
    cfg = _import_config()
    assert cfg.SEED == 12345


def test_primary_model_id():
    cfg = _import_config()
    assert cfg.PRIMARY_MODEL_ID in ("Mistral-7B", "Llama-3-8B")


def test_path_helpers_exist():
    cfg = _import_config()
    for name in ("data_path", "figures_path", "results_path", "docs_path"):
        assert callable(getattr(cfg, name))


def test_data_path_creates_directory(tmp_path, monkeypatch):
    cfg = _import_config()
    p = cfg.data_path("unit_test_dir", "x.parquet")
    assert p.parent.exists()
    assert str(p).startswith(str(PROJECT_ROOT / "data"))


def test_requirements_pinned():
    req = (PROJECT_ROOT / "code" / "requirements.txt").read_text()
    required = [
        "datasets", "transformers", "tree-sitter", "tree-sitter-python",
        "tree-sitter-java", "scikit-learn", "statsmodels", "pandas",
        "numpy", "scipy", "matplotlib", "seaborn", "kenlm", "ruptures",
        "pwlf", "jsonschema", "pytest", "pytest-cov", "psutil",
    ]
    lines = [
        ln.strip() for ln in req.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    for pkg in required:
        pinned = [ln for ln in lines if ln.split("==")[0].strip().lower() == pkg]
        assert pinned, f"{pkg} not pinned in requirements.txt"
        assert "==" in pinned[0], f"{pkg} is not pinned to an exact version"


def test_config_importable_as_module():
    # Mirrors the task verification: `python -c "import code.config"`
    cfg = importlib.import_module("code.config")
    assert cfg is not None