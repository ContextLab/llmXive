"""Unit tests for control corpus generation."""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from generation.control_corpus import (
    load_control_dataset,
    sample_control_corpus,
    save_control_corpus,
    merge_with_phenomenological,
    verify_marker_absence,
    generate_control_corpus
)


class TestLoadControlDataset:
    """Tests for load_control_dataset function."""
    
    @patch('generation.control_corpus.load_dataset')
    def test_load_cnn_dailymail_success(self, mock_load_dataset):
        """Test successful loading of cnn_dailymail dataset."""
        # Mock dataset
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([
            {"article": "Test article text for control corpus."},
            {"article": "Another test article."}
        ]))
        mock_load_dataset.return_value = mock_dataset
        
        dataset = load_control_dataset(split="train", limit=2)
        
        mock_load_dataset.assert_called_once_with(
            "cnn_dailymail",
            name="3.0.0",
            split="train",
            trust_remote_code=True,
            streaming=True
        )
        assert dataset is not None
    
    @patch('generation.control_corpus.load_dataset')
    def test_load_fallback_to_imdb(self, mock_load_dataset):
        """Test fallback to imdb when cnn_dailymail fails."""
        # First call fails, second succeeds
        mock_load_dataset.side_effect = [
            Exception("Dataset not found"),
            Mock(__iter__=Mock(return_value=iter([
                {"text": "Test review text."}
            ])))
        ]
        
        dataset = load_control_dataset(split="train", limit=1)
        
        # Should have called load_dataset twice
        assert mock_load_dataset.call_count == 2
        assert dataset is not None


class TestSampleControlCorpus:
    """Tests for sample_control_corpus function."""
    
    def test_sample_basic(self):
        """Test basic sampling from dataset."""
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([
            {"article": "Test article " + str(i) * 100} for i in range(10)
        ]))
        
        samples = sample_control_corpus(mock_dataset, n_samples=5)
        
        assert len(samples) == 5
        assert all(s["type"] == "control" for s in samples)
        assert all(s["strategy"] == "Technical" for s in samples)
        assert all("control_" in s["id"] for s in samples)
    
    def test_sample_empty_dataset(self):
        """Test sampling from empty dataset."""
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([]))
        
        samples = sample_control_corpus(mock_dataset, n_samples=5)
        
        assert len(samples) == 0
    
    def test_sample_short_text_filtered(self):
        """Test that short text samples are filtered out."""
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([
            {"article": "Short"},  # Should be filtered
            {"article": "A" * 200},  # Should be included
            {"article": "B" * 200}   # Should be included
        ]))
        
        samples = sample_control_corpus(mock_dataset, n_samples=10)
        
        assert len(samples) == 2


class TestSaveControlCorpus:
    """Tests for save_control_corpus function."""
    
    def test_save_csv(self):
        """Test saving samples to CSV."""
        samples = [
            {"id": "control_0001", "text": "Test text", "type": "control"},
            {"id": "control_0002", "text": "More text", "type": "control"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            save_control_corpus(samples, temp_path)
            
            # Verify file exists and contains data
            assert os.path.exists(temp_path)
            df = pd.read_csv(temp_path)
            assert len(df) == 2
            assert "id" in df.columns
            assert "type" in df.columns
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestMergeWithPhenomenological:
    """Tests for merge_with_phenomenological function."""
    
    def test_merge_with_existing_pheno(self):
        """Test merging control with existing phenomenological data."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            control_path = f.name
            pd.DataFrame([{"id": "c1", "type": "control"}]).to_csv(f, index=False)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pheno_path = f.name
            pd.DataFrame([{"id": "p1", "type": "phenomenological"}]).to_csv(f, index=False)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name
        
        try:
            merge_with_phenomenological(control_path, pheno_path, output_path)
            
            # Verify merged file
            assert os.path.exists(output_path)
            df = pd.read_csv(output_path)
            assert len(df) == 2
            assert set(df['type'].values) == {'control', 'phenomenological'}
        finally:
            for path in [control_path, pheno_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_merge_no_pheno(self):
        """Test merging when no phenomenological data exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            control_path = f.name
            pd.DataFrame([{"id": "c1", "type": "control"}]).to_csv(f, index=False)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name
        
        try:
            merge_with_phenomenological(control_path, "nonexistent.csv", output_path)
            
            assert os.path.exists(output_path)
            df = pd.read_csv(output_path)
            assert len(df) == 1
            assert df['type'].iloc[0] == 'control'
        finally:
            for path in [control_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)


class TestVerifyMarkerAbsence:
    """Tests for verify_marker_absence function."""
    
    def test_verify_no_markers(self):
        """Test verification when no markers are present."""
        samples = [
            {"id": "c1", "text": "Technical report without markers."},
            {"id": "c2", "text": "Another technical document."}
        ]
        marker_dicts = {
            "sensory": ["see", "hear", "feel"],
            "temporal": ["now", "then", "before"],
            "intentional": ["think", "believe", "desire"]
        }
        
        results = verify_marker_absence(samples, marker_dicts)
        
        assert results["samples_with_markers"] == 0
        assert results["total_samples"] == 2
    
    def test_verify_with_markers(self):
        """Test verification when some markers are present."""
        samples = [
            {"id": "c1", "text": "I see the light."},  # Contains 'see'
            {"id": "c2", "text": "Technical report."}
        ]
        marker_dicts = {
            "sensory": ["see", "hear", "feel"],
            "temporal": ["now", "then", "before"],
            "intentional": ["think", "believe", "desire"]
        }
        
        results = verify_marker_absence(samples, marker_dicts)
        
        assert results["samples_with_markers"] == 1
        assert results["total_samples"] == 2
        assert results["marker_counts"]["sensory"] >= 1


class TestGenerateControlCorpus:
    """Tests for generate_control_corpus function."""
    
    @patch('generation.control_corpus.load_control_dataset')
    @patch('generation.control_corpus.sample_control_corpus')
    @patch('generation.control_corpus.save_control_corpus')
    @patch('generation.control_corpus.verify_marker_absence')
    @patch('generation.control_corpus.safe_write_json')
    def test_generate_full_pipeline(self, mock_write_json, mock_verify, mock_save, mock_sample, mock_load):
        """Test full control corpus generation pipeline."""
        # Setup mocks
        mock_dataset = Mock()
        mock_load.return_value = mock_dataset
        mock_sample.return_value = [
            {"id": "control_0001", "text": "Test", "type": "control"}
        ]
        mock_verify.return_value = {"samples_with_markers": 0}
        
        config = {
            "generation_limit": 10,
            "output_dir": tempfile.mkdtemp()
        }
        
        try:
            generate_control_corpus(config)
            
            # Verify all functions were called
            mock_load.assert_called_once()
            mock_sample.assert_called_once()
            mock_save.assert_called_once()
            mock_verify.assert_called_once()
            mock_write_json.assert_called_once()
        finally:
            import shutil
            shutil.rmtree(config["output_dir"], ignore_errors=True)