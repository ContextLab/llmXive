import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.main import main, run_ingestion, generate_ingestion_summary
from code.utils.disk_check import InsufficientDiskSpaceError

class TestMainIntegration:
    """Integration tests for main.py orchestration logic."""

    @patch('code.main.check_disk_space')
    @patch('code.main.download_all_peaks')
    @patch('code.main.preprocess_all_cell_types')
    @patch('code.main.aggregate_background_model')
    @patch('code.main.scan_all_cell_types')
    @patch('code.main.aggregate_enrichment_results')
    @patch('code.main.generate_heatmap')
    @patch('code.main.calculate_silhouette_score')
    @patch('code.main.validate_motifs')
    @patch('code.main.generate_summary_table')
    @patch('code.main.save_provenance')
    def test_main_execution_flow(
        self,
        mock_save_provenance,
        mock_generate_summary_table,
        mock_validate_motifs,
        mock_calculate_silhouette_score,
        mock_generate_heatmap,
        mock_aggregate_enrichment_results,
        mock_scan_all_cell_types,
        mock_aggregate_background_model,
        mock_preprocess_all_cell_types,
        mock_download_all_peaks,
        mock_check_disk_space
    ):
        """Test that main() executes the full pipeline in correct order."""
        # Setup mocks
        mock_check_disk_space.return_value = None
        mock_download_all_peaks.return_value = {
            'GM12878': Path('/tmp/test.bed'),
            'K562': Path('/tmp/test.bed')
        }
        mock_preprocess_all_cell_types.return_value = {'GM12878': [], 'K562': []}
        mock_aggregate_background_model.return_value = {'GM12878': [], 'K562': []}
        mock_scan_all_cell_types.return_value = {'GM12878': [], 'K562': []}
        mock_aggregate_enrichment_results.return_value = []
        mock_generate_heatmap.return_value = {'silhouette_score': 0.5}
        mock_calculate_silhouette_score.return_value = 0.5
        mock_validate_motifs.return_value = {
            'overlap_pct': 65.0,
            'top_motifs': [{'motif_id': 'MA0001.1', 'q_value': 0.01, 'overlap_pct': 70.0}]
        }

        # Run main
        exit_code = main()

        # Assertions
        assert exit_code == 0
        mock_check_disk_space.assert_called_once()
        mock_download_all_peaks.assert_called_once()
        mock_preprocess_all_cell_types.assert_called_once()
        mock_aggregate_background_model.assert_called_once()
        mock_scan_all_cell_types.assert_called_once()
        mock_aggregate_enrichment_results.assert_called_once()
        mock_generate_heatmap.assert_called_once()
        mock_calculate_silhouette_score.assert_called_once()
        mock_validate_motifs.assert_called_once()
        mock_generate_summary_table.assert_called_once()
        mock_save_provenance.assert_called_once()

    @patch('code.main.check_disk_space')
    def test_main_disk_space_failure(self, mock_check_disk_space):
        """Test that main() fails gracefully when disk space is insufficient."""
        mock_check_disk_space.side_effect = InsufficientDiskSpaceError("Not enough space")

        exit_code = main()

        assert exit_code == 1
        mock_check_disk_space.assert_called_once()

    @patch('code.main.parse_bed_file')
    def test_generate_ingestion_summary_validates_cell_types(self, mock_parse_bed_file):
        """Test that generate_ingestion_summary raises error for unexpected cell types."""
        mock_parse_bed_file.return_value = []

        invalid_peaks = {'InvalidCellType': Path('/tmp/test.bed')}

        with pytest.raises(ValueError) as exc_info:
            generate_ingestion_summary(invalid_peaks)

        assert "Unexpected cell type" in str(exc_info.value)

    @patch('code.main.parse_bed_file')
    def test_generate_ingestion_summary_counts_peaks(self, mock_parse_bed_file):
        """Test that generate_ingestion_summary correctly counts peaks."""
        mock_parse_bed_file.side_effect = [
            ['peak1', 'peak2'],  # GM12878
            ['peak3']             # K562
        ]

        peak_files = {
            'GM12878': Path('/tmp/test1.bed'),
            'K562': Path('/tmp/test2.bed')
        }

        summary = generate_ingestion_summary(peak_files)

        assert summary['total_peaks'] == 3
        assert summary['parsed_count'] == 2
        assert 'GM12878' in summary['cell_types']
        assert 'K562' in summary['cell_types']
