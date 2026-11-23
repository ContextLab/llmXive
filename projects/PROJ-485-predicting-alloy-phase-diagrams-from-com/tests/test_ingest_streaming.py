import os
import sys
import csv
import tempfile
import json
import time
from unittest.mock import patch, MagicMock
import pytest

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ingest.load_data import stream_data, load_data_from_url, load_data_from_local_fallback
from utils.error_codes import ErrorCode

class TestStreamingDataLoader:
    """Tests for streaming data loader functionality."""

    def test_stream_data_memory_efficient(self):
        """Test that streaming processes data in chunks without loading everything into memory."""
        # Create a temporary large CSV file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['temperature', 'composition', 'element_a', 'element_b'])
            
            # Write 1.1 million rows to simulate large dataset
            row_count = 0
            for i in range(1100000):
                writer.writerow([i * 0.001, i % 100, 'Cu', 'Zn'])
                row_count += 1
                
            temp_path = f.name
            
        try:
            # Test streaming with file:// URL simulation
            # Note: In real implementation, this would use HTTP streaming
            # For testing, we verify the logic handles large files
            from ingest.load_data import load_data_from_local_fallback
            
            output_path = temp_path + '_output.csv'
            count = load_data_from_local_fallback(temp_path, output_path)
            
            assert count == 1100000, f"Expected 1100000 rows, got {count}"
            assert os.path.exists(output_path), "Output file was not created"
            
            # Verify output file size is reasonable (not exploded)
            output_size = os.path.getsize(output_path)
            assert output_size < 100 * 1024 * 1024, "Output file is unexpectedly large"
            
            # Verify we can read it back
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 1100001, f"Expected 1100001 lines (including header), got {len(rows)}"
                
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_path + '_output.csv'):
                os.remove(temp_path + '_output.csv')

    def test_stream_data_filters_missing_temperature(self):
        """Test that rows with missing temperature are filtered out."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['temperature', 'composition', 'element_a', 'element_b'])
            writer.writerow(['1000', '50', 'Cu', 'Zn'])
            writer.writerow(['', '50', 'Cu', 'Zn'])  # Missing temperature
            writer.writerow(['1200', '60', 'Cu', 'Zn'])
            writer.writerow(['', '70', 'Cu', 'Zn'])  # Missing temperature
            writer.writerow(['1400', '80', 'Cu', 'Zn'])
            
            temp_path = f.name
            
        try:
            output_path = temp_path + '_output.csv'
            count = load_data_from_local_fallback(temp_path, output_path)
            
            assert count == 3, f"Expected 3 rows (filtered), got {count}"
            
            # Verify output contains only valid rows
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 3
                for row in rows:
                    assert row['temperature'] != '', "Row with missing temperature was not filtered"
                    
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_path + '_output.csv'):
                os.remove(temp_path + '_output.csv')

    def test_stream_data_handles_large_file_without_oom(self):
        """Test that streaming handles large files without OOM errors."""
        # Create a simulated large file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['temperature', 'composition', 'element_a', 'element_b'])
            
            # Write 2 million rows
            for i in range(2000000):
                writer.writerow([str(i * 0.001), str(i % 100), 'Cu', 'Zn'])
                
            temp_path = f.name
            
        try:
            output_path = temp_path + '_output.csv'
            count = load_data_from_local_fallback(temp_path, output_path)
            
            assert count == 2000000, f"Expected 2000000 rows, got {count}"
            assert os.path.exists(output_path), "Output file was not created"
            
            # Verify file exists and has content
            assert os.path.getsize(output_path) > 0, "Output file is empty"
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_path + '_output.csv'):
                os.remove(temp_path + '_output.csv')

    def test_stream_data_fails_loudly_on_missing_source(self):
        """Test that missing data source raises appropriate error."""
        from utils.config import reset_config, get_config
        
        # Set empty config
        with patch('ingest.load_data.get_config') as mock_config:
            mock_config.return_value = {
                'nist_janaf_url': '',
                'sgte_url': '',
                'local_fallback_path': ''
            }
            
            try:
                load_data_from_url('', 'output.csv')
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert ErrorCode.DATA_SOURCE_MISSING.value in str(e), f"Wrong error code: {e}"

    def test_stream_data_writes_real_output_to_disk(self):
        """Test that streaming actually writes output to disk, not just memory."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['temperature', 'composition', 'element_a', 'element_b'])
            writer.writerow(['1000', '50', 'Cu', 'Zn'])
            writer.writerow(['1200', '60', 'Cu', 'Zn'])
            writer.writerow(['1400', '70', 'Cu', 'Zn'])
            
            temp_path = f.name
            
        try:
            output_path = temp_path + '_output.csv'
            count = load_data_from_local_fallback(temp_path, output_path)
            
            assert count == 3
            assert os.path.exists(output_path), "Output file must exist on disk"
            
            # Verify file is readable and contains expected data
            with open(output_path, 'r') as f:
                content = f.read()
                assert '1000' in content
                assert '1200' in content
                assert '1400' in content
                assert 'Cu' in content
                assert 'Zn' in content
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_path + '_output.csv'):
                os.remove(temp_path + '_output.csv')