import pytest
import pandas as pd
import hashlib
import os
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from primary_dimension_util import derive_primary_dimension_from_metadata, get_derivation_rule_hash, process_dataframe_primary_dimensions

def test_derive_primary_dimension_basic():
    """Test basic derivation of primary dimension."""
    prompt = "Test prompt text"
    expected_hash = hashlib.sha256(prompt.encode()).hexdigest()
    expected_int = int(expected_hash, 16)
    expected_dim = expected_int % 4

    result = derive_primary_dimension_from_metadata(prompt)
    assert result == expected_dim

def test_derive_primary_dimension_none():
    """Test derivation with None input."""
    result = derive_primary_dimension_from_metadata(None)
    assert result is None

def test_derive_primary_dimension_empty():
    """Test derivation with empty string."""
    result = derive_primary_dimension_from_metadata("")
    assert isinstance(result, int)
    assert 0 <= result < 4

def test_process_dataframe_primary_dimensions():
    """Test dataframe processing."""
    df = pd.DataFrame({
        "sample_id": [1, 2, 3],
        "prompt_text": ["Prompt A", "Prompt B", "Prompt C"]
    })
    
    import logging
    logger = logging.getLogger(__name__)
    
    result_df = process_dataframe_primary_dimensions(df, logger)
    
    assert "primary_dimension" in result_df.columns
    assert len(result_df) == 3
    assert all(isinstance(dim, int) for dim in result_df["primary_dimension"])
    assert all(0 <= dim < 4 for dim in result_df["primary_dimension"])

def test_derivation_rule_hash():
    """Test that derivation rule hash is consistent."""
    rule = "sha256_prompt_text_mod_4_v1"
    hash1 = get_derivation_rule_hash(rule)
    hash2 = get_derivation_rule_hash(rule)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
