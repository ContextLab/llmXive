"""
Contract test for Metabolomics Workbench search functionality (Task T013).

Verifies that the search module correctly queries the Metabolomics Workbench API
and returns structured metadata for defense-related metabolite experiments.
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.run_metabolomics_search import search_metabolomics_workbench, save_search_results
from code.exceptions import E_DATASET


class TestMetabolomicsSearch:
    """Contract tests for T013 Metabolomics Workbench search."""

    @pytest.fixture
    def mock_response(self):
        """Mock successful API response."""
        return Mock(
            status_code=200,
            json=Mock(return_value=[
                {
                    "STUDY_ID": "MW_STUDY_001",
                    "STUDY_TITLE": "Arabidopsis herbivore stress metabolomics",
                    "ORGANISM": "Arabidopsis thaliana",
                    "TREATMENT": "Herbivore infestation",
                    "SAMPLE_COUNT": 24,
                    "METABOLITE_COUNT": 150
                },
                {
                    "STUDY_ID": "MW_STUDY_002",
                    "STUDY_TITLE": "Solanum lycopersicum alkaloid profiling",
                    "ORGANISM": "Solanum lycopersicum",
                    "TREATMENT": "Insect attack",
                    "SAMPLE_COUNT": 18,
                    "METABOLITE_COUNT": 85
                }
            ])
        )

    @pytest.fixture
    def mock_session(self):
        """Mock requests session."""
        session = Mock()
        session.get = Mock(return_value=Mock())
        return session

    def test_search_returns_list(self, mock_response, mock_session):
        """Test that search returns a list of study metadata."""
        with patch('code.run_metabolomics_search.create_session', return_value=mock_session):
            mock_session.get.return_value = mock_response
            
            results = search_metabolomics_workbench(["terpenoid", "alkaloid"])
            
            assert isinstance(results, list)
            assert len(results) > 0

    def test_search_result_structure(self, mock_response, mock_session):
        """Test that each result has required metadata fields."""
        with patch('code.run_metabolomics_search.create_session', return_value=mock_session):
            mock_session.get.return_value = mock_response
            
            results = search_metabolomics_workbench(["terpenoid"])
            
            if results:
                required_fields = [
                    "study_id", "title", "organism", 
                    "treatment", "sample_count", "database", "source_url"
                ]
                for result in results:
                    for field in required_fields:
                        assert field in result, f"Missing field: {field}"

    def test_search_filters_by_keywords(self, mock_response, mock_session):
        """Test that results are filtered by defense keywords."""
        with patch('code.run_metabolomics_search.create_session', return_value=mock_session):
            mock_session.get.return_value = mock_response
            
            results = search_metabolomics_workbench(["defense", "stress"])
            
            # All results should contain defense-related terms
            for result in results:
                combined_text = f"{result['title']} {result['treatment']}".lower()
                assert any(kw in combined_text for kw in ["terpen", "alkaloid", "phenylprop", "defense", "herbivore", "stress"])

    def test_save_results_creates_file(self, tmp_path):
        """Test that save_search_results creates a valid JSON file."""
        test_results = [
            {
                "study_id": "TEST_001",
                "title": "Test Study",
                "organism": "Arabidopsis",
                "treatment": "Stress",
                "sample_count": 10,
                "database": "MW",
                "source_url": "http://test"
            }
        ]
        
        output_file = tmp_path / "test_results.json"
        save_search_results(test_results, output_file)
        
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert "search_date" in data
        assert "results" in data
        assert len(data["results"]) == 1

    def test_empty_search_returns_empty_list(self, mock_session):
        """Test handling of empty search results."""
        empty_response = Mock(
            status_code=200,
            json=Mock(return_value=[])
        )
        
        with patch('code.run_metabolomics_search.create_session', return_value=mock_session):
            mock_session.get.return_value = empty_response
            
            results = search_metabolomics_workbench(["nonexistent_compound_xyz"])
            
            assert results == []

    def test_api_error_raises_exception(self, mock_session):
        """Test that API errors raise E_DATASET."""
        error_response = Mock(
            status_code=500,
            raise_for_status=Mock(side_effect=Exception("API Error"))
        )
        
        with patch('code.run_metabolomics_search.create_session', return_value=mock_session):
            mock_session.get.return_value = error_response
            
            with pytest.raises(E_DATASET):
                search_metabolomics_workbench(["test"])
