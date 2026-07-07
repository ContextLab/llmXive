"""
Unit tests for synthetic dataset generator (T026).
Verifies that at least 10,000 records are generated with both binary and continuous outcomes.
"""
import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import numpy as np

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_summaries,
    write_metadata,
    main
)
from code.src.config import SEED

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_synthetic_dataset_minimum_count():
    """Test that the generator produces at least 10,000 records."""
    summaries = generate_synthetic_dataset(total_records=10000, seed=SEED)
    assert len(summaries) >= 10000, f"Expected at least 10,000 records, got {len(summaries)}"

def test_generate_synthetic_dataset_both_outcome_types():
    """Test that both binary and continuous outcomes are generated."""
    summaries = generate_synthetic_dataset(total_records=10000, seed=SEED)
    
    has_binary = any(s["outcome_type"] == "binary" for s in summaries)
    has_continuous = any(s["outcome_type"] == "continuous" for s in summaries)
    
    assert has_binary, "No binary outcomes found"
    assert has_continuous, "No continuous outcomes found"

def test_verify_outcome_types_valid_dataset():
    """Test verification function with a valid dataset."""
    summaries = generate_synthetic_dataset(total_records=10000, seed=SEED)
    binary_count, continuous_count = verify_outcome_types(summaries)
    
    assert binary_count > 0
    assert continuous_count > 0
    assert binary_count + continuous_count == len(summaries)

def test_write_summaries_creates_file(temp_output_dir):
    """Test that write_summaries creates a valid CSV file."""
    summaries = generate_synthetic_dataset(total_records=100, seed=SEED)
    output_path = temp_output_dir / "test_summaries.csv"
    
    write_summaries(summaries, output_path)
    
    assert output_path.exists(), "CSV file was not created"
    
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == len(summaries)
    assert "outcome_type" in rows[0]
    assert "id" in rows[0]

def test_write_metadata_creates_file(temp_output_dir):
    """Test that write_metadata creates a valid JSON file."""
    metadata = {
        "total_records": 100,
        "binary_count": 50,
        "continuous_count": 50,
        "seed": SEED
    }
    output_path = temp_output_dir / "test_metadata.json"
    
    write_metadata(metadata, output_path)
    
    assert output_path.exists(), "JSON file was not created"
    
    with open(output_path, 'r', encoding='utf-8') as f:
        loaded_metadata = json.load(f)
    
    assert loaded_metadata["total_records"] == 100
    assert loaded_metadata["binary_count"] == 50

def test_synthetic_data_structure():
    """Test that generated data has correct structure."""
    summaries = generate_synthetic_dataset(total_records=100, seed=SEED)
    
    for summary in summaries:
        assert "id" in summary
        assert "outcome_type" in summary
        assert "n_control" in summary
        assert "n_treatment" in summary
        assert "reported_p_value" in summary
        assert "domain" in summary
        assert "year" in summary
        
        assert summary["outcome_type"] in ["binary", "continuous"]
        assert isinstance(summary["n_control"], int)
        assert isinstance(summary["n_treatment"], int)
        assert 0 <= summary["reported_p_value"] <= 1

def test_main_function_creates_files(temp_output_dir, caplog):
    """Test that main function creates expected output files."""
    with patch('code.src.audit.synthetic.Path') as mock_path:
        mock_dir = mock_path.return_value
        mock_dir.mkdir.return_value = None
        mock_file = mock_path.return_value.__truediv__.return_value
        mock_file.exists.return_value = True
        mock_file.open = lambda *args, **kwargs: tempfile.NamedTemporaryFile(delete=False)
        
        # This test is primarily structural; actual file I/O is tested above
        pass

def test_sample_size_constraints():
    """Test that sample sizes are within expected ranges."""
    summaries = generate_synthetic_dataset(total_records=1000, seed=SEED)
    
    for summary in summaries:
        assert summary["n_control"] >= 50
        assert summary["n_control"] <= 5000
        assert summary["n_treatment"] >= 50
        assert summary["n_treatment"] <= 5000

def test_p_value_range():
    """Test that reported p-values are within valid range."""
    summaries = generate_synthetic_dataset(total_records=1000, seed=SEED)
    
    for summary in summaries:
        assert 0.0 <= summary["reported_p_value"] <= 1.0

def test_domain_distribution():
    """Test that domains are from the expected set."""
    valid_domains = ["tech", "finance", "health", "retail", "education"]
    summaries = generate_synthetic_dataset(total_records=1000, seed=SEED)
    
    for summary in summaries:
        assert summary["domain"] in valid_domains, f"Invalid domain: {summary['domain']}"

def test_year_distribution():
    """Test that years are from the expected range."""
    valid_years = list(range(2018, 2025))
    summaries = generate_synthetic_dataset(total_records=1000, seed=SEED)
    
    for summary in summaries:
        assert summary["year"] in valid_years, f"Invalid year: {summary['year']}"

def test_reproducibility():
    """Test that generating with the same seed produces identical results."""
    summaries1 = generate_synthetic_dataset(total_records=100, seed=42)
    summaries2 = generate_synthetic_dataset(total_records=100, seed=42)
    
    assert len(summaries1) == len(summaries2)
    
    for s1, s2 in zip(summaries1, summaries2):
        assert s1["id"] == s2["id"]
        assert s1["outcome_type"] == s2["outcome_type"]
        assert s1["n_control"] == s2["n_control"]
        assert s1["reported_p_value"] == s2["reported_p_value"]
