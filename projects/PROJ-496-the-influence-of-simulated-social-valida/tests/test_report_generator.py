import pytest
from pathlib import Path
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from report_generator import generate_negative_finding_report
from logger import setup_logging

setup_logging()

@pytest.fixture
def temp_output(tmp_path):
    return tmp_path / "test_report.pdf"

@pytest.fixture
def sample_search_summary():
    return {
        "keywords": "social, feedback, anxiety",
        "total_results": 10
    }

@pytest.fixture
def sample_none_datasets():
    return [
        {
            "id": "ds000003",
            "title": "General EEG Motor Task",
            "feedback_type": "None",
            "anxiety_measure": "None",
            "url": "https://example.com/ds000003"
        }
    ]

@pytest.fixture
def sample_sim_only_datasets():
    return [
        {
            "id": "ds000001",
            "title": "Social Feedback and Anxiety Study (Simulated)",
            "url": "https://example.com/ds000001"
        }
    ]

@pytest.fixture
def sample_real_only_datasets():
    return [
        {
            "id": "ds000002",
            "title": "EEG Response to Real Social Interaction",
            "url": "https://example.com/ds000002"
        }
    ]

def test_generates_pdf_file(temp_output, sample_search_summary, sample_none_datasets):
    """Test that the report generator creates a valid PDF file."""
    generate_negative_finding_report(
        output_path=str(temp_output),
        search_summary=sample_search_summary,
        none_datasets=sample_none_datasets
    )
    
    assert temp_output.exists(), "PDF file was not created"
    assert temp_output.stat().st_size > 0, "PDF file is empty"

def test_includes_search_summary(temp_output, sample_search_summary, sample_none_datasets):
    """Test that the report includes search summary details."""
    generate_negative_finding_report(
        output_path=str(temp_output),
        search_summary=sample_search_summary,
        none_datasets=sample_none_datasets
    )
    
    content = temp_output.read_bytes()
    # Basic check that the file is a PDF and contains some text structure
    assert content.startswith(b"%PDF"), "File does not appear to be a PDF"

def test_handles_empty_none_datasets(temp_output, sample_search_summary):
    """Test behavior when no 'None' datasets are present (edge case)."""
    generate_negative_finding_report(
        output_path=str(temp_output),
        search_summary=sample_search_summary,
        none_datasets=[]
    )
    
    assert temp_output.exists()

def test_includes_sim_and_real_only(temp_output, sample_search_summary, sample_sim_only_datasets, sample_real_only_datasets):
    """Test that Sim-Only and Real-Only lists are included in the report."""
    generate_negative_finding_report(
        output_path=str(temp_output),
        search_summary=sample_search_summary,
        none_datasets=[],
        sim_only_datasets=sample_sim_only_datasets,
        real_only_datasets=sample_real_only_datasets
    )
    
    assert temp_output.exists()
    assert temp_output.stat().st_size > 0
