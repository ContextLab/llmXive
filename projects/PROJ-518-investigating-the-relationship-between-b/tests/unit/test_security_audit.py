import subprocess
import sys
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
import tempfile
import os

# Import the functions to test
from scripts.security_audit import run_safety_check, update_vulnerable_packages, main

class TestSecurityAudit:
    def test_run_safety_check_missing_requirements(self, tmp_path):
        """Test that run_safety_check returns False if requirements.txt is missing."""
        # Create a temp directory without requirements.txt
        with patch('pathlib.Path.exists', return_value=False):
            result = run_safety_check()
            assert result is False

    def test_run_safety_check_success(self, tmp_path, caplog):
        """Test successful safety check (no vulnerabilities)."""
        # Create a mock requirements.txt
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("numpy==1.26.4\n")
        
        # Mock subprocess.run to simulate a clean safety check
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "No vulnerabilities found."
        mock_result.stderr = ""
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('subprocess.run', return_value=mock_result):
            
            result = run_safety_check()
            assert result is True

    def test_run_safety_check_vulnerabilities(self, tmp_path, caplog):
        """Test safety check when vulnerabilities are found."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("numpy==1.26.4\n")
        
        # Mock subprocess.run to simulate vulnerabilities found
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Critical vulnerability found in package X."
        mock_result.stderr = ""
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('subprocess.run', return_value=mock_result):
            
            result = run_safety_check()
            assert result is False

    def test_update_vulnerable_packages_success(self, tmp_path):
        """Test successful package update."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("numpy==1.26.4\n")
        
        # Mock pip upgrade success
        upgrade_mock = MagicMock()
        upgrade_mock.returncode = 0
        upgrade_mock.stderr = ""
        
        # Mock safety check success after update
        safety_mock = MagicMock()
        safety_mock.returncode = 0
        safety_mock.stdout = "No vulnerabilities."
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('subprocess.run', side_effect=[upgrade_mock, safety_mock]):
            
            result = update_vulnerable_packages()
            assert result is True

    def test_main_exits_clean_on_success(self, tmp_path, caplog):
        """Test main() exits with code 0 on success."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("numpy==1.26.4\n")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "No vulnerabilities."
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('subprocess.run', return_value=mock_result), \
             patch('sys.exit') as mock_exit:
            
            main()
            mock_exit.assert_called_with(0)

    def test_main_exits_error_on_failure(self, tmp_path, caplog):
        """Test main() exits with code 1 on failure."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("numpy==1.26.4\n")
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Vulnerabilities found."
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('subprocess.run', return_value=mock_result), \
             patch('sys.exit') as mock_exit:
            
            main()
            mock_exit.assert_called_with(1)
