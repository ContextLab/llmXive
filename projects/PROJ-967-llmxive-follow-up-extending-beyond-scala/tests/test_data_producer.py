import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_producer import (
    generate_synthetic_annotations,
    derive_primary_dimension,
    calculate_sha256
)

def test_generate_synthetic_annotations():
    """Test that synthetic annotations and teacher scores are generated correctly."""
    df = pd.DataFrame({
        "image_path": ["img1.jpg", "img2.jpg"],
        "species_id": [1, 2]
    })
    
    result_df = generate_synthetic_annotations(df, seed=42)
    
    assert "teacher_scores" in result_df.columns
    assert "student_scalar" in result_df.columns
    assert "human_annotations" in result_df.columns
    
    # Check structure of teacher_scores
    for scores in result_df["teacher_scores"]:
        assert isinstance(scores, dict)
        assert len(scores) == 4
        assert "dimension_0" in scores
        assert "dimension_1" in scores
        assert "dimension_2" in scores
        assert "dimension_3" in scores
    
    # Check student_scalar
    assert len(result_df["student_scalar"]) == 2
    assert all(isinstance(x, float) for x in result_df["student_scalar"])
    
    # Check human_annotations
    for annots in result_df["human_annotations"]:
        assert isinstance(annots, dict)
        assert len(annots) == 4

def test_derive_primary_dimension():
    """Test that primary_dimension is derived correctly from species_id."""
    df = pd.DataFrame({
        "species_id": [1, 2, 3, 4, 5]
    })
    
    result_df = derive_primary_dimension(df)
    
    assert "primary_dimension" in result_df.columns
    assert all(0 <= x <= 3 for x in result_df["primary_dimension"])
    
    # Check determinism
    df2 = pd.DataFrame({"species_id": [1, 2, 3, 4, 5]})
    result_df2 = derive_primary_dimension(df2)
    assert result_df["primary_dimension"].tolist() == result_df2["primary_dimension"].tolist()

def test_derive_primary_dimension_null():
    """Test handling of null species_id."""
    df = pd.DataFrame({
        "species_id": [1, None, 3]
    })
    
    result_df = derive_primary_dimension(df)
    
    assert result_df.loc[0, "primary_dimension"] is not None
    assert pd.isna(result_df.loc[1, "primary_dimension"])
    assert result_df.loc[2, "primary_dimension"] is not None
