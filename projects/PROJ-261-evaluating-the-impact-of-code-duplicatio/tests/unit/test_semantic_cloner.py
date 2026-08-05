"""
Unit tests for semantic distance computation.
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path
import csv

from semantic_cloner import SemanticCloner, load_segment_data


class TestSemanticCloner:
    """Tests for the SemanticCloner class."""

    def test_initialization(self):
        """Test that SemanticCloner initializes correctly."""
        cloner = SemanticCloner()
        assert cloner.model is not None
        assert cloner.device in ["cpu", "cuda"]

    def test_compute_embeddings_empty(self):
        """Test embedding computation with empty input."""
        cloner = SemanticCloner()
        embeddings = cloner.compute_embeddings([])
        assert len(embeddings) == 0

    def test_compute_embeddings_single(self):
        """Test embedding computation with a single text."""
        cloner = SemanticCloner()
        texts = ["def hello(): pass"]
        embeddings = cloner.compute_embeddings(texts)
        assert embeddings.shape[0] == 1
        assert embeddings.shape[1] > 0  # Should have embedding dimensions

    def test_compute_cosine_similarity_empty(self):
        """Test cosine similarity with empty embeddings."""
        cloner = SemanticCloner()
        similarities = cloner.compute_cosine_similarity(np.array([]))
        assert len(similarities) == 0

    def test_compute_cosine_similarity_single(self):
        """Test cosine similarity with a single embedding."""
        cloner = SemanticCloner()
        embeddings = np.array([[1.0, 0.0, 0.0]])
        similarities = cloner.compute_cosine_similarity(embeddings)
        assert len(similarities) == 0  # Need at least 2 for pairwise

    def test_compute_cosine_similarity_two(self):
        """Test cosine similarity with two identical embeddings."""
        cloner = SemanticCloner()
        embeddings = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        similarities = cloner.compute_cosine_similarity(embeddings)
        assert len(similarities) == 1
        assert np.isclose(similarities[0], 1.0, atol=1e-5)

    def test_compute_cosine_similarity_opposite(self):
        """Test cosine similarity with opposite embeddings."""
        cloner = SemanticCloner()
        embeddings = np.array([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
        similarities = cloner.compute_cosine_similarity(embeddings)
        assert len(similarities) == 1
        assert np.isclose(similarities[0], -1.0, atol=1e-5)

    def test_compute_semantic_distance_batch(self):
        """Test full semantic distance computation batch."""
        cloner = SemanticCloner()
        
        segment_ids = ["seg1", "seg2", "seg3"]
        code_texts = [
            "def hello(): pass",
            "def hello(): pass",  # Identical
            "def world(): pass"   # Different
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_semantic.csv"
            result_path = cloner.compute_semantic_distance_batch(
                segment_ids, code_texts, output_path
            )
            
            assert result_path.exists()
            
            with open(result_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2  # n-1 distances for n segments
                assert 'segment_id' in rows[0]
                assert 'semantic_distance' in rows[0]
                assert 'similarity' in rows[0]
                
                # First pair should be identical (distance ~ 0)
                assert float(rows[0]['semantic_distance']) < 0.1
                assert float(rows[0]['similarity']) > 0.9

    def test_compute_semantic_distance_batch_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        cloner = SemanticCloner()
        
        with pytest.raises(ValueError):
            cloner.compute_semantic_distance_batch(
                ["seg1", "seg2"],  # 2 segments
                ["code1"],         # 1 text
                Path("/tmp/test.csv")
            )

class TestLoadSegmentData:
    """Tests for load_segment_data function."""

    def test_load_from_clone_metrics_format(self):
        """Test loading data in clone_metrics.csv format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['segment_id', 'code', 'clone_density'])
            writer.writerow(['seg1', 'def foo(): pass', '0.5'])
            writer.writerow(['seg2', 'def bar(): pass', '0.3'])
            temp_path = Path(f.name)
        
        try:
            segment_ids, code_texts = load_segment_data(temp_path)
            assert len(segment_ids) == 2
            assert segment_ids == ['seg1', 'seg2']
            assert code_texts == ['def foo(): pass', 'def bar(): pass']
        finally:
            temp_path.unlink()

    def test_load_from_generic_format(self):
        """Test loading data with 'id' instead of 'segment_id'."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'code'])
            writer.writerow(['id1', 'x = 1'])
            writer.writerow(['id2', 'y = 2'])
            temp_path = Path(f.name)
        
        try:
            segment_ids, code_texts = load_segment_data(temp_path)
            assert len(segment_ids) == 2
            assert segment_ids == ['id1', 'id2']
        finally:
            temp_path.unlink()

    def test_load_empty_file(self):
        """Test loading an empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['segment_id', 'code'])  # Header only
            temp_path = Path(f.name)
        
        try:
            segment_ids, code_texts = load_segment_data(temp_path)
            assert len(segment_ids) == 0
        finally:
            temp_path.unlink()
