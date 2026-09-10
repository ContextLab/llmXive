import json
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code to path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing.enforce_sample_gate import enforce_sample_gate

class TestEnforceSampleGate:
    def setup_method(self):
        """Create a temporary directory for test data."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data" / "processed"
        self.data_dir.mkdir(parents=True)
        self.config_path = self.data_dir / "modeling_config.json"
        
        # Save original CWD
        self.original_cwd = Path.cwd()
        # Change to test_dir root so relative paths work
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up temporary directory and restore CWD."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_gate_passes_with_sufficient_sample(self):
        """Test that the gate passes when N >= 80 and abort_flag is False."""
        config_data = {
            "n_samples": 100,
            "max_depth": 5,
            "abort_flag": False
        }
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)

        # Should return True and not raise
        result = enforce_sample_gate()
        assert result is True

    def test_gate_fails_with_insufficient_sample(self):
        """Test that the gate raises SystemExit when abort_flag is True."""
        config_data = {
            "n_samples": 50,
            "max_depth": 3,
            "abort_flag": True
        }
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)

        with pytest.raises(SystemExit) as exc_info:
            enforce_sample_gate()
        
        assert exc_info.value.code == 1

    def test_gate_fails_with_missing_config(self):
        """Test that the gate raises SystemExit if config file is missing."""
        # Ensure the file does not exist
        if self.config_path.exists():
            self.config_path.unlink()

        with pytest.raises(SystemExit) as exc_info:
            enforce_sample_gate()
        
        assert exc_info.value.code == 1

    def test_gate_fails_with_invalid_json(self):
        """Test that the gate raises SystemExit if config is invalid JSON."""
        with open(self.config_path, 'w') as f:
            f.write("not valid json {")

        with pytest.raises(SystemExit) as exc_info:
            enforce_sample_gate()
        
        assert exc_info.value.code == 1
