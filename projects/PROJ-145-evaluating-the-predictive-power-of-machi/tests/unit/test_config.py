"""Unit tests for code/config.py (T002)."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

import config


def test_import_succeeds():
    assert config is not None


def test_random_seed_is_42():
    assert config.RANDOM_SEED == 42


def test_expected_aflow_checksum_placeholder():
    # Placeholder checksum is a valid 64-char hex SHA-256 string.
    assert isinstance(config.EXPECTED_AFLOW_CHECKSUM, str)
    assert len(config.EXPECTED_AFLOW_CHECKSUM) == 64
    int(config.EXPECTED_AFLOW_CHECKSUM, 16)  # must be hex


def test_path_constants():
    assert config.PROJECT_ROOT == PROJECT_ROOT
    assert config.DATA_RAW == PROJECT_ROOT / "data" / "raw"
    assert config.DATA_PROCESSED == PROJECT_ROOT / "data" / "processed"
    assert config.DATA_MODELS == PROJECT_ROOT / "models"


def test_element_source_list_nonempty():
    assert len(config.ELEMENT_SOURCE_LIST) > 0
    assert all(isinstance(e, str) for e in config.ELEMENT_SOURCE_LIST)