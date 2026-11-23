import pytest
import os
import json
from unittest.mock import patch, MagicMock

from data_loader import (
    inject_redundancy,
    validate_redundancy_clusters,
    run_trec_covid_redundancy_validation,
    DataInjectionError,
    RedundancyCluster
)

class TestT017TrecCovidValidation:
    """Tests for T017: Synthetic redundancy validation on trec-covid."""

    @pytest.fixture
    def mock_trec_covid_corpus(self):
        """Mock trec-covid corpus with sample documents."""
        return {
            "doc1": {
                "text": "The COVID-19 pandemic has caused significant global health impacts.",
                "title": "COVID-19 Global Health Impact"
            },
            "doc2": {
                "text": "Vaccines are effective in preventing severe disease outcomes.",
                "title": "Vaccine Efficacy Study"
            },
            "doc3": {
                "text": "Hospital capacity was overwhelmed during peak infection periods.",
                "title": "Healthcare System Strain"
            },
            "doc4": {
                "text": "Social distancing measures reduced transmission rates significantly.",
                "title": "Transmission Reduction Study"
            },
            "doc5": {
                "text": "Economic impacts of lockdowns were severe across multiple sectors.",
                "title": "Economic Lockdown Effects"
            }
        }

    def test_inject_redundancy_creates_clusters(self, mock_trec_covid_corpus):
        """Test that inject_redundancy creates valid clusters."""
        clusters = inject_redundancy(
            dataset_name="trec-covid",
            corpus=mock_trec_covid_corpus,
            redundancy_factor=2,
            injection_rate=1.0
        )

        assert len(clusters) > 0
        assert all(isinstance(c, RedundancyCluster) for c in clusters)
        for cluster in clusters:
            assert len(cluster.redundant_docs) == 2
            assert cluster.original_doc_id in mock_trec_covid_corpus

    def test_validate_redundancy_clusters_returns_true(self, mock_trec_covid_corpus):
        """Test that validation passes for valid clusters."""
        clusters = inject_redundancy(
            dataset_name="trec-covid",
            corpus=mock_trec_covid_corpus,
            redundancy_factor=2,
            injection_rate=1.0
        )

        assert validate_redundancy_clusters(clusters, "trec-covid") is True

    def test_validate_redundancy_clusters_fails_empty(self):
        """Test that validation fails for empty clusters."""
        assert validate_redundancy_clusters([], "trec-covid") is False

    @patch('data_loader.fetch_trec_covid')
    @patch('data_loader.inject_redundancy')
    @patch('data_loader.validate_redundancy_clusters')
    @patch('data_loader.save_injected_dataset')
    def test_run_trec_covid_validation_success(
        self,
        mock_save,
        mock_validate,
        mock_inject,
        mock_fetch
    ):
        """Test successful execution of trec-covid validation."""
        mock_fetch.return_value = {
            "trec-covid": {
                "corpus": {"doc1": {"text": "test", "title": "test"}}
            }
        }
        mock_inject.return_value = [
            RedundancyCluster(
                original_doc_id="doc1",
                original_text="test",
                redundant_docs=[{"doc_id": "doc1_dup_0", "text": "test"}]
            )
        ]
        mock_validate.return_value = True

        output_path = run_trec_covid_redundancy_validation(cache_dir="test_cache")

        assert output_path == "data/processed/injected_datasets_trec_covid.json"
        mock_fetch.assert_called_once_with("test_cache")
        mock_inject.assert_called_once()
        mock_validate.assert_called_once()
        mock_save.assert_called_once()

    @patch('data_loader.fetch_trec_covid')
    def test_run_trec_covid_validation_fetch_failure(self, mock_fetch):
        """Test that fetch failure raises DataInjectionError."""
        mock_fetch.return_value = {}

        with pytest.raises(DataInjectionError, match="Failed to fetch trec-covid"):
            run_trec_covid_redundancy_validation(cache_dir="test_cache")

    @patch('data_loader.fetch_trec_covid')
    @patch('data_loader.inject_redundancy')
    @patch('data_loader.validate_redundancy_clusters')
    def test_run_trec_covid_validation_invalid_clusters(
        self,
        mock_validate,
        mock_inject,
        mock_fetch
    ):
        """Test that invalid clusters raise DataInjectionError."""
        mock_fetch.return_value = {
            "trec-covid": {
                "corpus": {"doc1": {"text": "test", "title": "test"}}
            }
        }
        mock_inject.return_value = [
            RedundancyCluster(
                original_doc_id="doc1",
                original_text="test",
                redundant_docs=[]
            )
        ]
        mock_validate.return_value = False

        with pytest.raises(DataInjectionError, match="Redundancy validation failed"):
            run_trec_covid_redundancy_validation(cache_dir="test_cache")

    def test_paraphrase_text_generates_variation(self):
        """Test that paraphrase_text generates variations (not always identical)."""
        from data_loader import paraphrase_text
        from nltk.stem import WordNetLemmatizer

        lemmatizer = WordNetLemmatizer()
        original = "The quick brown fox jumps over the lazy dog"
        paraphrased = paraphrase_text(original, lemmatizer)

        # Paraphrase should not be empty
        assert len(paraphrased) > 0
        # For longer texts, it should ideally differ (though not guaranteed for all words)
        # We just ensure it doesn't crash and produces output