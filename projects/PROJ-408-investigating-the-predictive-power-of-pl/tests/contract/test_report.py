import pytest
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime

# Mock config for testing if real config is not initialized in test env
from unittest.mock import patch, MagicMock
from report import verify_sc003_retention, append_validation_log
from config import Config, load_config

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for test outputs."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

@pytest.fixture
def mock_config(temp_output_dir):
    """Mocks the config to point to temp directory."""
    mock_cfg = MagicMock(spec=Config)
    mock_cfg.output_dir = str(temp_output_dir)
    mock_cfg.retention_threshold_percent = 80.0
    mock_cfg.data_dir = str(temp_output_dir)
    
    with patch('report.get_config', return_value=mock_cfg):
        with patch('config.get_config', return_value=mock_cfg):
            yield mock_cfg

def test_verify_sc003_pass(mock_config, temp_output_dir):
    """Test SC-003 verification when retention is above threshold."""
    # 10 total, 9 retained = 90% (Pass > 80%)
    result = verify_sc003_retention(10, 9)
    
    assert result is True
    
    log_path = temp_output_dir / "reports" / "validation_log.txt"
    assert log_path.exists(), "Validation log file was not created."
    
    content = log_path.read_text()
    assert "SC-003" in content
    assert "PASS" in content
    assert "90.0%" in content

def test_verify_sc003_fail(mock_config, temp_output_dir):
    """Test SC-003 verification when retention is below threshold."""
    # 10 total, 5 retained = 50% (Fail < 80%)
    result = verify_sc003_retention(10, 5)
    
    assert result is False
    
    log_path = temp_output_dir / "reports" / "validation_log.txt"
    assert log_path.exists(), "Validation log file was not created."
    
    content = log_path.read_text()
    assert "SC-003" in content
    assert "FAIL" in content
    assert "50.0%" in content

def test_verify_sc003_exact_threshold(mock_config, temp_output_dir):
    """Test SC-003 verification at exact threshold."""
    # 10 total, 8 retained = 80% (Pass >= 80%)
    result = verify_sc003_retention(10, 8)
    
    assert result is True
    
    log_path = temp_output_dir / "reports" / "validation_log.txt"
    content = log_path.read_text()
    assert "80.0%" in content
    assert "PASS" in content

def test_verify_sc003_zero_total(mock_config, temp_output_dir):
    """Test SC-003 when total species is zero."""
    result = verify_sc003_retention(0, 0)
    
    assert result is False
    
    log_path = temp_output_dir / "reports" / "validation_log.txt"
    content = log_path.read_text()
    assert "0.0%" in content
    assert "FAIL" in content