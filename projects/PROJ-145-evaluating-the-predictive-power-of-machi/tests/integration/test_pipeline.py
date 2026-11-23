"""End-to-end smoke test for the project pipeline skeleton (T005)."""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


def test_project_layout_exists():
    for rel in (
        "code",
        "data/raw",
        "data/processed",
        "models",
        "tests/unit",
        "tests/integration",
    ):
        assert (PROJECT_ROOT / rel).exists(), f"missing directory: {rel}"


def test_config_random_seed_is_pinned():
    from code.config import RANDOM_SEED

    assert RANDOM_SEED == 42


def test_config_logging_setup():
    from code.config import setup_logging

    logger = setup_logging()
    assert logger is not None


def test_compute_checksum_module_importable():
    sys.path.insert(0, str(PROJECT_ROOT / "code"))
    from compute_checksum import compute_file_checksum

    assert callable(compute_file_checksum)


def test_feature_engineering_importable():
    try:
        from code import feature_engineering
    except ImportError as exc:
        pytest.skip(f"feature_engineering unavailable: {exc}")
    assert hasattr(feature_engineering, "process_dataset")
