"""
Tests for T036: Spec Verification Script
"""

import os
import tempfile
import pytest
from pathlib import Path

# Import the verification function
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from verify_spec_amendments import verify_spec_amendments

class TestSpecVerification:
    """Test suite for spec verification logic."""

    def test_missing_spec_file_raises_error(self):
        """Verify that missing spec.md raises RuntimeError."""
        with pytest.raises(RuntimeError, match="spec.md not found"):
            verify_spec_amendments("/nonexistent/path/spec.md")

    def test_missing_cxray_exclusion_raises_error(self):
        """Verify that missing ChestX-ray14 exclusion raises RuntimeError."""
        spec_content = """
        # Spec Document
        
        ## FR-004
        Native 1024x1024 ground truth used per Decision Record 002.
        
        ## SC-004
        Paired t-test or Wilcoxon signed-rank test used per Decision Record 002.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(spec_content)
            temp_path = f.name
        
        try:
            with pytest.raises(RuntimeError, match="ChestX-ray14"):
                verify_spec_amendments(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_native_gt_raises_error(self):
        """Verify that missing native ground truth reference raises RuntimeError."""
        spec_content = """
        # Spec Document
        
        ## FR-003
        ChestX-ray14 is excluded per Decision Record 001.
        
        ## SC-004
        Paired t-test or Wilcoxon signed-rank test used per Decision Record 002.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(spec_content)
            temp_path = f.name
        
        try:
            with pytest.raises(RuntimeError, match="native 1024x1024"):
                verify_spec_amendments(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_paired_test_raises_error(self):
        """Verify that missing paired test reference raises RuntimeError."""
        spec_content = """
        # Spec Document
        
        ## FR-003
        ChestX-ray14 is excluded per Decision Record 001.
        
        ## FR-004
        Native 1024x1024 ground truth used per Decision Record 002.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(spec_content)
            temp_path = f.name
        
        try:
            with pytest.raises(RuntimeError, match="paired t-test"):
                verify_spec_amendments(temp_path)
        finally:
            os.unlink(temp_path)

    def test_all_amendments_present_passes(self):
        """Verify that a spec with all amendments passes verification."""
        spec_content = """
        # ViQ Resolution Invariance Spec

        ## FR-003: Dataset Selection
        ChestX-ray14 is excluded from scope per Decision Record 001.
        Only COCO and ImageNet-1K are used.

        ## FR-004: Ground Truth Resolution
        Native 1024x1024 ground truth used per Decision Record 002.
        No upsampling of low-resolution images.

        ## SC-004: Statistical Testing
        Paired t-test or Wilcoxon signed-rank test used per Decision Record 002.
        One-sample t-test is not used.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(spec_content)
            temp_path = f.name
        
        try:
            result = verify_spec_amendments(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)