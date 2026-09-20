"""
Unit tests for the conditional synthesis logic (T033).
Tests the logic that suppresses meta-analysis if N < 10 and triggers descriptive synthesis.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the function to test
from code.analysis.conditional_synthesis import check_sample_size_and_route, MIN_SUBGROUP_SIZE

@pytest.fixture
def temp_csv_dir():
    """Creates a temporary directory with a mock CSV file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "cleaned_studies.csv"
        # Create a minimal valid CSV
        data = {
            "id": [f"study_{i}" for i in range(5)],
            "title": ["Study " + str(i) for i in range(5)],
            "registry": ["ClinicalTrials.gov"] * 5,
            "age_range": ["8-12"] * 5,
            "diagnosis": ["ASD"] * 5,
            "outcomes": ["SRS-2"] * 5,
            "intervention_components": ["breathing"] * 5,
            "delivery_format": ["caregiver-mediated"] * 5,
            "follow_up": ["3m"] * 5,
            "abstract_text": [None] * 5,
            "social_skill_domain": ["emotional regulation"] * 5
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        yield str(csv_path)
        # Cleanup handled by context manager

def test_small_sample_size_triggers_synthesis(temp_csv_dir):
    """
    Test that when N < 10, the function returns proceed_meta_analysis=False
    and generates a synthesis report.
    """
    with tempfile.TemporaryDirectory() as tmp_docs:
        output_path = os.path.join(tmp_docs, "test_synthesis.md")
        
        result = check_sample_size_and_route(
            cleaned_studies_path=temp_csv_dir,
            output_doc_path=output_path
        )
        
        assert result["n_studies"] == 5
        assert result["proceed_meta_analysis"] is False
        assert "synthesis_report_path" in result
        assert os.path.exists(result["synthesis_report_path"])
        
        # Verify content contains expected sections
        with open(result["synthesis_report_path"], 'r') as f:
            content = f.read()
            assert "Descriptive Synthesis" in content
            assert "N < 10" in content or "insufficient" in content.lower()

def test_large_sample_size_allows_meta_analysis(temp_csv_dir):
    """
    Test that when N >= 10, the function returns proceed_meta_analysis=True
    and does NOT generate a synthesis report.
    """
    # Create a CSV with 15 rows
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "cleaned_studies.csv"
        data = {
            "id": [f"study_{i}" for i in range(15)],
            "title": ["Study " + str(i) for i in range(15)],
            "registry": ["ClinicalTrials.gov"] * 15,
            "age_range": ["8-12"] * 15,
            "diagnosis": ["ASD"] * 15,
            "outcomes": ["SRS-2"] * 15,
            "intervention_components": ["breathing"] * 15,
            "delivery_format": ["caregiver-mediated"] * 15,
            "follow_up": ["3m"] * 15,
            "abstract_text": [None] * 15,
            "social_skill_domain": ["emotional regulation"] * 15
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        with tempfile.TemporaryDirectory() as tmp_docs:
            output_path = os.path.join(tmp_docs, "test_synthesis.md")
            
            result = check_sample_size_and_route(
                cleaned_studies_path=str(csv_path),
                output_doc_path=output_path
            )
            
            assert result["n_studies"] == 15
            assert result["proceed_meta_analysis"] is True
            assert "synthesis_report_path" not in result
            assert not os.path.exists(output_path)

def test_missing_csv_raises_error():
    """Test that a missing CSV file raises FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmp_docs:
        output_path = os.path.join(tmp_docs, "test_synthesis.md")
        with pytest.raises(FileNotFoundError):
            check_sample_size_and_route(
                cleaned_studies_path="/nonexistent/path.csv",
                output_doc_path=output_path
            )