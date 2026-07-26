import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
# Assuming tests are run from project root or this is added dynamically
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.preprocess import process_file, ProcessResult, CodeQLRunner, TreeSitterRunner


class TestPreprocessSkipsUnparseableFiles:
    """Tests for T013: test_preprocess_skips_unparseable_files"""

    def test_preprocess_skips_unparseable_files(self):
        """
        Verify that the preprocessing logic gracefully skips files that cannot be parsed
        by TreeSitter or CodeQL, logs the error, and returns a result indicating failure/skip.
        """
        # Create a temporary directory with a malformed Python file
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = Path(tmpdir) / "malformed.py"
            # Write invalid Python syntax that TreeSitter might struggle with or CodeQL might reject
            bad_content = "def broken(\n  # Missing closing paren and syntax error\n  x = 1\n"
            bad_file.write_text(bad_content)

            # Initialize runners
            # Note: In a real CI environment, codeql binary must be present.
            # For this unit test, we mock the external dependency behavior or rely on the
            # exception handling within the runner to catch the missing binary/syntax error.
            # We focus on the logic flow: exception -> log -> return skipped result.

            ts_runner = TreeSitterRunner()
            ql_runner = CodeQLRunner()

            # Act: Attempt to process the malformed file
            result = process_file(
                file_path=bad_file,
                language="python",
                ts_runner=ts_runner,
                ql_runner=ql_runner
            )

            # Assert: The result should indicate the file was not successfully processed
            # or the metrics are None/default, and the status should reflect the skip.
            assert result is not None
            assert result.status == "skipped" or result.status == "failed"
            assert result.metrics is None
            assert result.error_msg is not None
            assert "parse" in result.error_msg.lower() or "syntax" in result.error_msg.lower()


    def test_preprocess_handles_binary_file(self):
        """
        Verify that binary files (non-text) are skipped gracefully.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            binary_file = Path(tmpdir) / "binary.dat"
            # Write binary garbage
            binary_file.write_bytes(b'\x00\x01\x02\xff\xfe')

            ts_runner = TreeSitterRunner()
            ql_runner = CodeQLRunner()

            result = process_file(
                file_path=binary_file,
                language="python",
                ts_runner=ts_runner,
                ql_runner=ql_runner
            )

            assert result is not None
            assert result.status in ["skipped", "failed"]
            assert result.metrics is None


class TestPreprocessHandlesSyntaxErrors:
    """Tests for T013: test_preprocess_handles_syntax_errors"""

    def test_preprocess_handles_syntax_errors_gracefully(self):
        """
        Verify that files with specific Python syntax errors (e.g., invalid indentation,
        unexpected tokens) are caught, logged, and result in a skipped status without
        crashing the entire pipeline.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Case 1: IndentationError
            indent_file = Path(tmpdir) / "indent_error.py"
            indent_file.write_text("def foo():\nprint('bad indent')\n")

            ts_runner = TreeSitterRunner()
            ql_runner = CodeQLRunner()

            result = process_file(
                file_path=indent_file,
                language="python",
                ts_runner=ts_runner,
                ql_runner=ql_runner
            )

            # Should not crash, should report failure/skip
            assert result is not None
            assert result.status in ["skipped", "failed"]
            assert result.metrics is None

            # Case 2: Unexpected EOF
            eof_file = Path(tmpdir) / "eof_error.py"
            eof_file.write_text("x = 1\nif True:\n") # Missing block

            result = process_file(
                file_path=eof_file,
                language="python",
                ts_runner=ts_runner,
                ql_runner=ql_runner
            )

            assert result is not None
            assert result.status in ["skipped", "failed"]
            assert result.metrics is None


    def test_preprocess_successful_on_valid_file(self):
        """
        Sanity check: Ensure valid files are NOT skipped and produce metrics.
        This ensures the error handling doesn't accidentally skip everything.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_file = Path(tmpdir) / "valid.py"
            valid_file.write_text("def foo():\n    x = 1\n    return x\n")

            ts_runner = TreeSitterRunner()
            ql_runner = CodeQLRunner()

            result = process_file(
                file_path=valid_file,
                language="python",
                ts_runner=ts_runner,
                ql_runner=ql_runner
            )

            # Should succeed
            assert result is not None
            assert result.status == "success"
            assert result.metrics is not None
            assert result.metrics.get("cyclomatic_complexity") is not None
            assert result.error_msg is None