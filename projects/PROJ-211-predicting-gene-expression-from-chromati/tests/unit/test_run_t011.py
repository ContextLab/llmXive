import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path for imports
sys.path.insert(0, 'code')

class TestRunT011:
    
    @pytest.fixture
    def mock_utils(self):
        with patch('code.utils.checksum_file') as mock_checksum:
            mock_checksum.return_value = "abc123"
            yield mock_checksum

    @pytest.fixture
    def mock_generate_data(self):
        with patch('code.generate_data.set_seed') as mock_seed, \
             patch('code.generate_data.generate_gene_coordinates') as mock_genes, \
             patch('code.generate_data.generate_peak_coordinates') as mock_peaks, \
             patch('code.generate_data.generate_counts_matrix') as mock_counts, \
             patch('code.generate_data.write_counts_csv') as mock_write_counts, \
             patch('code.generate_data.write_peaks_bed') as mock_write_peaks:
            
            mock_genes.return_value = []
            mock_peaks.return_value = []
            mock_counts.return_value = {}
            
            yield {
                'set_seed': mock_seed,
                'generate_gene_coordinates': mock_genes,
                'generate_peak_coordinates': mock_peaks,
                'generate_counts_matrix': mock_counts,
                'write_counts_csv': mock_write_counts,
                'write_peaks_bed': mock_write_peaks
            }

    def test_main_creates_directories(self, mock_utils, mock_generate_data, tmp_path):
        """Test that main creates necessary directories"""
        with patch('code.run_t011.os.makedirs') as mock_makedirs, \
             patch('code.run_t011.os.path.exists', return_value=True), \
             patch('code.run_t011.open', create=True), \
             patch('code.run_t011.checksum_file', return_value="test"):
            
            from run_t011 import main
            
            # Mock the actual file operations to avoid writing to disk in test
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch('code.run_t011.os.path.dirname', return_value=tmpdir), \
                     patch('code.run_t011.os.path.exists', return_value=True):
                    
                    # Run main (it should complete without error)
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected from sys.exit(0)
                    
                    # Verify directories were created
                    assert mock_makedirs.called

    def test_main_calls_seed_and_generation_functions(self, mock_utils, mock_generate_data):
        """Test that main calls the generation functions in correct order"""
        with patch('code.run_t011.os.path.exists', return_value=True), \
             patch('code.run_t011.open', create=True), \
             patch('code.run_t011.checksum_file', return_value="test"):
            
            from run_t011 import main
            
            try:
                main()
            except SystemExit:
                pass
            
            # Verify functions were called
            mock_generate_data['set_seed'].assert_called_once()
            mock_generate_data['generate_gene_coordinates'].assert_called_once()
            mock_generate_data['generate_peak_coordinates'].assert_called_once()
            mock_generate_data['generate_counts_matrix'].assert_called_once()
            mock_generate_data['write_counts_csv'].assert_called_once()
            mock_generate_data['write_peaks_bed'].assert_called_once()

    def test_main_calculates_checksums(self, mock_utils, mock_generate_data):
        """Test that main calculates checksums for output files"""
        with patch('code.run_t011.os.path.exists', return_value=True), \
             patch('code.run_t011.open', create=True), \
             patch('code.run_t011.checksum_file', return_value="test"):
            
            from run_t011 import main
            
            try:
                main()
            except SystemExit:
                pass
            
            # Verify checksum_file was called twice (once for counts, once for peaks)
            assert mock_utils.call_count == 2

    def test_main_handles_missing_file_error(self, mock_utils, mock_generate_data):
        """Test that main raises FileNotFoundError if output files are missing"""
        with patch('code.run_t011.os.path.exists', side_effect=[True, False]), \
             patch('code.run_t011.open', create=True), \
             patch('code.run_t011.checksum_file', return_value="test"):
            
            from run_t011 import main
            
            with pytest.raises(FileNotFoundError, match="Failed to create"):
                try:
                    main()
                except SystemExit:
                    pass  # Ignore sys.exit

    def test_main_logs_checksums(self, mock_utils, mock_generate_data):
        """Test that main logs checksums to the checksum file"""
        with patch('code.run_t011.os.path.exists', return_value=True), \
             patch('code.run_t011.open', create=True) as mock_open, \
             patch('code.run_t011.checksum_file', return_value="test"):
            
            from run_t011 import main
            
            try:
                main()
            except SystemExit:
                pass
            
            # Verify file was opened for writing checksums
            assert mock_open.called
            mock_open.assert_any_call('logs/checksums.txt', 'a')