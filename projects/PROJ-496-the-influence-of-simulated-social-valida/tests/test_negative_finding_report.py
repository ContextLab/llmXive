import pytest
from pathlib import Path
import csv
import os
import sys

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from generate_negative_finding_report import load_search_results
from report_generator import generate_negative_finding_report

@pytest.fixture
def temp_csv(tmp_path):
    """Create a temporary CSV file with test data."""
    csv_file = tmp_path / "test_search_results.csv"
    data = [
        {"dataset_id": "ds001", "title": "Social Feedback Study", "feedback_type": "simulated", "anxiety_measure": "LSAS", "status": "Eligible", "url": "http://example.com/ds001"},
        {"dataset_id": "ds002", "title": "Anxiety Only Study", "feedback_type": "None", "anxiety_measure": "SPIN", "status": "None", "url": "http://example.com/ds002"},
        {"dataset_id": "ds003", "title": "Feedback Only Study", "feedback_type": "real", "anxiety_measure": "None", "status": "None", "url": "http://example.com/ds003"},
        {"dataset_id": "ds004", "title": "No Relevance", "feedback_type": "None", "anxiety_measure": "None", "status": "None", "url": "http://example.com/ds004"},
    ]
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return str(csv_file)

def test_load_search_results(temp_csv):
    """Test loading search results from CSV."""
    datasets = load_search_results(temp_csv)
    assert len(datasets) == 4
    assert datasets[0]["dataset_id"] == "ds001"
    assert datasets[1]["status"] == "None"

def test_generate_negative_finding_report_none(tmp_path):
    """Test generating a 'None' status negative finding report."""
    csv_file = tmp_path / "test_search_results.csv"
    data = [
        {"dataset_id": "ds002", "title": "Anxiety Only Study", "feedback_type": "None", "anxiety_measure": "SPIN", "status": "None", "url": "http://example.com/ds002"},
    ]
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    none_datasets = [d for d in data if d['status'] == 'None']
    search_summary = {
        "total_datasets_searched": 1,
        "none_status_count": 1,
        "search_keywords": ["social", "feedback"],
        "data_gap_statement": "Test data gap statement."
    }
    
    output_pdf = tmp_path / "test_report.pdf"
    generate_negative_finding_report(
        output_path=str(output_pdf),
        search_summary=search_summary,
        none_datasets=none_datasets,
        report_type="none"
    )
    
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0

def test_generate_negative_finding_report_empty(tmp_path):
    """Test generating a report with no 'None' status datasets."""
    search_summary = {
        "total_datasets_searched": 1,
        "none_status_count": 0,
        "search_keywords": ["social"],
        "data_gap_statement": "No gap."
    }
    
    output_pdf = tmp_path / "test_report_empty.pdf"
    generate_negative_finding_report(
        output_path=str(output_pdf),
        search_summary=search_summary,
        none_datasets=[],
        report_type="none"
    )
    
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0
