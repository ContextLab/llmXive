"""
Tests for the security audit module.
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock
import subprocess

from utils.security_audit import (
    run_bandit_check,
    run_safety_check,
    manual_code_review,
    check_file_permissions,
    generate_report,
    main
)

def test_run_bandit_check_structure():
    """Test that run_bandit_check returns a valid structure."""
    # Mock subprocess to avoid actually running bandit
    with patch('utils.security_audit.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"results": []}',
            stderr=""
        )
        result = run_bandit_check()
        assert "status" in result
        assert "tool" in result
        assert result["tool"] == "bandit"
        assert result["status"] == "passed"

def test_run_safety_check_structure():
    """Test that run_safety_check returns a valid structure."""
    with patch('utils.security_audit.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[]',
            stderr=""
        )
        result = run_safety_check()
        assert "status" in result
        assert "tool" in result
        assert result["tool"] == "safety"
        assert result["status"] == "passed"

def test_manual_code_review_no_issues():
    """Test manual review on a clean file."""
    # Create a temporary clean file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='code') as f:
        f.write("def clean_function():\n    return 42\n")
        temp_path = f.name

    try:
        # Patch os.walk to return only our temp file
        with patch('utils.security_audit.os.walk') as mock_walk:
            mock_walk.return_value = [
                ('code', [], [os.path.basename(temp_path)])
            ]
            result = manual_code_review()
            assert "status" in result
            assert result["status"] in ["passed", "warning"] # Warning if dir not found logic triggers
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_generate_report_aggregation():
    """Test that generate_report aggregates results correctly."""
    bandit = {"status": "passed", "tool": "bandit", "findings": [], "message": "OK"}
    safety = {"status": "passed", "tool": "safety", "findings": [], "message": "OK"}
    manual = {"status": "passed", "tool": "manual_review", "findings": [], "message": "OK"}
    perm = {"status": "passed", "tool": "file_permissions", "findings": [], "message": "OK"}

    report = generate_report(bandit, safety, manual, perm)
    assert report["overall_status"] == "passed"
    assert report["total_critical_issues"] == 0
    assert "tool_results" in report

def test_main_execution():
    """Test that main executes and produces a report file."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Mock all subprocess calls to succeed
        with patch('utils.security_audit.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"results": []}',
                stderr=""
            )
            with patch('utils.security_audit.os.path.exists') as mock_exists:
                # Ensure directories exist check passes
                mock_exists.return_value = True

                # Mock manual review to return passed
                with patch('utils.security_audit.manual_code_review') as mock_manual:
                    mock_manual.return_value = {"status": "passed", "findings": [], "tool": "manual_review"}
                    
                    # Mock check_file_permissions
                    with patch('utils.security_audit.check_file_permissions') as mock_perm:
                        mock_perm.return_value = {"status": "passed", "findings": [], "tool": "file_permissions"}
                        
                        # Run main
                        with patch('sys.argv', ['security_audit.py', '--output', tmp_path]):
                            try:
                                main()
                            except SystemExit:
                                pass # Expected at end of main
                            
                            assert os.path.exists(tmp_path)
                            with open(tmp_path, 'r') as f:
                                data = json.load(f)
                                assert "overall_status" in data
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)