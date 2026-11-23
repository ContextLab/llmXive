import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala" / "code"))

from fidelity_loss_lineage import verify_fidelity_loss_lineage, DERIVATION_RULE_STRING

def test_verify_fidelity_loss_mathematical_correctness():
    """Test that the lineage verification correctly calculates the loss."""
    # Create a mock dataframe
    data = {
        "fidelity_loss": [1.0, 2.0, 3.0],
        "student_scalar": [10.0, 20.0, 30.0],
        "human_annotations": [[11.0, 12.0, 13.0, 14.0], [22.0, 23.0, 24.0, 25.0], [27.0, 28.0, 29.0, 30.0]],
        "primary_dimension": [0, 1, 0]
    }
    df = pd.DataFrame(data)

    result = verify_fidelity_loss_lineage(df)

    assert result["verification_status"] == "passed"
    assert result["samples_verified"] == 3
    assert result["excluded_columns"] == ["teacher_scores"]
    
    # Check the hash is consistent
    import hashlib
    expected_hash = hashlib.sha256(DERIVATION_RULE_STRING.encode()).hexdigest()
    assert result["derivation_rule_hash"] == expected_hash

def test_verify_fidelity_loss_mismatch_detection():
    """Test that the verification detects incorrect loss values."""
    data = {
        "fidelity_loss": [999.0, 2.0, 3.0], # First one is wrong
        "student_scalar": [10.0, 20.0, 30.0],
        "human_annotations": [[11.0, 12.0, 13.0, 14.0], [22.0, 23.0, 24.0, 25.0], [27.0, 28.0, 29.0, 30.0]],
        "primary_dimension": [0, 1, 0]
    }
    df = pd.DataFrame(data)

    result = verify_fidelity_loss_lineage(df)

    assert result["verification_status"] == "failed"
    assert len(result["errors"]) > 0
    assert "Row 0" in result["errors"][0]

def test_verify_fidelity_loss_missing_columns():
    """Test that missing columns raise an error."""
    data = {
        "fidelity_loss": [1.0],
        "student_scalar": [10.0],
        # Missing human_annotations and primary_dimension
    }
    df = pd.DataFrame(data)

    with pytest.raises(ValueError) as exc_info:
        verify_fidelity_loss_lineage(df)
    
    assert "Missing required columns" in str(exc_info.value)

def test_verify_fidelity_loss_nan_handling():
    """Test that NaN values are handled gracefully (skipped)."""
    data = {
        "fidelity_loss": [1.0, None, 3.0],
        "student_scalar": [10.0, None, 30.0],
        "human_annotations": [[11.0, 12.0, 13.0, 14.0], [22.0, 23.0, 24.0, 25.0], [27.0, 28.0, 29.0, 30.0]],
        "primary_dimension": [0, 1, 0]
    }
    df = pd.DataFrame(data)

    result = verify_fidelity_loss_lineage(df)
    
    # Should verify the non-NaN rows
    assert result["samples_verified"] == 2
    assert result["verification_status"] == "passed"
