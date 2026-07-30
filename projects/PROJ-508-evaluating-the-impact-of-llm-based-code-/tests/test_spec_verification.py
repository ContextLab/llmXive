import pytest
import tempfile
import os
from pathlib import Path
from spec_verification import verify_spec_content, REQUIRED_SC_009_TEXT

class TestSpecVerification:
    
    def test_verify_spec_content_missing_file(self):
        """Test that verification fails gracefully when file is missing."""
        result = verify_spec_content("/nonexistent/path/spec.md")
        assert result is False

    def test_verify_spec_content_missing_text(self):
        """Test that verification fails when required text is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("This is a spec file without the required text.")
            temp_path = f.name

        try:
            result = verify_spec_content(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)

    def test_verify_spec_content_exact_match(self):
        """Test that verification passes when exact text is present."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(f"# Spec\n\nSome content.\n{REQUIRED_SC_009_TEXT}\nMore content.")
            temp_path = f.name

        try:
            result = verify_spec_content(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_verify_spec_content_with_whitespace_variations(self):
        """Test that verification passes even if whitespace varies slightly."""
        # The function normalizes whitespace, so newlines in the middle of the sentence
        # should still match if the words are in order.
        broken_up_text = REQUIRED_SC_009_TEXT.replace(" ", "  \n  ")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(f"# Spec\n\n{broken_up_text}")
            temp_path = f.name

        try:
            result = verify_spec_content(temp_path)
            # The regex normalization handles internal whitespace, so this should pass
            assert result is True
        finally:
            os.unlink(temp_path)
