"""
Test for Task T011d: Local Pilot Deployment
Verifies that the deployment script generates a valid local URL and deployment info.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.experiment.deploy import (
    ensure_streamlit_config,
    build_deployment_info,
    write_deployment_info,
    parse_arguments,
    main
)


class TestLocalDeployment:
    """Tests for the deployment functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_app_script(self, temp_dir):
        """Create a mock Streamlit app script."""
        app_script = temp_dir / "pilot_interface.py"
        app_script.write_text("# Mock Streamlit app\n")
        return app_script

    def test_ensure_streamlit_config_creates_file(self, temp_dir):
        """Test that ensure_streamlit_config creates config.toml if missing."""
        config_dir = temp_dir / ".streamlit"
        config_file = config_dir / "config.toml"
        
        assert not config_file.exists()
        
        ensure_streamlit_config(config_dir)
        
        assert config_file.exists()
        content = config_file.read_text()
        assert "[server]" in content
        assert "headless = true" in content
        assert "127.0.0.1" in content

    def test_ensure_streamlit_config_uses_existing(self, temp_dir):
        """Test that ensure_streamlit_config doesn't overwrite existing config."""
        config_dir = temp_dir / ".streamlit"
        config_file = config_dir / "config.toml"
        
        config_dir.mkdir(parents=True, exist_ok=True)
        original_content = "# Existing config\n[server]\nport = 9999"
        config_file.write_text(original_content)
        
        ensure_streamlit_config(config_dir)
        
        assert config_file.read_text() == original_content

    def test_build_deployment_info(self, mock_app_script):
        """Test that build_deployment_info returns correct structure."""
        port = 8501
        cohort_size = 20
        
        info = build_deployment_info(mock_app_script, port, cohort_size)
        
        assert "deployment_id" in info
        assert "app_script" in info
        assert "access_url" in info
        assert info["access_url"] == f"http://127.0.0.1:{port}"
        assert info["port"] == port
        assert info["cohort_size"] == cohort_size
        assert "timestamp" in info
        assert info["status"] == "ready"
        assert "instructions" in info

    def test_write_deployment_info(self, temp_dir, mock_app_script):
        """Test that write_deployment_info creates valid JSON file."""
        output_path = temp_dir / "deployment_info.json"
        info = build_deployment_info(mock_app_script, 8501, 20)
        
        write_deployment_info(info, output_path)
        
        assert output_path.exists()
        
        with open(output_path) as f:
            loaded_info = json.load(f)
        
        assert loaded_info == info

    def test_local_deployment_url_generated(self, temp_dir, mock_app_script):
        """
        Verification test for T011d:
        Assert that a local deployment URL is generated and accessible in the output.
        """
        output_path = temp_dir / "deployment_info.json"
        port = 8501
        cohort_size = 20
        
        # Build deployment info
        info = build_deployment_info(mock_app_script, port, cohort_size)
        
        # Verify URL is generated
        expected_url = f"http://127.0.0.1:{port}"
        assert info["access_url"] == expected_url, \
            f"Expected URL {expected_url}, got {info['access_url']}"
        
        # Write and verify
        write_deployment_info(info, output_path)
        assert output_path.exists()
        
        with open(output_path) as f:
            saved_info = json.load(f)
        
        assert saved_info["access_url"] == expected_url
        assert saved_info["status"] == "ready"
        assert saved_info["cohort_size"] == cohort_size

    def test_parse_arguments_default_values(self):
        """Test that parse_arguments returns correct defaults."""
        with patch('sys.argv', ['deploy.py']):
            args = parse_arguments()
        
        assert args.port == 8501
        assert args.cohort_size == 20
        assert args.start_server is False
        assert args.background is False
        assert args.output == Path("data/derived/deployment_info.json")

    def test_main_returns_success_when_app_exists(self, temp_dir, mock_app_script, capsys):
        """Test that main returns 0 when app script exists."""
        output_path = temp_dir / "deployment_info.json"
        
        # Mock the write_deployment_info to avoid file system writes in test
        with patch('src.experiment.deploy.write_deployment_info'):
            with patch('sys.argv', [
                'deploy.py',
                '--app-script', str(mock_app_script),
                '--output', str(output_path),
                '--port', '8501'
            ]):
                result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "DEPLOYMENT READY" in captured.out

    def test_main_returns_error_when_app_missing(self, temp_dir, capsys):
        """Test that main returns 1 when app script doesn't exist."""
        missing_app = temp_dir / "nonexistent.py"
        output_path = temp_dir / "deployment_info.json"
        
        with patch('sys.argv', [
            'deploy.py',
            '--app-script', str(missing_app),
            '--output', str(output_path)
        ]):
            result = main()
        
        assert result == 1
        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "not found" in captured.out.lower()

# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])