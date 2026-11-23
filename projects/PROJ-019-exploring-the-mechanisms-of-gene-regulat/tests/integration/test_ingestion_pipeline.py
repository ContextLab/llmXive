import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.main import run_ingestion
from code.config import DATA_PROCESSED_DIR, DATA_INTERIM_DIR

class TestIngestionPipelineIntegration:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            yield tmp_path

    @patch('code.main.check_disk_space')
    @patch('code.main.check_memory')
    @patch('code.main.download_all_peaks')
    @patch('code.main.parse_bed_file')
    @patch('code.main.process_cell_type_peaks')
    @patch('code.main.aggregate_background_model')
    def test_ingestion_creates_output_files(
        self,
        mock_agg_bg,
        mock_process,
        mock_parse,
        mock_download,
        mock_check_mem,
        mock_check_disk,
        temp_dirs
    ):
        """Test that ingestion creates all expected output files"""
        # Setup paths
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        DATA_INTERIM_DIR.mkdir(parents=True, exist_ok=True)

        # Setup mocks
        mock_download.return_value = {
            'GM12878': str(temp_dirs / 'GM12878.bed'),
            'K562': str(temp_dirs / 'K562.bed'),
            'HepG2': str(temp_dirs / 'HepG2.bed'),
            'H1-hESC': str(temp_dirs / 'H1-hESC.bed'),
            'IMR90': str(temp_dirs / 'IMR90.bed')
        }

        mock_parse.return_value = [
            {'chrom': 'chr1', 'start': 100, 'end': 200, 'name': 'peak1'}
        ]

        mock_process.return_value = [
            {'chrom': 'chr1', 'start': 100, 'end': 200, 'name': 'peak1', 'gene': 'GENE1'}
        ]

        mock_agg_bg.return_value = {'background': 'test'}

        # Run ingestion
        summary = run_ingestion()

        # Verify output file exists
        output_path = DATA_PROCESSED_DIR / "ingestion_summary.json"
        assert output_path.exists(), f"Output file not created: {output_path}"

        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'total_peaks' in data
        assert 'cell_types' in data
        assert 'parsed_count' in data
        assert 'timestamp' in data
        assert data['cell_types'] == ['GM1278', 'K562', 'HepG2', 'H1-hESC', 'IMR90']

        # Verify intermediate files
        for cell_type in ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']:
            interim_path = DATA_INTERIM_DIR / f"{cell_type}_peaks.bed"
            assert interim_path.exists(), f"Intermediate file not created: {interim_path}"

    @patch('code.main.check_disk_space')
    @patch('code.main.check_memory')
    @patch('code.main.download_all_peaks')
    def test_ingestion_with_predefined_files(
        self,
        mock_download,
        mock_check_mem,
        mock_check_disk,
        temp_dirs
    ):
        """Test ingestion with predefined peak files"""
        # Create dummy BED files
        cell_types = ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']
        peak_files = {}

        for ct in cell_types:
            bed_file = temp_dirs / f"{ct}.bed"
            with open(bed_file, 'w') as f:
                f.write("chr1\t100\t200\tpeak1\n")
                f.write("chr1\t300\t400\tpeak2\n")
            peak_files[ct] = str(bed_file)

        # Mock download to not be called
        mock_download.return_value = peak_files

        # Mock other dependencies
        with patch('code.main.parse_bed_file') as mock_parse, \
             patch('code.main.process_cell_type_peaks') as mock_process, \
             patch('code.main.aggregate_background_model') as mock_agg_bg:

            mock_parse.return_value = [
                {'chrom': 'chr1', 'start': 100, 'end': 200, 'name': 'peak1'},
                {'chrom': 'chr1', 'start': 300, 'end': 400, 'name': 'peak2'}
            ]

            mock_process.return_value = [
                {'chrom': 'chr1', 'start': 100, 'end': 200, 'name': 'peak1', 'gene': 'GENE1'},
                {'chrom': 'chr1', 'start': 300, 'end': 400, 'name': 'peak2', 'gene': 'GENE2'}
            ]

            mock_agg_bg.return_value = {'background': 'test'}

            # Run ingestion with predefined files
            summary = run_ingestion(peak_files=peak_files)

            # Verify results
            assert summary['total_peaks'] == 10  # 5 cell types * 2 peaks
            assert summary['parsed_count'] == 5
            assert set(summary['cell_types']) == set(cell_types)