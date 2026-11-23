import os
import tempfile
import zipfile
from pathlib import Path
import pytest

# Import the function to test
# Assuming the file is in code/ and we are running from project root
# The import path might need adjustment based on how tests are invoked
try:
    from code.archive_artifacts import create_archive
except ImportError:
    # Fallback for direct execution in some test runners
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from code.archive_artifacts import create_archive


class TestArchiveArtifacts:
    """Tests for the archive_artifacts module (T044)."""

    def test_create_archive_validates_missing_dirs(self):
        """Test that create_archive raises FileNotFoundError for missing directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            # Create one dir, but ask for two
            (base / "exists").mkdir()
            
            with pytest.raises(FileNotFoundError):
                create_archive(
                    source_dirs=["exists", "missing"],
                    output_filename="test.zip",
                    base_dir=base
                )

    def test_create_archive_creates_valid_zip(self):
        """Test that create_archive produces a valid zip file with correct contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create dummy directory structure
            dir1 = base / "data" / "processed"
            dir1.mkdir(parents=True)
            (dir1 / "data.csv").write_text("col1,col2\n1,2")
            
            dir2 = base / "outputs"
            dir2.mkdir()
            (dir2 / "results.json").write_text('{"key": "value"}')
            
            dir3 = base / "code"
            dir3.mkdir()
            (dir3 / "script.py").write_text("print('hello')")
            
            # Run the archive function
            archive_path = create_archive(
                source_dirs=["data/processed", "outputs", "code"],
                output_filename="test_archive.zip",
                base_dir=base
            )
            
            # Verify the file exists
            assert Path(archive_path).exists()
            assert archive_path.endswith(".zip")
            
            # Verify contents
            with zipfile.ZipFile(archive_path, 'r') as zf:
                names = zf.namelist()
                assert any("data/processed/data.csv" in n for n in names)
                assert any("outputs/results.json" in n for n in names)
                assert any("code/script.py" in n for n in names)

    def test_create_archive_empty_source_list(self):
        """Test that create_archive raises ValueError for empty source list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                create_archive(
                    source_dirs=[],
                    output_filename="test.zip",
                    base_dir=Path(tmpdir)
                )