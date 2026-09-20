"""
Unit tests for T026b: F-Test Verification
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from code.f_test_verifier import verify_f_test_results


def test_verify_valid_p_values():
    """Test verification with valid p-values."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        data = {
            "lmm": {
                "f_test_p_values": [0.05, 0.23, 0.99]
            }
        }
        with open(tmp.name, 'w') as f:
            json.dump(data, f)
        
        is_valid, messages = verify_f_test_results(Path(tmp.name))
        assert is_valid is True
        assert any("passed" in msg for msg in messages)
        os.unlink(tmp.name)


def test_verify_invalid_p_values():
    """Test verification with p-values outside [0, 1]."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        data = {
            "lmm": {
                "f_test_p_values": [0.05, 1.5, 0.99]
            }
        }
        with open(tmp.name, 'w') as f:
            json.dump(data, f)
        
        is_valid, messages = verify_f_test_results(Path(tmp.name))
        assert is_valid is False
        assert any("failed" in msg for msg in messages)
        os.unlink(tmp.name)


def test_verify_negative_p_values():
    """Test verification with negative p-values."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        data = {
            "lmm": {
                "f_test_p_values": [-0.1, 0.2]
            }
        }
        with open(tmp.name, 'w') as f:
            json.dump(data, f)
        
        is_valid, messages = verify_f_test_results(Path(tmp.name))
        assert is_valid is False
        os.unlink(tmp.name)


def test_verify_nested_f_tests_structure():
    """Test verification when p-values are in a nested f_tests dict."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        data = {
            "lmm": {
                "f_tests": {
                    "phosphorus": 0.03,
                    "nitrogen": 0.12
                }
            }
        }
        with open(tmp.name, 'w') as f:
            json.dump(data, f)
        
        is_valid, messages = verify_f_test_results(Path(tmp.name))
        assert is_valid is True
        os.unlink(tmp.name)


def test_verify_invalid_nested_f_tests():
    """Test verification with invalid p-values in nested f_tests."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        data = {
            "lmm": {
                "f_tests": {
                    "phosphorus": 0.03,
                    "nitrogen": 1.5
                }
            }
        }
        with open(tmp.name, 'w') as f:
            json.dump(data, f)
        
        is_valid, messages = verify_f_test_results(Path(tmp.name))
        assert is_valid is False
        os.unlink(tmp.name)