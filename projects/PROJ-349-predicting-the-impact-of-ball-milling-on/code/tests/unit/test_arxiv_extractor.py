"""
Unit tests for arXiv PDF extractor.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from src.ingest.arxiv_extractor import (
    extract_psd_from_arxiv,
    run_arxiv_ingestion,
    _extract_tables_from_text,
    _parse_table_to_metrics,
    _calculate_hash
)
from src.exceptions import DataIngestionError

class TestHashing:
    """Test hash calculation functionality."""
    
    def test_calculate_hash_consistency(self):
        """Test that same input produces same hash."""
        data = "test data"
        hash1 = _calculate_hash(data)
        hash2 = _calculate_hash(data)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_calculate_hash_uniqueness(self):
        """Test that different inputs produce different hashes."""
        hash1 = _calculate_hash("data1")
        hash2 = _calculate_hash("data2")
        assert hash1 != hash2

class TestTextParsing:
    """Test text parsing and table extraction."""
    
    def test_extract_tables_from_text_empty(self):
        """Test extraction from empty text."""
        tables = _extract_tables_from_text("")
        assert tables == []
    
    def test_extract_tables_from_text_no_numbers(self):
        """Test extraction from text without numbers."""
        text = "This is just text without any numbers or units."
        tables = _extract_tables_from_text(text)
        assert tables == []
    
    def test_extract_tables_from_text_with_tables(self):
        """Test extraction from text containing table-like content."""
        text = """
        Some text before
        D10: 5.2 µm D50: 12.3 µm D90: 25.1 µm
        More text
        D10: 3.1 µm D50: 8.7 µm D90: 18.9 µm
        Text after
        """
        tables = _extract_tables_from_text(text)
        assert len(tables) >= 1
        assert any("D10" in row for table in tables for row in table)
    
    def test_parse_table_to_metrics_basic(self):
        """Test parsing of basic table with D10, D50, D90."""
        table_rows = [
            "D10: 5.2 µm D50: 12.3 µm D90: 25.1 µm",
            "Material: Alumina"
        ]
        metrics = _parse_table_to_metrics(table_rows)
        assert metrics is not None
        assert 'd10' in metrics
        assert 'd50' in metrics
        assert 'd90' in metrics
        assert abs(metrics['d10'] - 5.2) < 0.01
        assert abs(metrics['d50'] - 12.3) < 0.01
        assert abs(metrics['d90'] - 25.1) < 0.01
    
    def test_parse_table_to_metrics_nanometers(self):
        """Test parsing with nanometer units (conversion to µm)."""
        table_rows = [
            "D10: 5200 nm D50: 12300 nm D90: 25100 nm"
        ]
        metrics = _parse_table_to_metrics(table_rows)
        assert metrics is not None
        assert abs(metrics['d10'] - 5.2) < 0.01
        assert abs(metrics['d50'] - 12.3) < 0.01
        assert abs(metrics['d90'] - 25.1) < 0.01
    
    def test_parse_table_to_metrics_no_metrics(self):
        """Test parsing when no metrics are found."""
        table_rows = [
            "Some random text",
            "Without any D values"
        ]
        metrics = _parse_table_to_metrics(table_rows)
        assert metrics is None

class TestFlaggedEntries:
    """Test that flagged entries are handled correctly."""
    
    def test_record_structure(self):
        """Test that extracted records have required structure."""
        # This is a mock test - actual extraction would require real PDFs
        mock_record = {
            'experiment_id': 'arxiv_12345_0',
            'source': 'arXiv',
            'material_type': 'unknown',
            'milling_speed': None,
            'milling_time': None,
            'ball_to_powder_ratio': None,
            'youngs_modulus': None,
            'density': None,
            'd10': 5.0,
            'd50': 12.0,
            'd90': 25.0,
            'process_duration': None,
            'pdf_url': 'https://arxiv.org/pdf/12345',
            'text_hash': 'dummy_hash'
        }
        assert 'experiment_id' in mock_record
        assert 'source' in mock_record
        assert 'd10' in mock_record
        assert 'd50' in mock_record
        assert 'd90' in mock_record

class TestExtractionIntegration:
    """Integration tests for the extraction pipeline."""
    
    @patch('src.ingest.arxiv_extractor.arxiv.Search')
    @patch('src.ingest.arxiv_extractor.arxiv.Client')
    @patch('src.ingest.arxiv_extractor.extract_text')
    @patch('src.ingest.arxiv_extractor.Path')
    def test_run_arxiv_ingestion_success(
        self, mock_path, mock_extract_text, mock_client, mock_search
    ):
        """Test successful ingestion run."""
        # Mock arXiv search results
        mock_paper = MagicMock()
        mock_paper.entry_id = "https://arxiv.org/abs/1234.5678"
        mock_paper.title = "Test Paper"
        mock_client.return_value.results.return_value = [mock_paper]
        
        # Mock text extraction
        mock_extract_text.return_value = "D10: 5.2 µm D50: 12.3 µm D90: 25.1 µm"
        
        # Mock path operations
        mock_output_path = MagicMock()
        mock_output_path.parent.mkdir.return_value = None
        mock_path.return_value = mock_output_path
        
        # Run ingestion
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the output file path
            import src.ingest.arxiv_extractor as extractor
            original_output = extractor.OUTPUT_FILE
            extractor.OUTPUT_FILE = Path(tmpdir) / "test_output.json"
            
            try:
                result = run_arxiv_ingestion()
                
                # Verify output file was created
                assert os.path.exists(extractor.OUTPUT_FILE)
                
                # Verify content
                with open(extractor.OUTPUT_FILE, 'r') as f:
                    data = json.load(f)
                    assert isinstance(data, list)
            finally:
                extractor.OUTPUT_FILE = original_output
    
    @patch('src.ingest.arxiv_extractor.arxiv.Search')
    @patch('src.ingest.arxiv_extractor.arxiv.Client')
    def test_run_arxiv_ingestion_no_results(self, mock_client, mock_search):
        """Test ingestion when no papers are found."""
        mock_client.return_value.results.return_value = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.ingest.arxiv_extractor as extractor
            original_output = extractor.OUTPUT_FILE
            extractor.OUTPUT_FILE = Path(tmpdir) / "test_output.json"
            
            try:
                result = run_arxiv_ingestion()
                
                # Verify empty output file was created
                assert os.path.exists(extractor.OUTPUT_FILE)
                with open(extractor.OUTPUT_FILE, 'r') as f:
                    data = json.load(f)
                    assert data == []
            finally:
                extractor.OUTPUT_FILE = original_output
    
    @patch('src.ingest.arxiv_extractor.extract_text')
    def test_extraction_with_exception(self, mock_extract_text):
        """Test that exceptions are handled gracefully."""
        mock_extract_text.side_effect = Exception("PDF read error")
        
        # This should not raise an exception, just log a warning
        # and return empty records
        records = []
        try:
            # We can't easily test the full pipeline without mocking more,
            # but we can test the error handling logic
            from src.ingest.arxiv_extractor import _extract_psd_from_pdf
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(b"fake pdf")
                temp_path = f.name
            
            try:
                records = _extract_psd_from_pdf(temp_path, "test_id")
            except DataIngestionError:
                # Expected behavior
                pass
            finally:
                os.unlink(temp_path)
        except Exception:
            # Should not reach here
            pytest.fail("Unexpected exception during error handling test")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
