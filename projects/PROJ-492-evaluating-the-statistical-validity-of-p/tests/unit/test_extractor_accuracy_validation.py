"""
Unit tests for the FR-002 validation logic.
Verifies the coverage calculation logic is correct.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.test_extractor_accuracy import calculate_field_coverage, REQUIRED_FIELDS

def test_full_coverage():
    """Test when all fields are present."""
    summaries = [
        {field: f"value_{field}" for field in REQUIRED_FIELDS}
        for _ in range(10)
    ]
    result = calculate_field_coverage(summaries)
    assert result["coverage"] == 100.0
    assert result["valid"] == 10
    assert result["total"] == 10

def test_partial_coverage():
    """Test when some fields are missing."""
    summaries = []
    # 9 complete, 1 missing one field
    for _ in range(9):
        summaries.append({field: f"value_{field}" for field in REQUIRED_FIELDS})
    
    # Missing 'reported_p_value'
    partial = {field: f"value_{field}" for field in REQUIRED_FIELDS if field != "reported_p_value"}
    partial["reported_p_value"] = None
    summaries.append(partial)
    
    result = calculate_field_coverage(summaries)
    assert result["coverage"] == 90.0
    assert result["valid"] == 9
    assert result["total"] == 10

def test_empty_corpus():
    """Test with empty list."""
    result = calculate_field_coverage([])
    assert result["coverage"] == 0.0
    assert result["valid"] == 0
    assert result["total"] == 0

def test_mixed_types():
    """Test with non-dict entries (should be skipped)."""
    summaries = [
        {field: f"value_{field}" for field in REQUIRED_FIELDS},
        "not a dict",
        None,
        {field: f"value_{field}" for field in REQUIRED_FIELDS}
    ]
    result = calculate_field_coverage(summaries)
    # Should count 2 valid out of 2 dicts (non-dicts are ignored in denominator? No, logic iterates)
    # Looking at implementation: if not isinstance(summary, dict): continue
    # So total is len(summaries), but valid only counts dicts with all fields.
    # Wait, the implementation:
    # if not summaries: return ...
    # valid_count = 0
    # for summary in summaries:
    #    if not isinstance(summary, dict): continue
    #    ... check fields ...
    # coverage = (valid_count / len(summaries)) * 100
    # So non-dicts count as invalid.
    assert result["total"] == 4
    assert result["valid"] == 2
    assert result["coverage"] == 50.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
