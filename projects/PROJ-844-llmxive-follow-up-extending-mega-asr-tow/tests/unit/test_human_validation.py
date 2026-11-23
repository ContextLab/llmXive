"""
Unit tests for code/human_validation.py
"""
import pytest
import sys
from pathlib import Path
import csv

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from human_validation import (
    load_and_merge_subsets,
    create_validation_sample
)

def test_create_validation_sample(tmp_path):
    """Test creation of validation sample."""
    # Create mock stress curves data
    stress_curves_file = tmp_path / "stress_curves.csv"
    with open(stress_curves_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["clip_id", "vector_id", "sss", "wer"])
        writer.writerow(["clip_001", "vec_001", "0.9", "0.05"])
        writer.writerow(["clip_002", "vec_002", "0.8", "0.10"])
    
    sample = create_validation_sample(
        stress_curves_file=str(stress_curves_file),
        sample_size=1
    )
    
    assert len(sample) == 1
    assert "clip_id" in sample[0]
    assert "vector_id" in sample[0]
