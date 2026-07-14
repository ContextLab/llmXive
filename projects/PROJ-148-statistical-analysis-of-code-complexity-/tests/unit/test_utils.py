import pytest
import os
import sys
import logging
from pathlib import Path
import numpy as np

# Add project root to path if not already
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_seed, set_random_seed, Config
from utils.logging import get_logger, get_project_logger
from utils.checksum import hash_bytes, hash_file, hash_dataframe, verify_checksum


class TestConfig:
    def test_get_seed_default(self, monkeypatch):
        monkeypatch.delenv("RANDOM_SEED", raising=False)
        assert get_seed() == 42

    def test_get_seed_from_env(self, monkeypatch):
        monkeypatch.setenv("RANDOM_SEED", "123")
        assert get_seed() == 123

    def test_set_random_seed(self):
        set_random_seed(99)
        val = np.random.random()
        set_random_seed(99)
        val2 = np.random.random()
        assert val == val2

    def test_config_default(self):
        cfg = Config()
        assert cfg.seed == 42
        assert cfg.data_dir == "data"

    def test_config_custom(self):
        cfg = Config(seed=100, data_dir="custom_data")
        assert cfg.seed == 100
        assert cfg.data_dir == "custom_data"


class TestLogging:
    def test_get_logger_returns_instance(self):
        logger = get_logger("test_logger_unit")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger_unit"

    def test_get_project_logger(self):
        logger = get_project_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive"

    def test_logger_level_default(self):
        logger = get_logger("test_level_default")
        assert logger.level == logging.WARNING

    def test_logger_level_set(self):
        logger = get_logger("test_level_set")
        logger.setLevel(logging.DEBUG)
        assert logger.level == logging.DEBUG


class TestChecksum:
    def test_hash_bytes(self):
        data = b"hello"
        h1 = hash_bytes(data)
        h2 = hash_bytes(data)
        assert h1 == h2
        assert len(h1) == 64

    def test_hash_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        h1 = hash_file(test_file)
        h2 = hash_file(test_file)
        assert h1 == h2
        assert len(h1) == 64

    def test_hash_file_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            hash_file(Path("nonexistent.txt"))

    def test_hash_dataframe(self):
        import pandas as pd
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        h1 = hash_dataframe(df)
        h2 = hash_dataframe(df)
        assert h1 == h2
        assert len(h1) == 64

    def test_hash_dataframe_unchanged(self):
        import pandas as pd
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        h1 = hash_dataframe(df)
        # Modify df in place
        df.iloc[0, 0] = 10
        h2 = hash_dataframe(df)
        assert h1 != h2

    def test_verify_checksum_match(self, tmp_path):
        test_file = tmp_path / "verify.txt"
        test_file.write_text("verify content")
        checksum = hash_file(test_file)
        assert verify_checksum(test_file, checksum) is True

    def test_verify_checksum_mismatch(self, tmp_path):
        test_file = tmp_path / "verify_fail.txt"
        test_file.write_text("verify content")
        fake_checksum = "a" * 64
        assert verify_checksum(test_file, fake_checksum) is False