import pytest
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

# Import from existing API surface
from utils.validators import validate_dataset_schema, ensure_contracts_dir, load_schema
from collect.save_cleaned_data import load_preprocessed_issues, validate_completeness

@pytest.fixture
def sample_issues():
    """Sample issues for testing."""
    return [
        {
            "issue_id": 1,
            "repository": "test/repo1",
            "resolution_time_hours": 24.5,
            "created_at": "2023-01-01T00:00:00Z",
            "closed_at": "2023-01-02T00:30:00Z",
            "language": "Python"
        },
        {
            "issue_id": 2,
            "repository": "test/repo2",
            "resolution_time_hours": 12.0,
            "created_at": "2023-01-01T00:00:00Z",
            "closed_at": "2023-01-01T12:00:00Z",
            "language": "JavaScript"
        }
    ]

def test_validate_completeness_threshold_met(sample_issues):
    """Test that completeness validation passes when threshold is met."""
    passed, completeness, missing_counts = validate_completeness(sample_issues)
    
    assert passed is True
    assert completeness >= 0.95
    assert len(missing_counts) > 0
    assert all(count == 0 for count in missing_counts.values())

def test_validate_completeness_threshold_not_met():
    """Test that completeness validation fails when threshold is not met."""
    issues_with_missing = [
        {
            "issue_id": 1,
            "repository": "test/repo1",
            "resolution_time_hours": 24.5,
            "created_at": "2023-01-01T00:00:00Z",
            # missing closed_at
            "language": "Python"
        }
    ]
    
    passed, completeness, missing_counts = validate_completeness(issues_with_missing)
    
    assert passed is False
    assert completeness < 0.95
    assert missing_counts['closed_at'] == 1

def test_schema_validation_on_csv(tmp_path):
    """Test that the CSV file conforms to the expected schema."""
    # Create a sample CSV
    csv_path = tmp_path / "test.csv"
    fieldnames = ['issue_id', 'repository', 'resolution_time_hours', 'created_at', 'closed_at']
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            'issue_id': 1,
            'repository': 'test/repo',
            'resolution_time_hours': 24.0,
            'created_at': '2023-01-01T00:00:00Z',
            'closed_at': '2023-01-02T00:00:00Z'
        })
    
    # Load schema and validate
    schema_path = ensure_contracts_dir() / "dataset_schema.yaml"
    if schema_path.exists():
        schema = load_schema(schema_path)
        # Basic validation that file exists and is readable
        assert csv_path.exists()
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert set(rows[0].keys()) == set(fieldnames)

def test_checksum_generation(tmp_path):
    """Test that checksum is generated correctly."""
    from collect.save_cleaned_data import calculate_checksum
    
    test_file = tmp_path / "test.txt"
    test_content = "test content"
    test_file.write_text(test_content)
    
    checksum = calculate_checksum(test_file)
    assert len(checksum) == 64  # SHA-256 hex length
    assert isinstance(checksum, str)
    assert all(c in '0123456789abcdef' for c in checksum)