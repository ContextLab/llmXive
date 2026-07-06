import os
import tempfile
from pathlib import Path
import pytest
from src.utils.logger import get_logger, setup_logging
from src.utils.config import Config, get_config, DEFAULT_AR_THRESHOLD

class TestLogger:
    def test_setup_logging_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=str(log_path))
            assert log_path.exists()
            assert logger is not None

    def test_get_logger_returns_instance(self):
        logger = get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"

    def test_get_logger_root(self):
        logger = get_logger()
        assert logger is not None
        assert logger.name == "root"


class TestConfig:
    def test_default_values(self):
        cfg = Config()
        assert cfg.ar_threshold == DEFAULT_AR_THRESHOLD
        assert cfg.lat_min == 20.0
        assert cfg.lat_max == 60.0
        assert isinstance(cfg.data_dir, Path)

    def test_from_env_overrides(self):
        # Save original env
        orig_val = os.environ.get("LMMXIVE_AR_THRESHOLD")
        try:
            os.environ["LMMXIVE_AR_THRESHOLD"] = "500"
            cfg = Config.from_env()
            assert cfg.ar_threshold == 500.0
        finally:
            # Restore
            if orig_val is None:
                del os.environ["LMMXIVE_AR_THRESHOLD"]
            else:
                os.environ["LMMXIVE_AR_THRESHOLD"] = orig_val

    def test_singleton_get_config(self):
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2
