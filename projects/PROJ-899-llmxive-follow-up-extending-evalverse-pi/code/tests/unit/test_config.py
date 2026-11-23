import os
import tempfile
from pathlib import Path
import pytest
import sys
import json

# Mock imports for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

class TestEnvironmentSetup:
    def test_directories_created(self):
        from src.config import ensure_environment, get_project_root
        ensure_environment()
        assert get_project_root().exists()

class TestConfigurationValues:
    def test_random_seed(self):
        from src.config import RANDOM_SEED
        assert RANDOM_SEED == 42

    def test_thresholds(self):
        from src.config import CORRELATION_THRESHOLD
        assert CORRELATION_THRESHOLD == 0.85

class TestConfigSummary:
    def test_get_config_summary(self):
        from src.config import get_config_summary
        summary = get_config_summary()
        assert "project_root" in summary
        assert "data_root" in summary
