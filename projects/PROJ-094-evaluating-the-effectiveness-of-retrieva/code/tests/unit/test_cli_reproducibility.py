"""
Unit tests for T014: Deterministic seed enforcement and reproducibility checks.
"""
import os
import sys
import random
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cli.main import set_deterministic_environment, verify_reproducibility_state
from src.lib.utils import set_fixed_seed

class TestDeterministicSeedEnforcement:
    
    def test_set_deterministic_environment_sets_python_seed(self):
        """Test that Python's random seed is set correctly."""
        set_deterministic_environment(42)
        val1 = random.random()
        set_deterministic_environment(42)
        val2 = random.random()
        assert val1 == val2, "Python random seed not enforced correctly"

    def test_set_deterministic_environment_sets_env_var(self):
        """Test that PYTHONHASHSEED environment variable is set."""
        set_deterministic_environment(42)
        assert os.environ.get('PYTHONHASHSEED') == '42'

    @patch('src.cli.main.np')
    def test_set_deterministic_environment_sets_numpy_seed(self, mock_np):
        """Test that NumPy seed is set if available."""
        # Mock numpy to exist
        mock_np.random.seed = MagicMock()
        set_deterministic_environment(42)
        mock_np.random.seed.assert_called_once_with(42)

    @patch('src.cli.main.torch')
    def test_set_deterministic_environment_sets_torch_seed(self, mock_torch):
        """Test that Torch seed is set if available."""
        mock_torch.manual_seed = MagicMock()
        mock_torch.cuda.is_available = MagicMock(return_value=False)
        
        set_deterministic_environment(42)
        
        mock_torch.manual_seed.assert_called_once_with(42)

    @patch('src.cli.main.torch')
    def test_set_deterministic_environment_sets_torch_cuda_deterministic(self, mock_torch):
        """Test that Torch CUDA deterministic flags are set."""
        mock_torch.manual_seed = MagicMock()
        mock_torch.cuda.is_available = MagicMock(return_value=True)
        mock_torch.cuda.manual_seed = MagicMock()
        mock_torch.cuda.manual_seed_all = MagicMock()
        
        set_deterministic_environment(42)
        
        assert mock_torch.backends.cudnn.deterministic == True
        assert mock_torch.backends.cudnn.benchmark == False

class TestReproducibilityChecks:
    
    def test_verify_reproducibility_state_no_state_file(self, caplog):
        """Test verification when no state file exists."""
        # Ensure no state file
        state_path = project_root / "data" / ".state.json"
        if state_path.exists():
            state_path.unlink()
        
        # Should not raise, just log info
        verify_reproducibility_state()
        assert "Verifying data integrity" in caplog.text or "No state file" in caplog.text

    @patch('src.cli.main.verify_all')
    def test_verify_reproducibility_state_success(self, mock_verify_all, caplog):
        """Test verification when state check passes."""
        mock_verify_all.return_value = True
        # Create a dummy state file
        state_path = project_root / "data" / ".state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.touch()
        
        verify_reproducibility_state()
        mock_verify_all.assert_called_once()
        assert "Data integrity verified" in caplog.text or "integrity" in caplog.text

    @patch('src.cli.main.verify_all')
    def test_verify_reproducibility_state_failure(self, mock_verify_all, caplog):
        """Test verification when state check fails."""
        mock_verify_all.side_effect = Exception("Checksum mismatch")
        # Create a dummy state file
        state_path = project_root / "data" / ".state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.touch()
        
        # Should log warning but not crash
        verify_reproducibility_state()
        assert "Data integrity check failed" in caplog.text or "warning" in caplog.text.lower()