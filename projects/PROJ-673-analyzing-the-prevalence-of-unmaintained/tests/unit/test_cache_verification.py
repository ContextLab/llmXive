"""
Test T008b: Verify local file caching mechanism with real pipeline simulation.

This test simulates the cache hit and cache miss scenarios as described in the task
verification steps, ensuring the caching mechanism works correctly with real data
operations (writing to and reading from disk).
"""
import os
import json
import hashlib
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
from src.utils.cache import save_response_to_cache, load_from_cache
from src.utils.checksum import generate_checksum


class TestCacheVerification:
    """Tests for T008b: Cache mechanism verification."""

    def test_cache_hit_verification(self, tmp_path):
        """
        Verify that a cache hit works correctly.
        1. Save a response with specific params.
        2. Load the response with the same params.
        3. Assert the data matches.
        """
        # Mock the cache directory to use a temp directory
        original_cache_dir = os.environ.get('CACHE_DIR')
        os.environ['CACHE_DIR'] = str(tmp_path / 'data' / 'raw')
        
        # Ensure directory exists (simulating T001/T008 setup)
        Path(os.environ['CACHE_DIR']).mkdir(parents=True, exist_ok=True)

        try:
            request_params = {'test': 1}
            response_data = {'data': 'test'}

            # Step 1: Save to cache
            checksum = save_response_to_cache(request_params, response_data)
            assert checksum is not None, "Checksum should be generated"
            
            # Verify file exists
            expected_filename = f"{checksum}.json"
            file_path = Path(os.environ['CACHE_DIR']) / expected_filename
            assert file_path.exists(), f"Cache file {expected_filename} should exist"

            # Step 2: Load from cache
            loaded_data = load_from_cache(request_params)
            
            # Step 3: Verify data matches
            assert loaded_data == response_data, "Loaded data should match saved data"
            print("Cache hit verified")

        finally:
            if original_cache_dir:
                os.environ['CACHE_DIR'] = original_cache_dir
            elif 'CACHE_DIR' in os.environ:
                del os.environ['CACHE_DIR']

    def test_cache_miss_and_isolation(self, tmp_path):
        """
        Verify that a cache miss does not overwrite existing files
        and retrieves the correct file for different params.
        """
        original_cache_dir = os.environ.get('CACHE_DIR')
        os.environ['CACHE_DIR'] = str(tmp_path / 'data' / 'raw')
        Path(os.environ['CACHE_DIR']).mkdir(parents=True, exist_ok=True)

        try:
            # First save
            params_1 = {'test': 1}
            data_1 = {'data': 'test'}
            checksum_1 = save_response_to_cache(params_1, data_1)
            
            # Second save (simulating cache miss scenario for new data)
            params_2 = {'test': 2}
            data_2 = {'data': 'test2'}
            checksum_2 = save_response_to_cache(params_2, data_2)

            # Verify two distinct files exist
            file_1 = Path(os.environ['CACHE_DIR']) / f"{checksum_1}.json"
            file_2 = Path(os.environ['CACHE_DIR']) / f"{checksum_2}.json"
            
            assert file_1.exists(), "First cache file should exist"
            assert file_2.exists(), "Second cache file should exist"
            assert checksum_1 != checksum_2, "Checksums should be different for different params"

            # Verify retrieval
            loaded_1 = load_from_cache(params_1)
            loaded_2 = load_from_cache(params_2)

            assert loaded_1 == data_1, "First load should return first data"
            assert loaded_2 == data_2, "Second load should return second data"
            
            # Verify non-overwrite: data_1 should still be intact
            loaded_1_again = load_from_cache(params_1)
            assert loaded_1_again == data_1, "First data should not be overwritten by second save"

        finally:
            if original_cache_dir:
                os.environ['CACHE_DIR'] = original_cache_dir
            elif 'CACHE_DIR' in os.environ:
                del os.environ['CACHE_DIR']

    def test_checksum_integrity(self, tmp_path):
        """
        Verify that the file content checksum matches the filename.
        """
        original_cache_dir = os.environ.get('CACHE_DIR')
        os.environ['CACHE_DIR'] = str(tmp_path / 'data' / 'raw')
        Path(os.environ['CACHE_DIR']).mkdir(parents=True, exist_ok=True)

        try:
            request_params = {'integrity': 'check'}
            response_data = {'value': 12345}

            checksum = save_response_to_cache(request_params, response_data)
            file_path = Path(os.environ['CACHE_DIR']) / f"{checksum}.json"

            # Compute checksum of file content
            with open(file_path, 'rb') as f:
                file_content_hash = generate_checksum(str(file_path))

            assert file_content_hash == checksum, "File content hash should match filename"

        finally:
            if original_cache_dir:
                os.environ['CACHE_DIR'] = original_cache_dir
            elif 'CACHE_DIR' in os.environ:
                del os.environ['CACHE_DIR']

    def test_cache_miss_returns_none(self, tmp_path):
        """
        Verify that loading non-existent params returns None.
        """
        original_cache_dir = os.environ.get('CACHE_DIR')
        os.environ['CACHE_DIR'] = str(tmp_path / 'data' / 'raw')
        Path(os.environ['CACHE_DIR']).mkdir(parents=True, exist_ok=True)

        try:
            result = load_from_cache({'non_existent': 'key'})
            assert result is None, "Cache miss should return None"

        finally:
            if original_cache_dir:
                os.environ['CACHE_DIR'] = original_cache_dir
            elif 'CACHE_DIR' in os.environ:
                del os.environ['CACHE_DIR']