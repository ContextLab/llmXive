"""
Unit tests for generate_manifest.py
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.generate_manifest import (
    extract_document_ids,
    save_manifest,
    SEED,
    NUM_DOCUMENTS,
    DATASET_NAME,
    SPLIT_NAME
)


class TestExtractDocumentIds:
    def test_extract_ids_with_id_field(self):
        """Test extraction when 'id' field exists."""
        docs = [{"id": "doc_1"}, {"id": "doc_2"}]
        ids = extract_document_ids(docs)
        assert ids == ["doc_1", "doc_2"]

    def test_extract_ids_with_document_id_field(self):
        """Test extraction when 'document_id' field exists."""
        docs = [{"document_id": "doc_1"}, {"document_id": "doc_2"}]
        ids = extract_document_ids(docs)
        assert ids == ["doc_1", "doc_2"]

    def test_extract_ids_fallback_to_index(self):
        """Test fallback to index when no ID field exists."""
        docs = [{"text": "hello"}, {"text": "world"}]
        ids = extract_document_ids(docs)
        assert ids == ["doc_0", "doc_1"]

    def test_extract_ids_removes_duplicates(self):
        """Test that duplicate IDs are removed."""
        docs = [{"id": "doc_1"}, {"id": "doc_1"}, {"id": "doc_2"}]
        ids = extract_document_ids(docs)
        assert ids == ["doc_1", "doc_2"]
        assert len(ids) == 2


class TestSaveManifest:
    def test_save_manifest_creates_file(self):
        """Test that save_manifest creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "config" / "test_manifest.json"
            ids = ["doc_1", "doc_2"]

            save_manifest(ids, output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_save_manifest_content(self):
        """Test that the saved manifest has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "config" / "test_manifest.json"
            ids = ["doc_1", "doc_2", "doc_3"]

            save_manifest(ids, output_path)

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert data["seed"] == SEED
            assert data["num_documents"] == len(ids)
            assert data["dataset"] == DATASET_NAME
            assert data["split"] == SPLIT_NAME
            assert data["document_ids"] == ids
            assert len(data["document_ids"]) == 3


class TestGenerateManifestIntegration:
    @patch('data.generate_manifest.load_dataset')
    def test_load_ruler_validation_sample(self, mock_load_dataset):
        """Test loading a sample of documents."""
        from data.generate_manifest import load_ruler_validation_sample

        # Mock dataset
        mock_docs = [
            {"id": f"doc_{i}", "text": f"Text {i}"}
            for i in range(10)
        ]
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=10)
        mock_dataset.select = MagicMock(return_value=mock_docs)
        mock_load_dataset.return_value = mock_dataset

        result = load_ruler_validation_sample(5, 42)

        assert len(result) == 5
        assert mock_dataset.select.called
        assert mock_dataset.select.call_args[0][0] == range(5)

    @patch('data.generate_manifest.load_dataset')
    def test_load_raises_if_not_enough_docs(self, mock_load_dataset):
        """Test that an error is raised if not enough documents are available."""
        from data.generate_manifest import load_ruler_validation_sample

        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=3)
        mock_load_dataset.return_value = mock_dataset

        with pytest.raises(RuntimeError, match="has only 3 documents"):
            load_ruler_validation_sample(10, 42)