"""T028: verify code/config.py constants exist with expected types/values."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code import config


def test_tmp_dir_is_path():
    assert isinstance(config.TMP_DIR, Path)
    assert config.TMP_DIR.exists()
    assert config.TMP_DIR.is_dir()


def test_data_dirs_are_paths():
    for d in (config.DATA_RAW_DIR, config.DATA_INTERIM_DIR, config.DATA_PROCESSED_DIR):
        assert isinstance(d, Path)
        assert d.exists()


def test_retry_constants():
    assert config.MAX_RETRIES == 3
    assert isinstance(config.MAX_RETRIES, int)
    assert config.RETRY_BACKOFF == 2
    assert isinstance(config.RETRY_BACKOFF, int)


def test_expected_cell_types():
    assert config.EXPECTED_CELL_TYPES == ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']
    assert isinstance(config.EXPECTED_CELL_TYPES, list)
    assert all(isinstance(ct, str) for ct in config.EXPECTED_CELL_TYPES)