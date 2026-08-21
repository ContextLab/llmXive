import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.main import generate_ingestion_summary, run_ingestion, EXPECTED_CELL_TYPES

class TestGenerateIngestionSummary:
    def test_valid_cell_types(self):
        """Test with valid cell types"""
        summary = generate_ingestion_summary(
            total_peaks=1000,
            cell_types=EXPECTED_CELL_TYPES,
            parsed_count=5
        )
        assert summary['total_peaks'] == 1000
        assert summary['cell_types'] == EXPECTED_CELL_TYPES
        assert summary['parsed_count'] == 5
        assert 'timestamp' in summary
        assert summary['status'] == 'completed'

    def test_invalid_cell_types_raises_error(self):
        """Test that invalid cell types raise ValueError"""
        with pytest.raises(ValueError) as exc_info:
            generate_ingestion_summary(
                total_peaks=1000,
                cell_types=['GM12878', 'K562', 'INVALID'],
                parsed_count=3
            )
        assert 'Unexpected cell types' in str(exc_info.value)

    def test_missing_cell_types_raises_error(self):
        """Test that missing expected cell types raise ValueError"""
        with pytest.raises(ValueError) as exc_info:
            generate_ingestion_summary(
                total_peaks=1000,
                cell_types=['GM12878'],  # Missing others
                parsed_count=1
            )
        assert 'Unexpected cell types' in str(exc_info.value)

class TestRunIngestion:
    @patch('code.main.download_all_peaks')
    @patch('code.main.parse_bed_file')
    @patch('code.main.process_cell_type_peaks')
    @patch('code.main.aggregate_background_model')
    @patch('code.main.check_disk_space')
    @patch('code.main.check_memory')
    def test_run_ingestion_success(
        self,
        mock_check_mem,
        mock_check_disk,
        mock_agg_bg,
        mock_process,
        mock_parse,
        mock_download
    ):
        """Test successful ingestion pipeline"""
        # Setup mocks
        mock_download.return_value = {
            'GM12878': '/tmp/GM12878_peaks.bed',
            'K562': '/tmp/K562_peaks.bed',
            'HepG2': '/tmp/HepG2_peaks.bed',
            'H1-hESC': '/tmp/H1-hESC_peaks.bed',
            'IMR90': '/tmp/IMR90_peaks.bed'
        }

        mock_parse.return_value = [
            {'chrom': 'chr1', 'start': 100, 'end': 200, 'name': 'peak1'},
            {'chrom': 'chr1', 'start': 300, 'end': 400, 'name': 'peak2'}
        ]

        mock_process.return_value = [
            {'chrom': 'chr1', 'start': 100, 'end': 200, 'name': 'peak1', 'gene': 'GENE1'},
            {'chrom': 'chr1', 'start': 300, 'end': 400, 'name': 'peak2', 'gene': 'GENE2'}
        ]

        mock_agg_bg.return_value = {'background': 'test'}

        # Run ingestion
        summary = run_ingestion()

        # Verify results
        assert summary['total_peaks'] == 10  # 5 cell types * 2 peaks each
        assert summary['parsed_count'] == 5
        assert summary['cell_types'] == EXPECTED_CELL_TYPES

    @patch('code.main.download_all_peaks')
    def test_run_ingestion_download_failure(self, mock_download):
        """Test that download failure raises DataFetchError"""
        from code.utils.network import DataFetchError
        mock_download.side_effect = DataFetchError("Download failed")

        with pytest.raises(DataFetchError):
            run_ingestion()

    @patch('code.main.parse_bed_file')
    def test_run_ingestion_parse_failure(self, mock_parse):
        """Test that parse failure is handled gracefully"""
        from code.main import EXPECTED_CELL_TYPES

        # Setup mock to return files but fail on parse
        mock_files = {ct: f'/tmp/{ct}.bed' for ct in EXPECTED_CELL_TYPES}

        with patch('code.main.download_all_peaks', return_value=mock_files):
            mock_parse.side_effect = Exception("Parse error")

            # Should not raise, but parsed_count should be 0
            summary = run_ingestion()
            assert summary['parsed_count'] == 0
            assert summary['total_peaks'] == 0
