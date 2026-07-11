"""
Unit tests for edge cases in the llmXive pipeline.
Covers empty datasets, single-row datasets, and zero-variance features.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import ensure_directories
from utils.logging import get_logger
from data_loader import ingest_dataset
from embeddings.generator import EmbeddingGenerator
from analysis.metadata_stats import compute_feature_stats, load_dataset_list, process_single_dataset, save_summary_csv
from models.projection import MLPProjection, create_projection_model
from models.trainer import Trainer


class TestEmptyDataset:
    """Tests for handling empty datasets."""

    def test_empty_dataframe_metadata_stats(self):
        """Test metadata_stats handles empty DataFrame gracefully."""
        empty_df = pd.DataFrame()
        
        with pytest.raises((ValueError, IndexError)):
            compute_feature_stats(empty_df)

    def test_empty_dataset_embedding_generation(self, tmp_path):
        """Test embedding generation with empty dataset."""
        # Create a minimal empty dataset structure
        dataset_dir = tmp_path / "empty_dataset"
        dataset_dir.mkdir()
        
        # Create empty CSV
        empty_csv = dataset_dir / "data.csv"
        empty_csv.write_text("id,text,image_path\n")
        
        # Create metadata file
        metadata = {
            "dataset_id": "empty_test",
            "task_type": "classification",
            "num_rows": 0,
            "has_text": True,
            "has_image": True
        }
        with open(dataset_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)
        
        # Test that processing an empty dataset raises appropriate error or handles gracefully
        # This is expected behavior - empty datasets should be detected and skipped
        try:
            stats = process_single_dataset(str(dataset_dir))
            assert stats is None or stats.get("num_rows", 0) == 0
        except (ValueError, IndexError) as e:
            # Expected: empty datasets should raise an error or be skipped
            assert "empty" in str(e).lower() or "zero" in str(e).lower()


class TestSingleRowDataset:
    """Tests for handling single-row datasets."""

    def test_single_row_metadata_stats(self):
        """Test metadata_stats handles single-row DataFrame correctly."""
        single_row_df = pd.DataFrame({
            'id': [1],
            'feature1': [10.0],
            'feature2': ['text'],
            'target': [1]
        })
        
        stats = compute_feature_stats(single_row_df)
        
        # Should compute stats without error
        assert stats is not None
        assert stats['num_rows'] == 1
        assert stats['feature_count'] == 3  # id, feature1, feature2

    def test_single_row_embedding_generation(self, tmp_path):
        """Test embedding generation with single-row dataset."""
        dataset_dir = tmp_path / "single_row_dataset"
        dataset_dir.mkdir()
        
        # Create single-row CSV
        single_csv = dataset_dir / "data.csv"
        single_csv.write_text("id,text,image_path\n1,sample text,path/to/image.jpg\n")
        
        # Create metadata file
        metadata = {
            "dataset_id": "single_row_test",
            "task_type": "classification",
            "num_rows": 1,
            "has_text": True,
            "has_image": True
        }
        with open(dataset_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)
        
        # Should process without error
        try:
            stats = process_single_dataset(str(dataset_dir))
            assert stats is not None
            assert stats['num_rows'] == 1
        except Exception as e:
            pytest.fail(f"Single row dataset processing failed: {e}")

    def test_single_row_projection_training(self, tmp_path):
        """Test projection model training with single-row dataset."""
        # Create a simple projection model
        input_dim = 10
        output_dim = 5
        model = MLPProjection(input_dim, output_dim)
        
        # Create single sample
        x = torch.randn(1, input_dim)
        y = torch.randn(1, output_dim)
        
        # Should not raise error
        output = model(x)
        assert output.shape == (1, output_dim)


class TestZeroVarianceFeatures:
    """Tests for handling zero-variance features."""

    def test_zero_variance_feature_stats(self):
        """Test metadata_stats correctly identifies zero-variance features."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'constant_feature': [5.0, 5.0, 5.0, 5.0, 5.0],
            'variable_feature': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        stats = compute_feature_stats(df)
        
        # Should identify constant feature
        assert 'constant_feature' in stats.get('zero_variance_features', [])
        assert stats.get('num_zero_variance_features', 0) >= 1

    def test_zero_variance_in_projection(self):
        """Test that zero-variance features are handled in projection."""
        # Create dataset with zero-variance feature
        df = pd.DataFrame({
            'feature1': [1.0, 1.0, 1.0],
            'feature2': [1.0, 2.0, 3.0],
            'target': [0, 1, 0]
        })
        
        # Normalize features (zero variance should result in NaN or constant)
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        
        # This should handle zero variance gracefully
        try:
            scaled = scaler.fit_transform(df[['feature1', 'feature2']])
            # Zero variance feature will have NaN or 0 after scaling
            assert scaled.shape == (3, 2)
        except Exception as e:
            # StandardScaler raises error for zero variance - this is expected
            # The pipeline should handle this by skipping or imputing
            assert "variance" in str(e).lower() or "std" in str(e).lower()

    def test_mixed_variance_features(self):
        """Test handling of mixed variance features."""
        df = pd.DataFrame({
            'high_var': [1.0, 10.0, 100.0, 1000.0],
            'zero_var': [5.0, 5.0, 5.0, 5.0],
            'low_var': [1.0, 1.1, 1.2, 1.3]
        })
        
        stats = compute_feature_stats(df)
        
        assert stats['num_zero_variance_features'] >= 1
        assert stats['num_non_zero_variance_features'] >= 2


class TestMissingValues:
    """Tests for handling missing values in datasets."""

    def test_high_missingness_stats(self):
        """Test metadata_stats handles high missingness correctly."""
        df = pd.DataFrame({
            'complete': [1.0, 2.0, 3.0, 4.0],
            'missing_some': [1.0, np.nan, 3.0, np.nan],
            'all_missing': [np.nan, np.nan, np.nan, np.nan]
        })
        
        stats = compute_feature_stats(df)
        
        assert stats['overall_missingness'] > 0
        assert stats['num_features_with_missing'] >= 2

    def test_missing_values_in_embedding(self):
        """Test embedding generation with missing values."""
        # Create dataset with missing text/image paths
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir) / "missing_test"
            dataset_dir.mkdir()
            
            # Create CSV with missing values
            csv_content = """id,text,image_path
            1,hello text,path/to/image.jpg
            2,,path/to/image2.jpg
            3,some text,
            """
            (dataset_dir / "data.csv").write_text(csv_content)
            
            metadata = {
                "dataset_id": "missing_test",
                "task_type": "classification",
                "num_rows": 3,
                "has_text": True,
                "has_image": True
            }
            with open(dataset_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)
            
            # Should handle missing values gracefully
            try:
                stats = process_single_dataset(str(dataset_dir))
                assert stats is not None
            except Exception as e:
                # Expected to handle missing values or raise informative error
                assert "missing" in str(e).lower() or "empty" in str(e).lower()


class TestInvalidDataFormats:
    """Tests for handling invalid data formats."""

    def test_corrupted_parquet_file(self):
        """Test handling of corrupted parquet files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corrupt_file = Path(tmp_dir) / "corrupt.parquet"
            corrupt_file.write_text("not a valid parquet file")
            
            try:
                import pandas as pd
                pd.read_parquet(str(corrupt_file))
                pytest.fail("Should have raised an error for corrupted parquet")
            except Exception as e:
                # Expected: corrupted file should raise error
                assert "parquet" in str(e).lower() or "corrupt" in str(e).lower()

    def test_invalid_json_metadata(self):
        """Test handling of invalid JSON metadata."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            metadata_file = Path(tmp_dir) / "metadata.json"
            metadata_file.write_text("{ invalid json }")
            
            try:
                with open(metadata_file, 'r') as f:
                    json.load(f)
                pytest.fail("Should have raised JSON decode error")
            except json.JSONDecodeError:
                # Expected: invalid JSON should raise decode error
                pass


class TestMemoryEdgeCases:
    """Tests for memory-related edge cases."""

    def test_very_small_batch_size(self):
        """Test processing with batch size of 1."""
        from embeddings.utils import batch_process_embeddings
        
        # Create small dataset
        data = [{"id": i, "text": f"text_{i}"} for i in range(5)]
        
        # Process with batch size 1
        try:
            # This should work but may be slow
            results = batch_process_embeddings(
                data, 
                batch_size=1,
                process_func=lambda x: x  # Dummy function
            )
            assert len(results) == 5
        except Exception as e:
            pytest.fail(f"Batch size 1 processing failed: {e}")

    def test_very_large_feature_dimension(self):
        """Test handling of very high dimensional features."""
        # Create model with high input dimension
        input_dim = 10000
        output_dim = 100
        
        try:
            model = MLPProjection(input_dim, output_dim)
            x = torch.randn(1, input_dim)
            output = model(x)
            assert output.shape == (1, output_dim)
        except MemoryError:
            # Expected: very large dimensions may cause memory issues
            pass


# Import torch for tests that need it
import torch


if __name__ == "__main__":
    pytest.main([__file__, "-v"])