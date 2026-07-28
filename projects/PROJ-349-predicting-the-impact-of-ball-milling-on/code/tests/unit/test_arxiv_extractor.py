"""
Unit tests for arXiv PDF extractor.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Ensure we can import from the project
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingest.arxiv_extractor import (
    _search_arxiv_papers,
    _download_pdf,
    _extract_text_from_pdf,
    _parse_tables_from_text,
    _extract_psd_from_arxiv_paper,
    run_arxiv_ingestion,
    extract_psd_from_arxiv,
    D_VALUE_PATTERN
)

@pytest.fixture
def mock_arxiv_result():
    """Create a mock arxiv.Result object."""
    result = MagicMock()
    result.entry_id = "http://arxiv.org/abs/2301.12345"
    result.title = "Ball Milling Effects on Particle Size"
    result.authors = ["Author A", "Author B"]
    result.published = "2023-01-01"
    return result

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestSearchArxivPapers:
    def test_search_returns_results(self):
        """Test that search returns a list of results."""
        mock_results = [MagicMock()]
        with patch('src.ingest.arxiv_extractor.arxiv.Search') as MockSearch:
            mock_search_instance = MagicMock()
            mock_search_instance.results.return_value = mock_results
            MockSearch.return_value = mock_search_instance

            results = _search_arxiv_papers("ball milling", "cond-mat.mtrl-sci", 10)

            assert len(results) == 1
            MockSearch.assert_called_once()

    def test_search_no_results_logs_warning(self, caplog):
        """Test that search with no results logs a warning."""
        with patch('src.ingest.arxiv_extractor.arxiv.Search') as MockSearch:
            mock_search_instance = MagicMock()
            mock_search_instance.results.return_value = []
            MockSearch.return_value = mock_search_instance

            results = _search_arxiv_papers("ball milling", "cond-mat.mtrl-sci", 10)

            assert len(results) == 0
            assert "no results found" in caplog.text

    def test_search_handles_exception(self, caplog):
        """Test that search handles exceptions gracefully."""
        with patch('src.ingest.arxiv_extractor.arxiv.Search') as MockSearch:
            MockSearch.side_effect = Exception("API Error")

            results = _search_arxiv_papers("ball milling", "cond-mat.mtrl-sci", 10)

            assert len(results) == 0
            assert "error" in caplog.text.lower()

class TestDownloadPdf:
    def test_download_success(self, mock_arxiv_result, temp_dir):
        """Test successful PDF download."""
        with patch('src.ingest.arxiv_extractor.arxiv.Result.download_pdf') as mock_download:
            # Create a dummy PDF file
            pdf_path = temp_dir / "2301.12345.pdf"
            pdf_path.touch()

            result = _download_pdf(mock_arxiv_result, temp_dir)

            assert result == pdf_path
            mock_download.assert_called_once()

    def test_download_failure(self, mock_arxiv_result, temp_dir):
        """Test PDF download failure."""
        with patch('src.ingest.arxiv_extractor.arxiv.Result.download_pdf') as mock_download:
            mock_download.side_effect = Exception("Download failed")

            result = _download_pdf(mock_arxiv_result, temp_dir)

            assert result is None

class TestExtractTextFromPdf:
    def test_extract_text_success(self, temp_dir):
        """Test successful text extraction."""
        # Create a dummy PDF file with some text
        pdf_path = temp_dir / "test.pdf"
        with open(pdf_path, "w") as f:
            f.write("D10: 10.5 D50: 50.2 D90: 90.1")

        with patch('src.ingest.arxiv_extractor.extract_text') as mock_extract:
            mock_extract.return_value = "D10: 10.5 D50: 50.2 D90: 90.1"

            text = _extract_text_from_pdf(pdf_path)

            assert text == "D10: 10.5 D50: 50.2 D90: 90.1"
            mock_extract.assert_called_once_with(str(pdf_path))

    def test_extract_text_failure(self, temp_dir):
        """Test text extraction failure."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()

        with patch('src.ingest.arxiv_extractor.extract_text') as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")

            text = _extract_text_from_pdf(pdf_path)

            assert text is None

class TestParseTablesFromText:
    def test_parse_d_values(self):
        """Test parsing D values from text."""
        text = "Sample: D10: 10.5, D50: 50.2, D90: 90.1"
        rows = _parse_tables_from_text(text)

        assert len(rows) == 1
        assert rows[0].get("d10") == 10.5
        assert rows[0].get("d50") == 50.2
        assert rows[0].get("d90") == 90.1

    def test_parse_no_d_values(self):
        """Test parsing text with no D values."""
        text = "This text contains no particle size data."
        rows = _parse_tables_from_text(text)

        assert len(rows) == 0

    def test_parse_multiple_rows(self):
        """Test parsing multiple rows of D values."""
        text = """
        Sample A: D10: 10.5, D50: 50.2, D90: 90.1
        Sample B: D10: 12.3, D50: 55.5, D90: 95.0
        """
        rows = _parse_tables_from_text(text)

        assert len(rows) == 2
        assert rows[0].get("d10") == 10.5
        assert rows[1].get("d10") == 12.3

class TestExtractPsdFromArxivPaper:
    def test_extract_success(self, mock_arxiv_result, temp_dir):
        """Test successful extraction from a paper."""
        # Mock download_pdf to create a dummy file
        with patch('src.ingest.arxiv_extractor._download_pdf') as mock_download:
            pdf_path = temp_dir / "2301.12345.pdf"
            pdf_path.touch()
            mock_download.return_value = pdf_path

            # Mock extract_text
            with patch('src.ingest.arxiv_extractor._extract_text_from_pdf') as mock_extract:
                mock_extract.return_value = "D10: 10.5 D50: 50.2 D90: 90.1"

                record = _extract_psd_from_arxiv_paper(mock_arxiv_result, temp_dir)

                assert record is not None
                assert record["source"] == "arXiv"
                assert record["arxiv_id"] == "2301.12345"
                assert record["data"]["d10"] == 10.5

    def test_extract_no_pdf(self, mock_arxiv_result, temp_dir):
        """Test extraction when PDF download fails."""
        with patch('src.ingest.arxiv_extractor._download_pdf') as mock_download:
            mock_download.return_value = None

            record = _extract_psd_from_arxiv_paper(mock_arxiv_result, temp_dir)

            assert record is None

    def test_extract_no_text(self, mock_arxiv_result, temp_dir):
        """Test extraction when text extraction fails."""
        with patch('src.ingest.arxiv_extractor._download_pdf') as mock_download:
            pdf_path = temp_dir / "2301.12345.pdf"
            pdf_path.touch()
            mock_download.return_value = pdf_path

            with patch('src.ingest.arxiv_extractor._extract_text_from_pdf') as mock_extract:
                mock_extract.return_value = None

                record = _extract_psd_from_arxiv_paper(mock_arxiv_result, temp_dir)

                assert record is None

class TestRunArxivIngestion:
    def test_run_ingestion(self, temp_dir, mock_arxiv_result):
        """Test the full ingestion pipeline."""
        output_file = temp_dir / "arxiv_tables.json"

        # Mock search
        with patch('src.ingest.arxiv_extractor._search_arxiv_papers') as mock_search:
            mock_search.return_value = [mock_arxiv_result]

            # Mock extraction
            with patch('src.ingest.arxiv_extractor._extract_psd_from_arxiv_paper') as mock_extract:
                mock_extract.return_value = {
                    "experiment_id": "abc123",
                    "source": "arXiv",
                    "data": {"d10": 10.5}
                }

                records = run_arxiv_ingestion(str(output_file))

                assert len(records) == 1
                assert output_file.exists()

                with open(output_file, "r") as f:
                    data = json.load(f)
                    assert len(data) == 1

    def test_run_ingestion_no_results(self, temp_dir):
        """Test ingestion when no results are found."""
        output_file = temp_dir / "arxiv_tables.json"

        with patch('src.ingest.arxiv_extractor._search_arxiv_papers') as mock_search:
            mock_search.return_value = []

            records = run_arxiv_ingestion(str(output_file))

            assert len(records) == 0
            assert output_file.exists()

            with open(output_file, "r") as f:
                data = json.load(f)
                assert data == []

class TestExtractPsdFromArxiv:
    def test_convenience_function(self):
        """Test the convenience function."""
        with patch('src.ingest.arxiv_extractor.run_arxiv_ingestion') as mock_run:
            mock_run.return_value = [{"test": "data"}]

            result = extract_psd_from_arxiv()

            assert result == [{"test": "data"}]
            mock_run.assert_called_once()
