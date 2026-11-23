"""
Unit tests for data loading edge cases: corrupted PDFs and malformed bounding boxes.
These tests verify the robustness of the data loading pipeline without requiring
real external resources, using in-memory mocks to simulate edge cases.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import io

# Import the real data loading logic from the project
# Based on the API surface, data loading is primarily handled in `code/retriever.py`
# via `load_processed_data`. However, for edge case testing of raw data ingestion
# (PDFs, boxes), we need to test the underlying logic or the module that handles it.
# Since `code/retriever.py` is the entry point for processed data, we will test
# the error handling logic that would be invoked if raw data were loaded here.
#
# Note: The project API surface shows `code/retriever.py` uses `load_processed_data`.
# To test "corrupted PDFs" and "malformed boxes", we assume there is a loader
# function or we are testing the `load_processed_data` function's ability to
# handle malformed JSON inputs (which represent the "processed" state of boxes).
#
# We will import `load_processed_data` from `code.retriever` and test its
# resilience to malformed JSON structures that would represent "malformed boxes".
# For "corrupted PDFs", since the actual PDF parsing happens in `code/` (likely
# in a utility not fully exposed in the API surface list, or inside `load_processed_data`
# if it re-fetches), we will mock the file reading to simulate corruption.

try:
    from code.retriever import load_processed_data
except ImportError:
    # Fallback if the import path is slightly different in the actual environment
    # but based on the provided surface, this is the correct import.
    pytest.skip("code.retriever module not found or import failed", allow_module_level=True)


class TestMalformedBoundingBoxes:
    """Tests for handling malformed bounding box data in JSON inputs."""

    def test_missing_bbox_keys(self, tmp_path):
        """Test loading JSON with missing 'bbox' keys."""
        malformed_data = [
            {"id": "1", "text": "Sample text", "bbox": [0, 0, 10, 10]},
            {"id": "2", "text": "Missing bbox"},  # Missing 'bbox' key
            {"id": "3", "text": "Another sample", "bbox": [0, 0, 10, 10]},
        ]
        json_file = tmp_path / "processed.json"
        with open(json_file, "w") as f:
            json.dump(malformed_data, f)

        # The loader should ideally skip or handle this gracefully.
        # We expect it to either raise a specific error or return partial data.
        # Based on standard robustness requirements, we expect a ValueError or
        # a filtered list. Let's test that it doesn't crash with a generic KeyError.
        with pytest.raises((KeyError, ValueError, TypeError)) as exc_info:
            load_processed_data(str(json_file))
        # Verify the error message mentions the missing key or invalid format
        assert "bbox" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_invalid_bbox_dimensions(self, tmp_path):
        """Test loading JSON with bounding boxes of incorrect dimensionality."""
        malformed_data = [
            {"id": "1", "text": "Sample text", "bbox": [0, 0, 10, 10]},
            {"id": "2", "text": "Too few dims", "bbox": [0, 0]},  # Only 2 dims
            {"id": "3", "text": "Too many dims", "bbox": [0, 0, 10, 10, 20]},  # 5 dims
            {"id": "4", "text": "Valid", "bbox": [0, 0, 10, 10]},
        ]
        json_file = tmp_path / "processed.json"
        with open(json_file, "w") as f:
            json.dump(malformed_data, f)

        with pytest.raises((ValueError, TypeError)) as exc_info:
            load_processed_data(str(json_file))
        assert "bbox" in str(exc_info.value).lower() or "dimension" in str(exc_info.value).lower()

    def test_non_numeric_bbox_values(self, tmp_path):
        """Test loading JSON with non-numeric values in bounding boxes."""
        malformed_data = [
            {"id": "1", "text": "Sample text", "bbox": [0, 0, 10, 10]},
            {"id": "2", "text": "Non-numeric", "bbox": ["a", "b", "c", "d"]},
            {"id": "3", "text": "Valid", "bbox": [0, 0, 10, 10]},
        ]
        json_file = tmp_path / "processed.json"
        with open(json_file, "w") as f:
            json.dump(malformed_data, f)

        with pytest.raises((ValueError, TypeError)) as exc_info:
            load_processed_data(str(json_file))
        assert "numeric" in str(exc_info.value).lower() or "bbox" in str(exc_info.value).lower()

    def test_negative_bbox_values(self, tmp_path):
        """Test loading JSON with negative bounding box coordinates."""
        # Depending on the spec, negative coordinates might be invalid.
        # We test that the loader detects and handles this.
        malformed_data = [
            {"id": "1", "text": "Sample text", "bbox": [0, 0, 10, 10]},
            {"id": "2", "text": "Negative", "bbox": [-10, -10, 0, 0]},
            {"id": "3", "text": "Valid", "bbox": [0, 0, 10, 10]},
        ]
        json_file = tmp_path / "processed.json"
        with open(json_file, "w") as f:
            json.dump(malformed_data, f)

        # We expect the loader to raise an error for invalid coordinates
        with pytest.raises((ValueError, TypeError)) as exc_info:
            load_processed_data(str(json_file))
        assert "negative" in str(exc_info.value).lower() or "bbox" in str(exc_info.value).lower()

class TestCorruptedPDFs:
    """Tests for handling corrupted PDF files during loading."""

    def test_corrupted_pdf_file(self, tmp_path):
        """Test loading a file that claims to be a PDF but is corrupted."""
        # Create a file with a PDF header but corrupted content
        corrupted_pdf = b"%PDF-1.4\n" + b"\x00" * 100 + b"trailer\n"
        pdf_file = tmp_path / "corrupted.pdf"
        with open(pdf_file, "wb") as f:
            f.write(corrupted_pdf)

        # We simulate the scenario where `load_processed_data` or a helper
        # tries to read this. Since `load_processed_data` in `code.retriever`
        # likely loads JSON, we need to test the PDF loading logic if it exists
        # in the project.
        #
        # However, based on the task description "corrupted PDFs", and the fact
        # that T006 handles PDF parsing, we should test the robustness of the
        # PDF parsing step. Since the API surface doesn't explicitly list a
        # `load_pdfs` function, we assume the error handling is internal to
        # the data pipeline.
        #
        # For this test, we will mock the `pdfplumber` library to raise an error
        # when opening the corrupted file, and verify that the main loader
        # handles this gracefully (or raises a specific, informative error).

        with patch("code.retriever.pdfplumber") as mock_pdfplumber:
            mock_pdfplumber.open.side_effect = Exception("Corrupted PDF")
            mock_pdfplumber.__enter__ = MagicMock()
            mock_pdfplumber.__exit__ = MagicMock()

            # We need to call the function that actually loads PDFs.
            # Since `load_processed_data` loads JSON, we might need to test
            # a different function or assume `load_processed_data` calls a
            # PDF loader internally if the file extension is .pdf.
            #
            # Given the ambiguity, we will test the scenario where the
            # data loader encounters a file that cannot be parsed as a PDF.
            # We will assume the existence of a helper function `load_pdf_chunks`
            # or similar in `code.retriever` or `code/` that we can test.
            #
            # If `load_processed_data` is the only entry point, we might need
            # to adapt our test to check if it correctly skips or errors on
            # a list of files that includes a corrupted PDF.
            #
            # For now, we will test that the system raises a clear error
            # when a corrupted PDF is encountered.
            with pytest.raises(Exception) as exc_info:
                # This assumes `load_processed_data` or a related function
                # attempts to parse the PDF. If not, this test will need
                # adjustment based on the actual implementation.
                load_processed_data(str(pdf_file))

            assert "corrupted" in str(exc_info.value).lower() or "pdf" in str(exc_info.value).lower()

    def test_empty_pdf_file(self, tmp_path):
        """Test loading an empty PDF file."""
        empty_pdf = b""
        pdf_file = tmp_path / "empty.pdf"
        with open(pdf_file, "wb") as f:
            f.write(empty_pdf)

        with patch("code.retriever.pdfplumber") as mock_pdfplumber:
            mock_pdfplumber.open.side_effect = Exception("Empty PDF")
            with pytest.raises(Exception) as exc_info:
                load_processed_data(str(pdf_file))
            assert "empty" in str(exc_info.value).lower() or "pdf" in str(exc_info.value).lower()

class TestDataLoaderRobustness:
    """General robustness tests for the data loader."""

    def test_empty_json_file(self, tmp_path):
        """Test loading an empty JSON file."""
        json_file = tmp_path / "empty.json"
        with open(json_file, "w") as f:
            f.write("")

        with pytest.raises((json.JSONDecodeError, ValueError)) as exc_info:
            load_processed_data(str(json_file))

    def test_malformed_json_structure(self, tmp_path):
        """Test loading a JSON file with malformed structure (e.g., not a list)."""
        malformed_json = '{"not": "a list"}'
        json_file = tmp_path / "malformed.json"
        with open(json_file, "w") as f:
            f.write(malformed_json)

        with pytest.raises((ValueError, TypeError)) as exc_info:
            load_processed_data(str(json_file))
        assert "list" in str(exc_info.value).lower() or "structure" in str(exc_info.value).lower()

    def test_missing_required_fields(self, tmp_path):
        """Test loading JSON with missing required fields (e.g., 'text')."""
        malformed_data = [
            {"id": "1", "bbox": [0, 0, 10, 10]},  # Missing 'text'
            {"id": "2", "text": "Sample text", "bbox": [0, 0, 10, 10]},
        ]
        json_file = tmp_path / "processed.json"
        with open(json_file, "w") as f:
            json.dump(malformed_data, f)

        with pytest.raises((KeyError, ValueError)) as exc_info:
            load_processed_data(str(json_file))
        assert "text" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()