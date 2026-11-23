import json
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from run_metabolomics_search import (
    search_metabolomics_workbench,
    search_by_analysis_type,
    DEFENSE_COMPOUND_KEYWORDS
)

class TestMetabolomicsSearch:
    """Contract tests for Metabolomics Workbench search functionality."""

    def test_search_metabolomics_workbench_connection(self):
        """Test that we can connect to Metabolomics Workbench API."""
        # This test verifies the API is reachable
        try:
            results = search_metabolomics_workbench(
                keywords=["test"],
                organism="Arabidopsis"
            )
            # Should return a list (possibly empty)
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"Failed to connect to Metabolomics Workbench: {e}")

    def test_search_returns_valid_structure(self):
        """Test that search results have expected structure."""
        results = search_metabolomics_workbench(
            keywords=["metabolite"],
            organism="Arabidopsis"
        )
        
        # Each result should be a dict with study ID
        for study in results:
            assert isinstance(study, dict)
            assert "study_id" in study or "Study_ID" in study

    def test_search_by_category(self):
        """Test searching by compound category."""
        results = search_by_analysis_type(
            compound_category="terpenoids",
            analysis_types=["LC-MS"],
            organism="Arabidopsis"
        )
        
        assert "LC-MS" in results
        assert isinstance(results["LC-MS"], list)

    def test_keywords_exist(self):
        """Test that defense compound keywords are defined."""
        assert "terpenoids" in DEFENSE_COMPOUND_KEYWORDS
        assert "alkaloids" in DEFENSE_COMPOUND_KEYWORDS
        assert "phenylpropanoids" in DEFENSE_COMPOUND_KEYWORDS

    def test_search_results_saved(self):
        """Test that search results can be saved and loaded."""
        from run_metabolomics_search import save_search_results
        
        test_results = {
            "LC-MS": [{"study_id": "TEST001"}]
        }
        
        output_path = Path(__file__).parent.parent.parent / "data" / "raw" / "test_search_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        save_search_results(
            test_results,
            str(output_path),
            {"test": True}
        )
        
        assert output_path.exists()
        
        with open(output_path) as f:
            loaded = json.load(f)
            
        assert "results" in loaded
        assert loaded["results"]["LC-MS"][0]["study_id"] == "TEST001"
        
        # Cleanup
        output_path.unlink()