"""
Unit tests for model_training module (T020)

Tests the n-gram model training functionality without requiring full dataset.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from model_training import (
    KneserNeyCountVectorizer,
    load_author_data,
    train_author_models,
    save_model,
    main,
    NGRAM_ORDERS,
    MIN_ABSTRACTS_PER_AUTHOR
)
from config import set_seed, reset_config


@pytest.fixture(autouse=True)
def setup_config():
    """Setup and teardown for test configuration."""
    reset_config()
    set_seed(42)
    yield
    reset_config()


@pytest.fixture
def temp_author_dir(tmp_path):
    """Create a temporary author directory with test abstracts."""
    author_dir = tmp_path / "test_author"
    author_dir.mkdir()
    
    # Create test abstracts
    abstracts = [
        "this is a test abstract for author training",
        "another test abstract with different content",
        "third abstract to ensure we have enough data",
        "fourth abstract for testing purposes only",
        "fifth abstract to reach minimum requirement",
        "sixth abstract with more text",
        "seventh abstract for good measure",
        "eighth abstract to be safe",
        "ninth abstract for training",
        "tenth abstract to complete the set",
        "eleventh extra abstract",
        "twelfth extra abstract"
    ]
    
    for i, abstract in enumerate(abstracts):
        (author_dir / f"abstract_{i}.txt").write_text(abstract)
    
    return author_dir


@pytest.fixture
def mock_processed_data(temp_author_dir):
    """Mock the data/processed directory structure."""
    with patch('model_training.DATA_PROCESSED_DIR', str(temp_author_dir.parent)):
        yield temp_author_dir


class TestKneserNeyCountVectorizer:
    """Tests for the Kneser-Ney approximated CountVectorizer."""
    
    def test_initialization(self):
        """Test vectorizer initialization with different parameters."""
        vec = KneserNeyCountVectorizer(ngram_range=(4, 4), alpha=0.1)
        assert vec.ngram_order == 4
        assert vec.alpha == 0.1
        assert vec.analyzer == 'char'
    
    def test_fit_transform_basic(self):
        """Test basic fit and transform functionality."""
        vec = KneserNeyCountVectorizer(ngram_range=(3, 3))
        docs = ["hello world", "foo bar baz"]
        
        vec.fit(docs)
        result = vec.transform(docs)
        
        assert result.shape[0] == 2
        assert result.shape[1] > 0
        assert np.all(result >= 0)  # Probabilities should be non-negative
    
    def test_different_ngram_orders(self):
        """Test vectorizer with different n-gram orders."""
        for n in [4, 5, 6]:
            vec = KneserNeyCountVectorizer(ngram_range=(n, n))
            docs = ["this is a test string for n-gram analysis"]
            
            vec.fit(docs)
            result = vec.transform(docs)
            
            assert result.shape[0] == 1
            assert vec.ngram_order == n
    
    def test_smoothing_effect(self):
        """Test that smoothing is applied (no zero probabilities after discount)."""
        vec = KneserNeyCountVectorizer(ngram_range=(2, 2), alpha=0.1)
        docs = ["ab cd", "ef gh"]
        
        vec.fit(docs)
        result = vec.transform(docs)
        
        # With smoothing, we should have normalized probabilities
        row_sums = result.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-5)


class TestLoadAuthorData:
    """Tests for loading author data."""
    
    def test_load_author_data_success(self, mock_processed_data):
        """Test successful loading of author abstracts."""
        abstracts = load_author_data("test_author")
        
        assert len(abstracts) == 12
        assert all(isinstance(a, str) for a in abstracts)
        assert all(len(a) > 0 for a in abstracts)
    
    def test_load_author_data_not_found(self, mock_processed_data):
        """Test error handling for missing author directory."""
        with pytest.raises(FileNotFoundError):
            load_author_data("non_existent_author")
    
    def test_load_author_data_empty_files(self, mock_processed_data, tmp_path):
        """Test handling of empty files in author directory."""
        author_dir = tmp_path / "empty_test"
        author_dir.mkdir()
        (author_dir / "empty.txt").write_text("")
        (author_dir / "non_empty.txt").write_text("content")
        
        with patch('model_training.DATA_PROCESSED_DIR', str(tmp_path)):
            abstracts = load_author_data("empty_test")
            
            assert len(abstracts) == 1
            assert abstracts[0] == "content"


class TestTrainAuthorModels:
    """Tests for author model training."""
    
    def test_train_models_basic(self, mock_processed_data):
        """Test basic model training for an author."""
        abstracts = load_author_data("test_author")
        result = train_author_models("test_author", abstracts)
        
        assert "models" in result
        assert "metrics" in result
        assert "train_count" in result
        assert "test_count" in result
        assert result["train_count"] + result["test_count"] == len(abstracts)
    
    def test_train_models_insufficient_data(self):
        """Test handling of insufficient data."""
        short_abstracts = ["short", "data"]
        result = train_author_models("short_author", short_abstracts)
        
        assert result["error"] == "insufficient_data"
    
    def test_train_models_multiple_orders(self, mock_processed_data):
        """Test training models for multiple n-gram orders."""
        abstracts = load_author_data("test_author")
        result = train_author_models("test_author", abstracts, ngram_orders=[4, 5])
        
        assert len(result["models"]) == 2
        assert "n4" in result["models"]
        assert "n5" in result["models"]
    
    def test_train_models_perplexity_calculation(self, mock_processed_data):
        """Test that perplexity is calculated correctly."""
        abstracts = load_author_data("test_author")
        result = train_author_models("test_author", abstracts)
        
        for model_name, metrics in result["metrics"].items():
            assert "perplexity" in metrics
            assert metrics["perplexity"] > 0


class TestSaveModel:
    """Tests for model saving functionality."""
    
    def test_save_model_success(self, mock_processed_data, tmp_path):
        """Test successful model saving."""
        abstracts = load_author_data("test_author")
        result = train_author_models("test_author", abstracts)
        
        with patch('model_training.OUTPUT_DIR', str(tmp_path / "models")):
            with patch('model_training.register_artifact'):
                with patch('model_training.hash_artifact', return_value="test_hash"):
                    model_path = save_model(
                        result["models"]["n4"], 
                        "test_author", 
                        4, 
                        is_fallback=False
                    )
                    
                    assert os.path.exists(model_path)
                    assert "author_test_author_n4.pkl" in model_path
    
    def test_save_model_fallback(self, mock_processed_data, tmp_path):
        """Test saving fallback model with correct naming."""
        abstracts = load_author_data("test_author")
        result = train_author_models("test_author", abstracts)
        
        with patch('model_training.OUTPUT_DIR', str(tmp_path / "models")):
            with patch('model_training.register_artifact'):
                with patch('model_training.hash_artifact', return_value="test_hash"):
                    model_path = save_model(
                        result["models"]["n4"], 
                        "test_author", 
                        4, 
                        is_fallback=True
                    )
                    
                    assert os.path.exists(model_path)
                    assert "fallback" in model_path


class TestMain:
    """Tests for the main entry point."""
    
    def test_main_execution(self, mock_processed_data, tmp_path):
        """Test main function execution."""
        with patch('model_training.DATA_PROCESSED_DIR', str(mock_processed_data.parent)):
            with patch('model_training.OUTPUT_DIR', str(tmp_path / "models")):
                with patch('model_training.METRICS_DIR', str(tmp_path / "metrics")):
                    with patch('model_training.register_artifact'):
                        with patch('model_training.hash_artifact', return_value="test_hash"):
                            result = main()
                            
                            assert result["total_authors"] > 0
                            assert result["successful"] > 0
                            assert os.path.exists(Path(tmp_path) / "models")
                            assert os.path.exists(Path(tmp_path) / "metrics" / "training_summary.json")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])