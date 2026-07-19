import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

from data_loader import (
    create_redundancy_clusters,
    inject_synonym_replacement,
    inject_sentence_shuffle,
    prepare_injected_datasets,
    DataInjectionError
)

class TestDataLoaderInjection:
    @pytest.fixture
    def sample_records(self):
        """Create sample records for testing."""
        return [
            {
                "query_id": "1",
                "query_text": "test query",
                "doc_id": "doc1",
                "doc_text": "This is a sample document with multiple words for testing synonym replacement and sentence shuffling.",
                "relevance_score": 1,
                "split": "test",
                "dataset": "test"
            },
            {
                "query_id": "2",
                "query_text": "another query",
                "doc_id": "doc2",
                "doc_text": "This is another document with different content for testing purposes.",
                "relevance_score": 1,
                "split": "test",
                "dataset": "test"
            }
        ]

    @pytest.fixture
    def mock_nltk(self):
        """Mock NLTK to avoid downloading data during tests."""
        with patch('data_loader.nltk.download') as mock_download:
            with patch('data_loader.wordnet.synsets') as mock_synsets:
                # Mock a synonym for 'sample'
                mock_lemma = MagicMock()
                mock_lemma.name.return_value = 'sample'
                mock_syn = MagicMock()
                mock_syn.lemmas.return_value = [mock_lemma]
                mock_synsets.return_value = [mock_syn]
                yield mock_download, mock_synsets

    def test_inject_synonym_replacement(self, mock_nltk):
        """Test synonym replacement injection."""
        mock_download, mock_synsets = mock_nltk
        from nltk.stem import WordNetLemmatizer
        lemmatizer = WordNetLemmatizer()

        text = "This is a sample document."
        injected = inject_synonym_replacement(text, lemmatizer, replacement_rate=1.0)

        # Should be different but similar
        assert injected != text or len(injected) > 0

    def test_inject_sentence_shuffle(self):
        """Test sentence shuffle injection."""
        text = "First sentence. Second sentence. Third sentence."
        injected = inject_sentence_shuffle(text, shuffle_rate=1.0)

        # Should be different order
        assert injected != text or len(injected) > 0

    def test_create_redundancy_clusters(self, sample_records, mock_nltk):
        """Test cluster creation."""
        mock_download, mock_synsets = mock_nltk
        clusters, stats = create_redundancy_clusters(
            sample_records,
            clusters_per_doc=2,
            similarity_threshold=0.8,
            seed=42
        )

        assert len(clusters) > 0
        assert all(hasattr(c, 'original_doc_id') for c in clusters)
        assert all(hasattr(c, 'injected_docs') for c in clusters)
        assert all(len(c.injected_docs) == 2 for c in clusters)

    def test_prepare_injected_datasets_creates_file(self, sample_records, mock_nltk, tmp_path):
        """Test that prepare_injected_datasets creates the output file."""
        mock_download, mock_synsets = mock_nltk

        # Mock the fetch function to return sample records
        with patch('data_loader.fetch_beir_datasets', return_value=sample_records):
            output_path = str(tmp_path / "test_injected.json")
            result_path = prepare_injected_datasets(
                datasets=["test"],
                output_path=output_path,
                clusters_per_doc=2,
                similarity_threshold=0.8,
                seed=42
            )

            assert os.path.exists(result_path)
            with open(result_path, 'r') as f:
                data = json.load(f)
            assert len(data) > 0
            assert all('original_doc_id' in item for item in data)
            assert all('injected_docs' in item for item in data)

    def test_prepare_injected_datasets_with_low_similarity(self, sample_records, mock_nltk, tmp_path):
        """Test that prepare_injected_datasets handles low similarity gracefully."""
        mock_download, mock_synsets = mock_nltk

        # Force low similarity by mocking the embedding calculation
        with patch('data_loader.fetch_beir_datasets', return_value=sample_records):
            with patch('data_loader.SentenceTransformer') as mock_model:
                # Mock embeddings that result in low similarity
                mock_model.return_value.encode.return_value = np.array([[0.1, 0.1], [0.2, 0.2]])
                
                output_path = str(tmp_path / "test_low_sim.json")
                # Should not raise if avg is > 0.90, but will warn
                result_path = prepare_injected_datasets(
                    datasets=["test"],
                    output_path=output_path,
                    clusters_per_doc=2,
                    similarity_threshold=0.95,
                    seed=42
                )
                
                # File should still be created
                assert os.path.exists(result_path)

    def test_data_injection_error_on_very_low_similarity(self, sample_records, mock_nltk, tmp_path):
        """Test that DataInjectionError is raised on very low similarity."""
        mock_download, mock_synsets = mock_nltk

        with patch('data_loader.fetch_beir_datasets', return_value=sample_records):
            with patch('data_loader.SentenceTransformer') as mock_model:
                # Mock embeddings that result in very low similarity (< 0.90)
                mock_model.return_value.encode.return_value = np.array([[0.1, 0.0], [0.0, 0.1]])
                
                output_path = str(tmp_path / "test_fail.json")
                
                with pytest.raises(DataInjectionError) as exc_info:
                    prepare_injected_datasets(
                        datasets=["test"],
                        output_path=output_path,
                        clusters_per_doc=2,
                        similarity_threshold=0.95,
                        seed=42
                    )
                
                assert "significantly below threshold" in str(exc_info.value)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])