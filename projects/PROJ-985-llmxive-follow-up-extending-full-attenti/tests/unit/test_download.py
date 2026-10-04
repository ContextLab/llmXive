"""
Unit tests for the RULER dataset downloader (T011).

Tests:
1. Manifest loading with valid and invalid inputs
2. Streaming dataset filtering logic (mocked)
3. Output file generation and verification
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from code.data.download import load_manifest, download_ruler_dataset, get_project_root


class TestLoadManifest:
    """Tests for the load_manifest function."""

    def test_load_manifest_valid_list(self, tmp_path):
        """Test loading a valid manifest with a list of IDs."""
        manifest_data = ["doc_1", "doc_2", "doc_3"]
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))

        result = load_manifest(manifest_path)
        assert result == {"doc_1", "doc_2", "doc_3"}
        assert len(result) == 3

    def test_load_manifest_valid_dict(self, tmp_path):
        """Test loading a valid manifest with a dict containing 'document_ids'."""
        manifest_data = {"document_ids": ["doc_1", "doc_2"]}
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))

        result = load_manifest(manifest_path)
        assert result == {"doc_1", "doc_2"}

    def test_load_manifest_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised when manifest is missing."""
        missing_path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError, match="Manifest file not found"):
            load_manifest(missing_path)

    def test_load_manifest_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        manifest_path = tmp_path / "invalid.json"
        manifest_path.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            load_manifest(manifest_path)

    def test_load_manifest_invalid_format(self, tmp_path):
        """Test that ValueError is raised for unexpected manifest structure."""
        manifest_path = tmp_path / "invalid_format.json"
        manifest_path.write_text(json.dumps({"unexpected_key": [1, 2, 3]}))

        with pytest.raises(ValueError, match="Invalid manifest format"):
            load_manifest(manifest_path)


class TestDownloadRulerDataset:
    """Tests for the download_ruler_dataset function."""

    @patch('code.data.download.load_dataset')
    def test_download_filters_correctly(self, mock_load_dataset, tmp_path):
        """Test that the function correctly filters documents by manifest IDs."""
        # Setup mock dataset
        mock_item_1 = {"id": "doc_1", "content": "text 1"}
        mock_item_2 = {"id": "doc_2", "content": "text 2"}
        mock_item_3 = {"id": "doc_3", "content": "text 3"}
        mock_item_4 = {"id": "doc_4", "content": "text 4"}

        # Iterator that yields all items
        def mock_iter():
            for item in [mock_item_1, mock_item_2, mock_item_3, mock_item_4]:
                yield item

        mock_load_dataset.return_value = mock_iter()

        manifest_ids = {"doc_1", "doc_3"}
        output_path = tmp_path / "output.jsonl"

        count = download_ruler_dataset(manifest_ids, output_path)

        assert count == 2
        assert output_path.exists()

        # Verify content
        with open(output_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            doc_ids = [json.loads(line)["id"] for line in lines]
            assert "doc_1" in doc_ids
            assert "doc_3" in doc_ids
            assert "doc_2" not in doc_ids
            assert "doc_4" not in doc_ids

    @patch('code.data.download.load_dataset')
    def test_download_no_matches_raises_error(self, mock_load_dataset, tmp_path):
        """Test that RuntimeError is raised if no documents match."""
        mock_item = {"id": "doc_999", "content": "text"}
        
        def mock_iter():
            yield mock_item

        mock_load_dataset.return_value = mock_iter()

        manifest_ids = {"doc_1", "doc_2"}
        output_path = tmp_path / "output.jsonl"

        with pytest.raises(RuntimeError, match="No documents found matching"):
            download_ruler_dataset(manifest_ids, output_path)

    @patch('code.data.download.load_dataset')
    def test_download_handles_missing_id_field(self, mock_load_dataset, tmp_path):
        """Test that items without ID fields are skipped."""
        mock_item_1 = {"id": "doc_1", "content": "text 1"}
        mock_item_2 = {"content": "no id here"}  # Missing ID
        mock_item_3 = {"id": "doc_2", "content": "text 2"}

        def mock_iter():
            for item in [mock_item_1, mock_item_2, mock_item_3]:
                yield item

        mock_load_dataset.return_value = mock_iter()

        manifest_ids = {"doc_1", "doc_2"}
        output_path = tmp_path / "output.jsonl"

        count = download_ruler_dataset(manifest_ids, output_path)

        assert count == 2
        assert output_path.exists()

    @patch('code.data.download.load_dataset')
    def test_download_handles_dataset_load_failure(self, mock_load_dataset, tmp_path):
        """Test that ConnectionError is raised if dataset loading fails."""
        mock_load_dataset.side_effect = Exception("Network error")

        manifest_ids = {"doc_1"}
        output_path = tmp_path / "output.jsonl"

        with pytest.raises(ConnectionError, match="Failed to load dataset"):
            download_ruler_dataset(manifest_ids, output_path)

    def test_download_creates_output_directory(self, tmp_path):
        """Test that the function creates the output directory if it doesn't exist."""
        # Mock the dataset loading to avoid actual network calls
        with patch('code.data.download.load_dataset') as mock_load:
            mock_item = {"id": "doc_1", "content": "text"}
            mock_load.return_value = iter([mock_item])

            # Create a nested path that doesn't exist
            deep_path = tmp_path / "deep" / "nested" / "output.jsonl"

            manifest_ids = {"doc_1"}
            count = download_ruler_dataset(manifest_ids, deep_path)

            assert count == 1
            assert deep_path.exists()


class TestIntegration:
    """Integration tests for the full download pipeline."""

    def test_end_to_end_with_mocked_dataset(self, tmp_path):
        """Test the full flow from manifest to output file."""
        # Create manifest
        manifest_path = tmp_path / "manifest.json"
        manifest_ids = ["doc_1", "doc_2", "doc_3"]
        manifest_path.write_text(json.dumps(manifest_ids))

        # Mock dataset
        all_docs = [
            {"id": "doc_1", "text": "First doc"},
            {"id": "doc_2", "text": "Second doc"},
            {"id": "doc_3", "text": "Third doc"},
            {"id": "doc_4", "text": "Fourth doc (not in manifest)"},
        ]

        with patch('code.data.download.load_dataset') as mock_load:
            mock_load.return_value = iter(all_docs)

            output_path = tmp_path / "downloaded.jsonl"
            count = download_ruler_dataset(set(manifest_ids), output_path)

            assert count == 3
            assert output_path.exists()

            with open(output_path, 'r') as f:
                lines = f.readlines()
                ids = [json.loads(line)["id"] for line in lines]
                assert set(ids) == set(manifest_ids)