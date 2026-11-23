import pytest
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from main import run_pipeline_with_timeout, write_pipeline_status, TIMEOUT_SECONDS

class TestPipelineTimeout:
    @pytest.fixture
    def temp_paths(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            yield {
                'raw_data': base / 'data' / 'raw',
                'processed_metrics': base / 'data' / 'processed',
                'results': base / 'results',
                'logs': base / 'logs',
                'state': base / 'state'
            }
            # Create dirs
            for p in ['raw_data', 'processed_metrics', 'results', 'logs', 'state']:
                temp_paths[p].mkdir(parents=True, exist_ok=True)

    def test_successful_pipeline_writes_success_status(self, temp_paths):
        """Test that a successful run writes SUCCESS status."""
        config = {}
        
        # Mock the internal functions to avoid actual execution
        with patch('main.load_real_data'), \
             patch('main.run_regression'), \
             patch('main.Path.glob', return_value=[]): # No files to process
            
            status = run_pipeline_with_timeout(config, temp_paths)
            
            assert status['status'] == 'SUCCESS'
            assert status['network_id'] == 'aggregate'
            assert status['duration'] >= 0

    def test_timeout_writes_timeout_status(self, temp_paths):
        """Test that exceeding timeout writes TIMEOUT status."""
        config = {}
        
        # Mock load_real_data to take a long time (simulated by patching time)
        # We can't actually sleep for 6 hours, so we mock the time check logic
        # or force the timeout by mocking the elapsed time calculation.
        
        # Strategy: Mock time.time to jump forward
        original_time = time.time
        start = original_time()
        
        def mock_time():
            return start + TIMEOUT_SECONDS + 10 # Exceed limit
        
        with patch('main.load_real_data'), \
             patch('main.run_regression'), \
             patch('main.Path.glob', return_value=[]), \
             patch('main.time.time', side_effect=mock_time):
            
            status = run_pipeline_with_timeout(config, temp_paths)
            
            assert status['status'] == 'TIMEOUT'
            assert status['network_id'] == 'aggregate' # No network completed
            assert status['duration'] >= TIMEOUT_SECONDS

    def test_timeout_with_partial_completion(self, temp_paths):
        """Test that timeout after processing some networks logs the last ID."""
        config = {}
        mock_files = [Path('snap_1.mtx'), Path('snap_2.mtx')]
        
        # Mock glob to return files
        # We need to simulate processing one, then timing out on the next
        
        call_count = 0
        start = time.time()
        
        def mock_time():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return start
            elif call_count == 2:
                return start + TIMEOUT_SECONDS + 10
            return original_time()

        with patch('main.load_real_data'), \
             patch('main.run_regression'), \
             patch('main.Path.glob', return_value=mock_files), \
             patch('main.time.time', side_effect=mock_time):
             
            # We need to simulate that load_real_data or the loop checks time
            # The current implementation checks time at the start of the loop
            # But load_real_data is outside. Let's assume load_real_data takes time.
            # Actually, the loop checks:
            #   current_time = time.time()
            #   elapsed = current_time - start_time
            #   if elapsed > TIMEOUT_SECONDS: raise TimeoutError
            
            # To test "last_completed_network_id", we need to simulate:
            # 1. Process snap_1.mtx (success)
            # 2. Process snap_2.mtx (timeout)
            
            # Let's refine the mock_time to allow one iteration
            call_count = 0
            def mock_time_iter():
                nonlocal call_count
                # First call (start of loop): 0
                # Second call (check time): 0
                # Third call (next loop): > TIMEOUT
                if call_count < 3:
                    call_count += 1
                    return start
                call_count += 1
                return start + TIMEOUT_SECONDS + 10

            with patch('main.time.time', side_effect=mock_time_iter):
                 status = run_pipeline_with_timeout(config, temp_paths)
                 # The loop logic:
                 # for file in files:
                 #    check time -> OK
                 #    process -> OK
                 # next file
                 #    check time -> TIMEOUT -> raise
                 # So last_completed_network_id should be 'snap_1'
                 assert status['status'] == 'TIMEOUT'
                 # Note: The current implementation sets last_completed_network_id BEFORE processing.
                 # Let's verify the logic in main.py:
                 # for file_path in network_files:
                 #    ...
                 #    last_completed_network_id = network_id
                 #    ... process ...
                 # If timeout happens at check, last_completed is NOT updated for the current file.
                 # So it should be 'snap_1'.
                 assert status['network_id'] == 'snap_1'

    def test_write_pipeline_status_creates_json(self, temp_paths):
        """Test that write_pipeline_status creates the file with correct content."""
        status = {
            "network_id": "test_net",
            "duration": 100.0,
            "status": "SUCCESS"
        }
        output_path = temp_paths['results'] / "pipeline_status.json"
        
        write_pipeline_status(status, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['status'] == 'SUCCESS'
        assert data['network_id'] == 'test_net'
        assert data['duration'] == 100.0