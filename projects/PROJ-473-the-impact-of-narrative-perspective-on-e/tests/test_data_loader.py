"""
Unit tests for data_loader module.

These tests verify that the data loader correctly fetches and processes
real external datasets from Project Gutenberg, OSF, and Moral Foundations Twitter.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

# Import the module under test
from data_loader import (
    fetch_gutenberg_stories,
    load_reader_response_data,
    fetch_moral_foundations_twitter,
    fetch_all_datasets,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR
)
from utils import compute_artifact_hash

class TestDataLoader:
    """Test cases for data loading functionality."""
    
    def test_gutenberg_story_ids_are_valid(self):
        """Verify that Gutenberg story IDs are positive integers."""
        from data_loader import GUTENBERG_STORY_IDS
        assert len(GUTENBERG_STORY_IDS) > 0
        for book_id in GUTENBERG_STORY_IDS:
            assert isinstance(book_id, int)
            assert book_id > 0
    
    def test_data_directories_exist(self):
        """Verify that data directories are created."""
        assert DATA_RAW_DIR.exists()
        assert DATA_PROCESSED_DIR.exists()
    
    def test_artifact_hash_function_exists(self):
        """Verify that compute_artifact_hash is callable."""
        assert callable(compute_artifact_hash)
        
        # Test with a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash_value = compute_artifact_hash(temp_path)
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64  # SHA-256 hex length
        finally:
            os.unlink(temp_path)
    
    def test_reader_response_data_columns(self):
        """Verify that reader response data has required columns."""
        # This test will attempt to load real data
        try:
            df = load_reader_response_data()
            required_columns = ['story_id', 'empathy_score', 'moral_judgement_score']
            
            for col in required_columns:
                assert col in df.columns, f"Missing required column: {col}"
            
            assert len(df) > 0, "Reader response data should not be empty"
            
        except RuntimeError as e:
            # If real data is not available, skip this test
            pytest.skip(f"Real data not available: {e}")
    
    def test_data_loader_summary_created(self):
        """Verify that data loader summary file is created."""
        # Run fetch_all_datasets (may partially fail)
        results = fetch_all_datasets()
        
        summary_path = DATA_PROCESSED_DIR / "data_loader_summary.json"
        assert summary_path.exists(), "Summary file should be created"
        
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        assert 'gutenberg_count' in summary
        assert 'reader_responses_count' in summary
        assert 'moral_foundations_count' in summary
        assert 'errors' in summary
    
    def test_gutenberg_metadata_format(self):
        """Verify that Gutenberg metadata has correct format."""
        # This test will attempt to fetch real data
        try:
            stories = fetch_gutenberg_stories()
            
            if len(stories) > 0:
                required_fields = ['book_id', 'filename', 'filepath', 'hash', 'source']
                
                for story in stories:
                    for field in required_fields:
                        assert field in story, f"Missing field in story metadata: {field}"
                    
                    # Verify filepath exists
                    assert Path(story['filepath']).exists(), f"File not found: {story['filepath']}"
                    
                    # Verify hash is valid
                    assert len(story['hash']) == 64, f"Invalid hash length: {story['hash']}"
        
        except RuntimeError as e:
            pytest.skip(f"Real data not available: {e}")
    
    def test_data_integrity_on_reload(self):
        """Verify that reloading data produces consistent hashes."""
        # This is a basic test - in practice, we'd compare hashes across runs
        try:
            # Load data twice and compare
            df1 = load_reader_response_data()
            hash1 = compute_artifact_hash(str(DATA_RAW_DIR / "reader_responses.csv"))
            
            df2 = load_reader_response_data()
            hash2 = compute_artifact_hash(str(DATA_RAW_DIR / "reader_responses.csv"))
            
            # Hashes should be the same for the same data
            assert hash1 == hash2, "Data hash should be consistent across reloads"
            
        except RuntimeError as e:
            pytest.skip(f"Real data not available: {e}")

class TestDataLoaderErrors:
    """Test cases for error handling in data loading."""
    
    def test_invalid_url_handling(self):
        """Verify that invalid URLs raise appropriate errors."""
        with pytest.raises(RuntimeError):
            load_reader_response_data("https://invalid-url-that-does-not-exist.example.com/data.csv")
    
    def test_malformed_data_handling(self):
        """Verify that malformed data is handled gracefully."""
        # Create a temporary malformed CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("invalid,csv,content\nwithout,proper,columns\n")
            temp_path = f.name
        
        try:
            # This should fail when trying to parse
            with pytest.raises((ValueError, KeyError)):
                pd.read_csv(temp_path)
        finally:
            os.unlink(temp_path)
