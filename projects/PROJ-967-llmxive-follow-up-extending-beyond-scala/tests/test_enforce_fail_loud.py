"""
Tests for T000e: Enforce 'Fail Loud' for missing real data.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from enforce_fail_loud import check_for_real_data, main

class TestEnforceFailLoud:
    """Tests for the fail-loud logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        
        # Patch the global paths in the module
        import enforce_fail_loud
        self.original_config_path = enforce_fail_loud.CONFIG_PATH
        self.original_research_path = enforce_fail_loud.RESEARCH_MD_PATH
        self.original_raw_data_path = self.project_root / "data" / "raw" / "z_reward.parquet"
        
        enforce_fail_loud.CONFIG_PATH = self.project_root / "data" / "processed" / "config.json"
        enforce_fail_loud.RESEARCH_MD_PATH = self.project_root / "specs" / "001-llmxive-follow-up-extending-beyond-scala" / "research.md"
        
        # Create necessary directories
        (self.project_root / "data" / "processed").mkdir(parents=True)
        (self.project_root / "data" / "raw").mkdir(parents=True)
        (self.project_root / "specs" / "001-llmxive-follow-up-extending-beyond-scala").mkdir(parents=True)

    def teardown_method(self):
        """Tear down test fixtures."""
        import enforce_fail_loud
        enforce_fail_loud.CONFIG_PATH = self.original_config_path
        enforce_fail_loud.RESEARCH_MD_PATH = self.original_research_path
        self.temp_dir.cleanup()

    def test_missing_config_fails(self):
        """Test that missing config.json returns False."""
        assert check_for_real_data() is False

    def test_synthetic_flag_in_config(self):
        """Test that IS_SYNTHETIC_RUN=True causes failure."""
        config_path = Path(enforce_fail_loud.CONFIG_PATH)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump({"IS_SYNTHETIC_RUN": True}, f)
        
        assert check_for_real_data() is False

    def test_mock_data_flag_in_config(self):
        """Test that IS_MOCK_DATA=True causes failure."""
        config_path = Path(enforce_fail_loud.CONFIG_PATH)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump({"IS_MOCK_DATA": True}, f)
        
        assert check_for_real_data() is False

    def test_real_data_present_succeeds(self):
        """Test that real data presence returns True."""
        config_path = Path(enforce_fail_loud.CONFIG_PATH)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump({"IS_SYNTHETIC_RUN": False}, f)
        
        # Create fake raw data file
        raw_data_path = Path(enforce_fail_loud.CONFIG_PATH).parent.parent / "raw" / "z_reward.parquet"
        raw_data_path.parent.mkdir(parents=True, exist_ok=True)
        raw_data_path.touch()
        
        assert check_for_real_data() is True

    def test_main_raises_runtime_error_when_no_data(self):
        """Test that main() raises RuntimeError when no data is found."""
        # Ensure no config and no raw data
        assert not Path(enforce_fail_loud.CONFIG_PATH).exists()
        
        with pytest.raises(RuntimeError) as exc_info:
            main()
        
        assert "No real data found" in str(exc_info.value)
        assert "FR-006" in str(exc_info.value)
        assert "Constitution Principle VII" in str(exc_info.value)

    def test_main_returns_zero_when_data_exists(self):
        """Test that main() returns 0 when data exists."""
        config_path = Path(enforce_fail_loud.CONFIG_PATH)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump({}, f)
        
        # Create fake raw data file
        raw_data_path = Path(enforce_fail_loud.CONFIG_PATH).parent.parent / "raw" / "z_reward.parquet"
        raw_data_path.parent.mkdir(parents=True, exist_ok=True)
        raw_data_path.touch()
        
        result = main()
        assert result == 0
