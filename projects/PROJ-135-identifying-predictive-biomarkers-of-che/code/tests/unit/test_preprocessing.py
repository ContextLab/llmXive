"""
Unit tests for preprocessing harmonization logic (T015).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os
import sys

# Add the code directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.preprocessing import (
    harmonize_gene_ids,
    filter_low_coverage_dataset,
    process_tumor_type_harmonization,
    MIN_COVERAGE_THRESHOLD
)
from src.config import get_project_root

# Mock MyGeneInfo to avoid API calls during testing
class MockMyGeneInfo:
    def querymany(self, queries, scopes, fields, species, returnall=False):
        # Simulate successful mapping for some, failure for others
        results = []
        for q in queries:
            if q.startswith("ENSG") or q.startswith("1"):
                results.append({"query": q, "symbol": f"GENE_{q}"})
            else:
                # Simulate unmapped
                pass
        return results


@pytest.fixture
def sample_counts():
    """Create a sample DataFrame with gene IDs."""
    data = {
        "gene_id": ["ENSG000001", "ENSG000002", "1000", "2000", "UNKNOWN"],
        "sample1": [10, 20, 5, 15, 0],
        "sample2": [12, 22, 6, 16, 1],
        "response": [1, 0, 1, 0, 1]
    }
    return pd.DataFrame(data)


def test_harmonize_gene_ids(sample_counts):
    """Test that gene IDs are mapped to HGNC symbols."""
    # We need to patch the MyGeneInfo class in the module
    import src.preprocessing as prep_module
    original_mg = prep_module.MyGeneInfo

    # Replace with mock
    prep_module.MyGeneInfo = MockMyGeneInfo

    try:
        df_harmonized, coverage, mapped, total = harmonize_gene_ids(sample_counts)

        # Check that the column was updated
        assert "GENE_ENSG000001" in df_harmonized["gene_id"].values
        assert "GENE_1000" in df_harmonized["gene_id"].values
        assert np.nan in df_harmonized["gene_id"].values # For UNKNOWN

        # Check coverage calculation (4 mapped out of 5)
        assert coverage == pytest.approx(0.8)
        assert mapped == 4
        assert total == 5
    finally:
        # Restore original class
        prep_module.MyGeneInfo = original_mg


def test_filter_low_coverage_dataset_valid(sample_counts):
    """Test that a dataset with >= 95% coverage is accepted."""
    # Create a mock dataset with 100% coverage
    data = {
        "gene_id": ["ENSG000001", "ENSG000002"],
        "sample1": [10, 20],
        "sample2": [12, 22]
    }
    df = pd.DataFrame(data)

    # Mock MyGeneInfo for this test
    import src.preprocessing as prep_module
    original_mg = prep_module.MyGeneInfo
    prep_module.MyGeneInfo = MockMyGeneInfo

    try:
        # First harmonize to get valid counts
        df_harm, cov, m, t = harmonize_gene_ids(df)
        # In mock, both map -> 100%
        assert cov == 1.0

        # Now test filter
        is_valid = filter_low_coverage_dataset(df_harm, "TEST_TUMOR", cov, m, t)
        assert is_valid is True
    finally:
        prep_module.MyGeneInfo = original_mg


def test_filter_low_coverage_dataset_invalid(sample_counts, tmp_path):
    """Test that a dataset with < 95% coverage is rejected and gate is updated."""
    # Create a mock dataset with 50% coverage
    data = {
        "gene_id": ["ENSG000001", "UNKNOWN"],
        "sample1": [10, 20],
        "sample2": [12, 22]
    }
    df = pd.DataFrame(data)

    import src.preprocessing as prep_module
    original_mg = prep_module.MyGeneInfo
    prep_module.MyGeneInfo = MockMyGeneInfo

    # Mock the update_feasibility_gate to capture the call
    original_update = prep_module.update_feasibility_gate
    captured_call = {}

    def mock_update(status, reason, details=None):
        captured_call["status"] = status
        captured_call["reason"] = reason
        captured_call["details"] = details

    prep_module.update_feasibility_gate = mock_update

    try:
        df_harm, cov, m, t = harmonize_gene_ids(df)
        # In mock, 1 mapped, 1 unmapped -> 50%
        assert cov == 0.5

        is_valid = filter_low_coverage_dataset(df_harm, "TEST_TUMOR", cov, m, t)

        assert is_valid is False
        assert captured_call["status"] == "partial_failure"
        assert captured_call["reason"] == "low_harmonization_coverage"
        assert captured_call["details"]["coverage"] == 0.5
    finally:
        prep_module.MyGeneInfo = original_mg
        prep_module.update_feasibility_gate = original_update