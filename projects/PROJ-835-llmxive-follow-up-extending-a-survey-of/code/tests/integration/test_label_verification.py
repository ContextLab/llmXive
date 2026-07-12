"""
Integration tests for label verification (T011b).
Tests the automated check for absence of latent-space correlation.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.verify_labels import (
    load_dataset,
    validate_dataset_schema,
    check_label_embedding_correlation,
    check_metadata_correlation,
    verify_labels
)


class TestLabelVerification:
    """Integration tests for label verification functionality."""

    def test_load_dataset_basic(self):
        """Test loading embeddings from a parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy embeddings
            embeddings = np.random.randn(100, 512)
            df = pd.DataFrame({'embedding': list(embeddings)})
            path = Path(tmpdir) / "embeddings.parquet"
            df.to_parquet(path)
            
            data = load_dataset(str(path))
            
            assert 'embeddings' in data
            assert data['embeddings'].shape == (100, 512)
            assert data['embeddings_df'] is not None

    def test_validate_dataset_schema_valid(self):
        """Test schema validation with valid data."""
        embeddings = np.random.randn(50, 128)
        data = {'embeddings': embeddings}
        
        assert validate_dataset_schema(data) is True

    def test_validate_dataset_schema_invalid(self):
        """Test schema validation with invalid data."""
        # Missing embeddings
        assert validate_dataset_schema({}) is False
        
        # Wrong shape
        data = {'embeddings': np.random.randn(10,)}  # 1D instead of 2D
        assert validate_dataset_schema(data) is False

    def test_check_label_correlation_no_correlation(self):
        """Test that random embeddings and labels show no correlation."""
        np.random.seed(42)
        embeddings = np.random.randn(200, 64)
        labels = np.random.randint(0, 2, 200)
        
        is_suspicious, stats = check_label_embedding_correlation(
            embeddings, labels, correlation_threshold=0.3, p_value_threshold=0.05
        )
        
        # With random data, should not be suspicious
        assert is_suspicious is False
        assert 'mean_correlation' in stats
        assert 'max_correlation' in stats

    def test_check_label_correlation_with_correlation(self):
        """Test detection of actual correlation between embeddings and labels."""
        np.random.seed(42)
        n_samples = 500
        
        # Create embeddings where first dimension correlates with labels
        labels = np.random.randint(0, 2, n_samples)
        embeddings = np.random.randn(n_samples, 64)
        # Inject correlation: add label-dependent offset to first dimension
        embeddings[:, 0] += labels * 2.0
        
        is_suspicious, stats = check_label_embedding_correlation(
            embeddings, labels, correlation_threshold=0.3, p_value_threshold=0.05
        )
        
        # Should detect correlation
        assert is_suspicious is True
        assert stats['max_correlation'] > 0.3

    def test_check_metadata_correlation(self):
        """Test metadata correlation check."""
        np.random.seed(42)
        n_samples = 300
        
        embeddings = np.random.randn(n_samples, 32)
        metadata = {
            'random_field': np.random.randn(n_samples),
            'correlated_field': embeddings[:, 0] + np.random.randn(n_samples) * 0.1
        }
        
        is_suspicious, stats = check_metadata_correlation(
            embeddings, metadata, correlation_threshold=0.3, p_value_threshold=0.05
        )
        
        # correlated_field should show correlation
        assert 'correlated_field' in stats
        assert stats['correlated_field']['max_correlation'] > 0.3

    def test_verify_labels_full_pipeline(self):
        """Test the full verification pipeline with valid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create embeddings
            embeddings = np.random.randn(200, 64)
            embed_df = pd.DataFrame({'embedding': list(embeddings)})
            embed_path = Path(tmpdir) / "embeddings.parquet"
            embed_df.to_parquet(embed_path)
            
            # Create labels (random, no correlation)
            labels = np.random.randint(0, 2, 200)
            label_df = pd.DataFrame({'label': labels})
            label_path = Path(tmpdir) / "labels.csv"
            label_df.to_csv(label_path)
            
            # Create metadata
            metadata = pd.DataFrame({'random_attr': np.random.randn(200)})
            meta_path = Path(tmpdir) / "metadata.csv"
            metadata.to_csv(meta_path)
            
            output_path = Path(tmpdir) / "report.json"
            
            # Should pass (no correlation)
            result = verify_labels(
                embeddings_path=str(embed_path),
                labels_path=str(label_path),
                metadata_path=str(meta_path),
                output_path=str(output_path)
            )
            
            assert result is True
            assert output_path.exists()
            
            # Verify report contents
            with open(output_path) as f:
                report = json.load(f)
            assert report['verification_passed'] is True

    def test_verify_labels_fails_on_correlation(self):
        """Test that verification fails when correlation is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create embeddings with injected correlation
            n_samples = 400
            labels = np.random.randint(0, 2, n_samples)
            embeddings = np.random.randn(n_samples, 64)
            embeddings[:, 0] += labels * 3.0  # Strong correlation
            
            embed_df = pd.DataFrame({'embedding': list(embeddings)})
            embed_path = Path(tmpdir) / "embeddings.parquet"
            embed_df.to_parquet(embed_path)
            
            label_df = pd.DataFrame({'label': labels})
            label_path = Path(tmpdir) / "labels.csv"
            label_df.to_csv(label_path)
            
            result = verify_labels(
                embeddings_path=str(embed_path),
                labels_path=str(label_path),
                correlation_threshold=0.3,
                p_value_threshold=0.05
            )
            
            # Should fail due to correlation
            assert result is False

    def test_verify_labels_no_labels(self):
        """Test verification when labels are not provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            embeddings = np.random.randn(100, 32)
            embed_df = pd.DataFrame({'embedding': list(embeddings)})
            embed_path = Path(tmpdir) / "embeddings.parquet"
            embed_df.to_parquet(embed_path)
            
            # Should pass (no labels to check)
            result = verify_labels(
                embeddings_path=str(embed_path),
                labels_path=None
            )
            
            assert result is True

    def test_verify_labels_thresholds(self):
        """Test that thresholds correctly control sensitivity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            n_samples = 500
            labels = np.random.randint(0, 2, n_samples)
            embeddings = np.random.randn(n_samples, 64)
            # Inject moderate correlation
            embeddings[:, 0] += labels * 1.5
            
            embed_df = pd.DataFrame({'embedding': list(embeddings)})
            embed_path = Path(tmpdir) / "embeddings.parquet"
            embed_df.to_parquet(embed_path)
            
            label_df = pd.DataFrame({'label': labels})
            label_path = Path(tmpdir) / "labels.csv"
            label_df.to_csv(label_path)
            
            # Low threshold -> should detect
            result_low = verify_labels(
                embeddings_path=str(embed_path),
                labels_path=str(label_path),
                correlation_threshold=0.1
            )
            
            # High threshold -> might not detect
            result_high = verify_labels(
                embeddings_path=str(embed_path),
                labels_path=str(label_path),
                correlation_threshold=0.9
            )
            
            # With low threshold, should fail
            assert result_low is False
            # With high threshold, might pass
            # (depends on actual correlation strength)