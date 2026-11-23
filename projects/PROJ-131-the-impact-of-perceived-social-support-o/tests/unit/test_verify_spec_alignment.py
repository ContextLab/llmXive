import pytest
from pathlib import Path
import tempfile
import os
from code.data.verify_spec_alignment import verify_spec_alignment

class TestVerifySpecAlignment:
    def test_spec_aligned(self):
        """Test with a spec that has FR-001/FR-002 removed, SC-001 revised, and Synthetic Cohort rejected."""
        spec_content = """
        # Spec

        ## FR-001: Dual-Dataset Matching (REMOVED)
        This feature has been removed.

        ## FR-002: Synthetic Cohort Generation (DEPRECATED)
        This feature is deprecated.

        ## SC-001: Data Source (REVISED)
        This scale has been revised.

        ## Rejection of Dual-Dataset Matching
        The Synthetic Cohort approach is rejected as methodologically invalid.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(spec_content)
            temp_path = f.name

        try:
            result = verify_spec_alignment(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_spec_missing_fr1(self):
        """Test with a spec missing FR-001 entirely."""
        spec_content = """
        # Spec

        ## FR-002: Synthetic Cohort Generation (DEPRECATED)
        This feature is deprecated.

        ## SC-001: Data Source (REVISED)
        This scale has been revised.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(spec_content)
            temp_path = f.name

        try:
            result = verify_spec_alignment(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)

    def test_spec_active_synthetic_cohort(self):
        """Test with a spec that proposes Synthetic Cohort as a valid step."""
        spec_content = """
        # Spec

        ## FR-001: Dual-Dataset Matching (REMOVED)
        This feature has been removed.

        ## FR-002: Synthetic Cohort Generation (DEPRECATED)
        This feature is deprecated.

        ## SC-001: Data Source (REVISED)
        This scale has been revised.

        ## Proposed Approach
        We will implement the Synthetic Cohort method to improve accuracy.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(spec_content)
            temp_path = f.name

        try:
            result = verify_spec_alignment(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)

    def test_spec_missing_sc1_revised(self):
        """Test with a spec missing REVISED for SC-001."""
        spec_content = """
        # Spec

        ## FR-001: Dual-Dataset Matching (REMOVED)
        This feature has been removed.

        ## FR-002: Synthetic Cohort Generation (DEPRECATED)
        This feature is deprecated.

        ## SC-001: Data Source
        This scale is unchanged.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(spec_content)
            temp_path = f.name

        try:
            result = verify_spec_alignment(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)
