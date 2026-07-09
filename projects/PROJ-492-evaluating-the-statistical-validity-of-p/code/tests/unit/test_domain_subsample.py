import pytest
import csv
import json
from pathlib import Path
import tempfile
import os

from code.src.audit.domain_subsample import (
    load_audit_records_from_json,
    load_summaries_from_csv,
    extract_domain_from_record,
    calculate_domain_proportions,
    create_balanced_subsample,
    write_subsample_to_csv,
    run_domain_subsample
)

@pytest.fixture
def sample_records():
    """Create sample audit records with known domain distribution."""
    return [
        {"id": 1, "domain": "tech", "value": 0.5},
        {"id": 2, "domain": "tech", "value": 0.6},
        {"id": 3, "domain": "tech", "value": 0.7},
        {"id": 4, "domain": "tech", "value": 0.8},
        {"id": 5, "domain": "tech", "value": 0.9},
        {"id": 6, "domain": "health", "value": 0.4},
        {"id": 7, "domain": "health", "value": 0.5},
        {"id": 8, "domain": "finance", "value": 0.6},
        {"id": 9, "domain": "finance", "value": 0.7},
        {"id": 10, "domain": "education", "value": 0.8},
    ]

@pytest.fixture
def temp_json_file(sample_records):
    """Create a temporary JSON file with sample records."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_records, f)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_csv_file(sample_records):
    """Create a temporary CSV file with sample records."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        fieldnames = sample_records[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_records)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

def test_extract_domain_from_record():
    """Test domain extraction from various record formats."""
    # Standard domain field
    record1 = {"domain": "example.com", "other": "data"}
    assert extract_domain_from_record(record1) == "example.com"
    
    # Source domain field
    record2 = {"source_domain": "test.org", "other": "data"}
    assert extract_domain_from_record(record2) == "test.org"
    
    # URL extraction
    record3 = {"url": "https://news.site.com/article", "other": "data"}
    assert extract_domain_from_record(record3) == "news.site.com"
    
    # Missing domain
    record4 = {"id": 1}
    assert extract_domain_from_record(record4) == "unknown"

def test_calculate_domain_proportions(sample_records):
    """Test calculation of domain proportions."""
    proportions = calculate_domain_proportions(sample_records)
    
    assert len(proportions) == 4  # tech, health, finance, education
    assert abs(proportions["tech"] - 0.5) < 0.01  # 5/10
    assert abs(proportions["health"] - 0.2) < 0.01  # 2/10
    assert abs(proportions["finance"] - 0.2) < 0.01  # 2/10
    assert abs(proportions["education"] - 0.1) < 0.01  # 1/10

def test_create_balanced_subsample_no_violation():
    """Test subsampling when no domain exceeds threshold."""
    # All domains are <= 30%
    records = [
        {"id": 1, "domain": "a"},
        {"id": 2, "domain": "b"},
        {"id": 3, "domain": "c"},
    ]
    
    subsampled = create_balanced_subsample(records, max_domain_proportion=0.30)
    
    # All records should be preserved
    assert len(subsampled) == 3

def test_create_balanced_subsample_with_violation(sample_records):
    """Test subsampling when a domain exceeds threshold."""
    # tech domain is 50% (5/10), which exceeds 30%
    subsampled = create_balanced_subsample(sample_records, max_domain_proportion=0.30)
    
    # Total records should be reduced
    assert len(subsampled) < len(sample_records)
    
    # Tech should be at most 30%
    tech_count = sum(1 for r in subsampled if r["domain"] == "tech")
    tech_proportion = tech_count / len(subsampled)
    assert tech_proportion <= 0.30

def test_run_domain_subsample_json(temp_json_file):
    """Test running domain subsampling on JSON input."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_path = Path(f.name)
    
    try:
        original_count, subsampled_count, proportions = run_domain_subsample(
            temp_json_file, output_path, max_domain_proportion=0.30, input_format="json"
        )
        
        assert original_count == 10
        assert subsampled_count < original_count
        assert output_path.exists()
        
        # Verify no domain exceeds 30%
        for domain, prop in proportions.items():
            assert prop <= 0.30
    finally:
        if output_path.exists():
            os.unlink(output_path)

def test_run_domain_subsample_csv(temp_csv_file):
    """Test running domain subsampling on CSV input."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_path = Path(f.name)
    
    try:
        original_count, subsampled_count, proportions = run_domain_subsample(
            temp_csv_file, output_path, max_domain_proportion=0.30, input_format="csv"
        )
        
        assert original_count == 10
        assert subsampled_count < original_count
        assert output_path.exists()
        
        # Verify no domain exceeds 30%
        for domain, prop in proportions.items():
            assert prop <= 0.30
    finally:
        if output_path.exists():
            os.unlink(output_path)

def test_create_balanced_subsample_deterministic(sample_records):
    """Test that subsampling is deterministic with fixed seed."""
    # Run twice and compare results
    result1 = create_balanced_subsample(sample_records, max_domain_proportion=0.30)
    result2 = create_balanced_subsample(sample_records, max_domain_proportion=0.30)
    
    # Results should be identical due to seeded RNG
    ids1 = [r["id"] for r in result1]
    ids2 = [r["id"] for r in result2]
    assert ids1 == ids2
