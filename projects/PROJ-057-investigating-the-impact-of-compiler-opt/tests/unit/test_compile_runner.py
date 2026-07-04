"""
Unit tests for the CompileRunner.
"""
import os
import sys
import tempfile
import subprocess
from pathlib import Path
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from benchmarks.compile_runner import CompileRunner


class TestCompileRunner:
    """Test cases for CompileRunner."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel_dir = Path(tmpdir) / "kernels"
            output_dir = Path(tmpdir) / "output"
            kernel_dir.mkdir()
            output_dir.mkdir()
            yield kernel_dir, output_dir

    def test_hash_binary(self, temp_dirs):
        """Test SHA-256 hashing of a binary file."""
        kernel_dir, output_dir = temp_dirs
        runner = CompileRunner(str(kernel_dir), str(output_dir))

        # Create a dummy binary
        dummy_binary = output_dir / "test_binary"
        dummy_binary.write_bytes(b"fake binary content 12345")

        hash1 = runner._hash_binary(dummy_binary)
        hash2 = runner._hash_binary(dummy_binary)

        assert len(hash1) == 64  # SHA-256 hex length
        assert hash1 == hash2  # Deterministic

    def test_compile_dummy_source(self, temp_dirs):
        """Test compiling a simple C++ source file."""
        kernel_dir, output_dir = temp_dirs
        runner = CompileRunner(str(kernel_dir), str(output_dir))

        # Create a dummy source file
        source_file = kernel_dir / "dummy.cpp"
        source_file.write_text("""
        int main() { return 0; }
        """)

        output_path, binary_hash = runner.compile_kernel(
            source_file,
            flags=["-O2"],
            output_name="test_dummy"
        )

        assert output_path.exists()
        assert len(binary_hash) == 64
        assert output_path.name == "test_dummy"

    def test_compile_fails_on_missing_source(self, temp_dirs):
        """Test that compilation fails gracefully for missing source."""
        kernel_dir, output_dir = temp_dirs
        runner = CompileRunner(str(kernel_dir), str(output_dir))

        missing_source = kernel_dir / "nonexistent.cpp"

        with pytest.raises(FileNotFoundError):
            runner.compile_kernel(missing_source, flags=["-O2"])

    def test_run_test_compilation(self, temp_dirs):
        """Test the run_test_compilation method."""
        kernel_dir, output_dir = temp_dirs
        runner = CompileRunner(str(kernel_dir), str(output_dir))

        binary_hash = runner.run_test_compilation()

        assert len(binary_hash) == 64
        assert binary_hash != ""  # Should be a valid hash

    def test_invalid_flags_handled(self, temp_dirs):
        """Test that invalid compiler flags cause an error."""
        kernel_dir, output_dir = temp_dirs
        runner = CompileRunner(str(kernel_dir), str(output_dir))

        source_file = kernel_dir / "dummy.cpp"
        source_file.write_text("int main() { return 0; }")

        # Use a clearly invalid flag
        with pytest.raises(RuntimeError):
            runner.compile_kernel(source_file, flags=["-invalid-flag-xyz"])