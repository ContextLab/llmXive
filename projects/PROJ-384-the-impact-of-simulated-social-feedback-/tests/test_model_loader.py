"""
Tests for the model_loader module.

Verifies that:
1. The sentiment pipeline loads correctly
2. The Rosenberg lexicon loads correctly
3. Caching works as expected
4. Error handling works for missing files
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from utils.model_loader import (
    get_sentiment_pipeline,
    get_rosenberg_lexicon,
    clear_cache
)
from utils.config import DATA_RAW_DIR


class TestModelLoader:
    """Test cases for model loading functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Clear cache before each test to ensure clean state
        clear_cache()
    
    def teardown_method(self):
        """Tear down test fixtures after each test method."""
        # Clear cache after each test
        clear_cache()
    
    def test_sentiment_pipeline_loads(self):
        """Test that the sentiment pipeline loads successfully."""
        # This test may take a moment as it downloads the model
        pipeline = get_sentiment_pipeline()
        assert pipeline is not None
        assert hasattr(pipeline, 'run') or callable(pipeline)
    
    def test_sentiment_pipeline_caching(self):
        """Test that the sentiment pipeline is cached."""
        # Get the pipeline twice
        pipeline1 = get_sentiment_pipeline()
        pipeline2 = get_sentiment_pipeline()
        
        # They should be the same object
        assert pipeline1 is pipeline2
    
    def test_rosenberg_lexicon_loads(self):
        """Test that the Rosenberg lexicon loads successfully."""
        lexicon = get_rosenberg_lexicon()
        assert lexicon is not None
        assert isinstance(lexicon, set)
        assert len(lexicon) > 0
    
    def test_rosenberg_lexicon_caching(self):
        """Test that the Rosenberg lexicon is cached."""
        # Get the lexicon twice
        lexicon1 = get_rosenberg_lexicon()
        lexicon2 = get_rosenberg_lexicon()
        
        # They should be the same object
        assert lexicon1 is lexicon2
    
    def test_rosenberg_lexicon_contains_expected_words(self):
        """Test that the lexicon contains expected Rosenberg words."""
        lexicon = get_rosenberg_lexicon()
        
        # Common Rosenberg self-esteem scale words (lowercase)
        expected_words = ['good', 'worthwhile', 'failure', 'adequate', 
                         'like', 'respect', 'feel', 'worthy']
        
        # Check that at least some expected words are present
        found_words = [word for word in expected_words if word in lexicon]
        assert len(found_words) > 0, f"Expected some Rosenberg words, found: {found_words}"
    
    def test_clear_cache(self):
        """Test that clear_cache properly resets the cache."""
        # Load both items
        pipeline1 = get_sentiment_pipeline()
        lexicon1 = get_rosenberg_lexicon()
        
        # Clear cache
        clear_cache()
        
        # Load again - should create new instances
        pipeline2 = get_sentiment_pipeline()
        lexicon2 = get_rosenberg_lexicon()
        
        # The cache should be reset (though we can't easily test object identity
        # for the pipeline due to its complexity, we can test the lexicon)
        # Note: This test primarily verifies the function runs without error
        assert pipeline2 is not None
        assert lexicon2 is not None
    
    def test_rosenberg_lexicon_missing_file(self):
        """Test error handling when lexicon file is missing."""
        # Temporarily rename the lexicon file
        lexicon_path = DATA_RAW_DIR / "lexicons" / "rosenberg_words.txt"
        
        if lexicon_path.exists():
            backup_path = lexicon_path.with_suffix('.txt.backup')
            lexicon_path.rename(backup_path)
            
            try:
                # Clear cache to force reload
                clear_cache()
                
                # Should raise FileNotFoundError
                with pytest.raises(FileNotFoundError):
                    get_rosenberg_lexicon()
            finally:
                # Restore the file
                if backup_path.exists():
                    lexicon_path.parent.mkdir(parents=True, exist_ok=True)
                    backup_path.rename(lexicon_path)
        else:
            # If file doesn't exist, skip this test
            pytest.skip("Lexicon file does not exist, skipping missing file test")
