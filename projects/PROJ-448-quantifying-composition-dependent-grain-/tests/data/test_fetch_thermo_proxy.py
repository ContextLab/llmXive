"""
Tests for code/data/fetch_thermo_proxy.py

These tests verify the fetching logic and the strict validation of ternary parameters.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.fetch_thermo_proxy import (
    calculate_sha256,
    validate_ternary_parameters,
    ThermodynamicError
)

class TestCalculateSHA256:
    def test_calculate_sha256(self):
        """Test SHA256 calculation on a temporary file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_path = f.name

        try:
            checksum = calculate_sha256(Path(temp_path))
            assert len(checksum) == 64  # SHA256 hex length
            assert isinstance(checksum, str)
        finally:
            os.unlink(temp_path)

class TestValidateTernaryParameters:
    def test_validate_missing_parameters(self):
        """Test that missing ternary parameters raise an error."""
        # Create a fake TDB content missing one required system
        # Required: FE-CR-MO, FE-CR-V, FE-MO-V, FE-CR-W, FE-MO-W
        fake_content = """
        ELEMENT FE | BCC_A2 | 55.845
        ELEMENT CR | BCC_A2 | 51.996
        ELEMENT MO | BCC_A2 | 95.95
        ELEMENT V | BCC_A2 | 50.9415
        ELEMENT W | BCC_A2 | 183.84

        PARAMETER (G, FE, CR, MO, 0) ; 1.0
        PARAMETER (G, FE, CR, V, 0) ; 1.0
        PARAMETER (G, FE, MO, V, 0) ; 1.0
        PARAMETER (G, FE, CR, W, 0) ; 1.0
        # Missing FE-MO-W
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.tdb', delete=False) as f:
            f.write(fake_content)
            temp_path = f.name

        try:
            with pytest.raises(ThermodynamicError) as exc_info:
                validate_ternary_parameters(Path(temp_path))
            
            assert "Missing required ternary" in str(exc_info.value)
            assert "FE-MO-W" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_validate_all_parameters_present(self):
        """Test that validation passes when all parameters are present."""
        fake_content = """
        ELEMENT FE | BCC_A2 | 55.845
        ELEMENT CR | BCC_A2 | 51.996
        ELEMENT MO | BCC_A2 | 95.95
        ELEMENT V | BCC_A2 | 50.9415
        ELEMENT W | BCC_A2 | 183.84

        PARAMETER (G, FE, CR, MO, 0) ; 1.0
        PARAMETER (G, FE, CR, V, 0) ; 1.0
        PARAMETER (G, FE, MO, V, 0) ; 1.0
        PARAMETER (G, FE, CR, W, 0) ; 1.0
        PARAMETER (G, FE, MO, W, 0) ; 1.0
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.tdb', delete=False) as f:
            f.write(fake_content)
            temp_path = f.name

        try:
            # Should not raise
            validate_ternary_parameters(Path(temp_path))
        finally:
            os.unlink(temp_path)
