"""
Unit tests for T015: Persona-Chat download functionality.
"""
import pytest
from pathlib import Path
import sys
import json
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.data_integrity import compute_file_checksum, generate_manifest
from code.utils.schema_validator import load_schema


class TestPersonaChatDownload:
    """Tests for the Persona-Chat download module."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    def test_compute_file_checksum(self, temp_dir):
        """Test file checksum computation."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = compute_file_checksum(test_file)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length

    def test_generate_manifest(self, temp_dir):
        """Test manifest generation."""
        # Create test files
        (temp_dir / "file1.txt").write_text("Content 1")
        (temp_dir / "file2.txt").write_text("Content 2")
        
        manifest = generate_manifest(temp_dir)
        
        assert "files" in manifest
        assert manifest["total_files"] == 2
        assert manifest["total_size_bytes"] > 0
        
        for file_info in manifest["files"]:
            assert "path" in file_info
            assert "checksum" in file_info
            assert "size_bytes" in file_info

    def test_schema_validation(self):
        """Test that dataset schema can be loaded."""
        schema_path = project_root / "contracts" / "dataset.schema.yaml"
        if schema_path.exists():
            schema = load_schema(schema_path)
            assert schema is not None
            assert "Dialogue" in schema or "Dataset" in schema
        else:
            pytest.skip("Schema file not found - skipping validation test")

    def test_required_fields_constant(self):
        """Test that required fields are defined."""
        # Import the module to check constants
        from code import download_persona_chat
        
        assert hasattr(download_persona_chat, "REQUIRED_FIELDS")
        assert "quality_rating" in download_persona_chat.REQUIRED_FIELDS
        assert "user_id" in download_persona_chat.REQUIRED_FIELDS
        assert "dialogue_id" in download_persona_chat.REQUIRED_FIELDS

    def test_dataset_id_constant(self):
        """Test that dataset ID is correctly defined."""
        from code import download_persona_chat
        
        assert hasattr(download_persona_chat, "DATASET_ID")
        assert download_persona_chat.DATASET_ID == "cardinal/canonical-persona-chat"