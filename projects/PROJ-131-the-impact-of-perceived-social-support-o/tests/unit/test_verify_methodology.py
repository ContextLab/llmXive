"""
Unit tests for code/data/verify_methodology.py
"""
import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add the project root to the path so we can import verify_methodology
# Assuming tests are run from the project root or code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.verify_methodology import find_section_5, verify_alignment

class TestFindSection5:
    def test_section_5_found(self):
        content = """
        # Spec
        ## 1. Intro
        Content
        ## 5. Methodological Notes
        This is the revised approach.
        ## 6. Conclusion
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            result = find_section_5(path)
            assert result is not None
            assert "Methodological Notes" in result
            assert "Revised Approach" in result
        finally:
            os.unlink(path)

    def test_section_5_not_found(self):
        content = """
        # Spec
        ## 1. Intro
        ## 2. Data
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            result = find_section_5(path)
            assert result is None
        finally:
            os.unlink(path)

class TestVerifyAlignment:
    def test_aligned_with_revised_approach_no_synthetic(self):
        content = """
        ## 5. Methodological Notes
        The Revised Approach is used.
        We do not use the Synthetic Cohort.
        """
        is_aligned, issues = verify_alignment(content)
        assert is_aligned
        assert len(issues) == 0

    def test_aligned_with_revised_approach_and_rejection_context(self):
        content = """
        ## 5. Methodological Notes
        The Revised Approach is used.
        The Synthetic Cohort was excluded due to methodological invalidity.
        """
        is_aligned, issues = verify_alignment(content)
        assert is_aligned
        assert len(issues) == 0

    def test_missing_revised_approach(self):
        content = """
        ## 5. Methodological Notes
        We use the old approach.
        """
        is_aligned, issues = verify_alignment(content)
        assert not is_aligned
        assert any("Missing 'Revised Approach'" in issue for issue in issues)

    def test_synthetic_cohort_without_rejection(self):
        content = """
        ## 5. Methodological Notes
        We use the Revised Approach.
        We also construct a Synthetic Cohort to match datasets.
        """
        is_aligned, issues = verify_alignment(content)
        assert not is_aligned
        assert any("Mentions 'Synthetic Cohort' without clear rejection context" in issue for issue in issues)