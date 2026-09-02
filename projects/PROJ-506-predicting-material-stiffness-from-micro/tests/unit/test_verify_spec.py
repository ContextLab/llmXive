"""
Unit tests for verify_spec.py (T004v verification logic).
"""
import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.verify_spec import verify_spec

def test_verify_spec_success():
    """Test that verify_spec returns True when spec.md contains required text."""
    # Create a temporary spec.md
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "specs" / "001-predict-stiffness-cnn" / "spec.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)

        content = """
        # Specification

        ## FR-001: Microstructure Generation Resolution
        The system must generate images with **128x128 pixels**.

        ## US-1
        ### Acceptance Scenario 1
        The output must be **128x128 pixels**.
        """
        spec_path.write_text(content)

        # Temporarily change working directory
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            result = verify_spec()
            assert result is True
        finally:
            os.chdir(old_cwd)

def test_verify_spec_missing_fr001():
    """Test that verify_spec returns False if FR-001 is missing 128x128."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "specs" / "001-predict-stiffness-cnn" / "spec.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)

        content = """
        # Specification

        ## FR-001: Microstructure Generation Resolution
        The system must generate images.

        ## US-1
        ### Acceptance Scenario 1
        The output must be **128x128 pixels**.
        """
        spec_path.write_text(content)

        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            result = verify_spec()
            assert result is False
        finally:
            os.chdir(old_cwd)

def test_verify_spec_missing_us1():
    """Test that verify_spec returns False if US-1 is missing 128x128."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "specs" / "001-predict-stiffness-cnn" / "spec.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)

        content = """
        # Specification

        ## FR-001: Microstructure Generation Resolution
        The system must generate images with **128x128 pixels**.

        ## US-1
        ### Acceptance Scenario 1
        The output must be generated.
        """
        spec_path.write_text(content)

        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            result = verify_spec()
            assert result is False
        finally:
            os.chdir(old_cwd)
