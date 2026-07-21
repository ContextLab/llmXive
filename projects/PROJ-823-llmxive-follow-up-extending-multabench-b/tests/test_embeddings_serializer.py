import os
import tempfile
from pathlib import Path
import numpy as np
import pytest
import pandas as pd

from embeddings.serializer import (
    serialize_embeddings_to_parquet,
    load_embeddings_from_parquet,
    generate_run_id
)

class TestEmbeddingSerializer:
    def test_generate_run_id_format(self):
        """Test that run_id follows the expected format."""
        run_id = generate_run_id()
        assert run_id.startswith("run_")
        parts = run_id.split("_")
        assert len(parts) >= 3  # run, timestamp, salt
        
    def test_serialize_and_load_basic(self):
        """Test basic serialization and loading of embeddings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_embeddings.parquet"
            
            # Create test embeddings
            embeddings = [
                {
                    'dataset_id': 'dataset_a',
                    'sample_id': 'sample_1',
                    'embedding': np.array([0.1, 0.2, 0.3]),
                    'modality': 'image',
                    'model_name': 'clip_vit_b_32'
                },
                {
                    'dataset_id': 'dataset_b',
                    'sample_id': 'sample_2',
                    'embedding': np.array([0.4, 0.5, 0.6, 0.7]),
                    'modality': 'text',
                    'model_name': 'sentence_bert'
                }
            ]
            
            run_id = generate_run_id()
            
            # Serialize
            serialize_embeddings_to_parquet(embeddings, str(output_path), run_id)
            
            # Verify file exists
            assert output_path.exists()
            
            # Load back
            loaded = load_embeddings_from_parquet(str(output_path))
            
            # Verify count
            assert len(loaded) == 2
            
            # Verify data integrity
            assert loaded[0]['dataset_id'] == 'dataset_a'
            assert np.allclose(loaded[0]['embedding'], embeddings[0]['embedding'])
            assert loaded[0]['modality'] == 'image'
            assert loaded[0]['run_id'] == run_id
            
            assert loaded[1]['dataset_id'] == 'dataset_b'
            assert np.allclose(loaded[1]['embedding'], embeddings[1]['embedding'])
            assert loaded[1]['modality'] == 'text'
            
    def test_serialize_empty_list(self):
        """Test serialization of an empty embedding list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty_embeddings.parquet"
            
            run_id = generate_run_id()
            
            # Serialize empty list
            serialize_embeddings_to_parquet([], str(output_path), run_id)
            
            # Verify file exists
            assert output_path.exists()
            
            # Load back
            loaded = load_embeddings_from_parquet(str(output_path))
            
            # Verify empty result
            assert len(loaded) == 0
            
    def test_filter_by_run_id(self):
        """Test filtering embeddings by run_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "filtered_embeddings.parquet"
            
            # Create embeddings with different run_ids
            embeddings = [
                {
                    'dataset_id': 'dataset_a',
                    'sample_id': 'sample_1',
                    'embedding': np.array([0.1, 0.2]),
                    'modality': 'image',
                    'run_id': 'run_1'
                },
                {
                    'dataset_id': 'dataset_b',
                    'sample_id': 'sample_2',
                    'embedding': np.array([0.3, 0.4]),
                    'modality': 'text',
                    'run_id': 'run_2'
                }
            ]
            
            # Note: In real usage, run_id is added by serialize_embeddings_to_parquet
            # For this test, we simulate pre-existing run_ids
            
            # Serialize
            serialize_embeddings_to_parquet(embeddings, str(output_path), 'run_1')
            
            # Load with filter
            filtered = load_embeddings_from_parquet(
                str(output_path),
                filter_by_run_id='run_1'
            )
            
            # Verify only run_1 embeddings are returned
            assert len(filtered) == 1
            assert filtered[0]['run_id'] == 'run_1'
            
    def test_filter_by_dataset_id(self):
        """Test filtering embeddings by dataset_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "filtered_embeddings.parquet"
            
            embeddings = [
                {
                    'dataset_id': 'dataset_a',
                    'sample_id': 'sample_1',
                    'embedding': np.array([0.1, 0.2]),
                    'modality': 'image'
                },
                {
                    'dataset_id': 'dataset_a',
                    'sample_id': 'sample_2',
                    'embedding': np.array([0.3, 0.4]),
                    'modality': 'text'
                },
                {
                    'dataset_id': 'dataset_b',
                    'sample_id': 'sample_3',
                    'embedding': np.array([0.5, 0.6]),
                    'modality': 'image'
                }
            ]
            
            run_id = generate_run_id()
            serialize_embeddings_to_parquet(embeddings, str(output_path), run_id)
            
            # Load with dataset filter
            filtered = load_embeddings_from_parquet(
                str(output_path),
                filter_by_dataset_id='dataset_a'
            )
            
            # Verify only dataset_a embeddings are returned
            assert len(filtered) == 2
            assert all(e['dataset_id'] == 'dataset_a' for e in filtered)
            
    def test_metadata_preservation(self):
        """Test that additional metadata fields are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metadata_embeddings.parquet"
            
            embeddings = [
                {
                    'dataset_id': 'dataset_a',
                    'sample_id': 'sample_1',
                    'embedding': np.array([0.1, 0.2]),
                    'modality': 'image',
                    'model_name': 'custom_model',
                    'seed': 42,
                    'timestamp': '2024-01-01T00:00:00',
                    'extra_field': 'custom_value'
                }
            ]
            
            run_id = generate_run_id()
            serialize_embeddings_to_parquet(embeddings, str(output_path), run_id)
            
            loaded = load_embeddings_from_parquet(str(output_path))
            
            # Verify metadata preservation
            assert loaded[0]['model_name'] == 'custom_model'
            assert loaded[0]['seed'] == 42
            assert loaded[0]['timestamp'] == '2024-01-01T00:00:00'
            # Note: extra_field might not be preserved if not in schema, 
            # but standard fields should be
