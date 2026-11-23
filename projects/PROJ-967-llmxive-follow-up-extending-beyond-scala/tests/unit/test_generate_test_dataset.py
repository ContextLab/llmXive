import pytest
import os
import sys
import pandas as pd
import numpy as np
import hashlib
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_test_dataset import generate_deterministic_scores, generate_student_scalar, generate_human_annotations

def test_generate_deterministic_scores_consistency():
    """Test that the same inputs produce the same scores."""
    prompt = "test prompt"
    species = 1
    
    scores1 = generate_deterministic_scores(prompt, species)
    scores2 = generate_deterministic_scores(prompt, species)
    
    assert scores1 == scores2
    assert len(scores1) == 4
    assert all(0 <= s <= 1 for s in scores1)

def test_generate_deterministic_scores_variation():
    """Test that different inputs produce different scores."""
    scores1 = generate_deterministic_scores("prompt A", 1)
    scores2 = generate_deterministic_scores("prompt B", 1)
    scores3 = generate_deterministic_scores("prompt A", 2)
    
    assert scores1 != scores2
    assert scores1 != scores3

def test_student_scalar_calculation():
    """Test that student scalar is the mean of teacher scores."""
    scores = [0.1, 0.2, 0.3, 0.4]
    scalar = generate_student_scalar(scores)
    assert np.isclose(scalar, 0.25)

def test_human_annotations_independence():
    """Test that human annotations are independent of teacher scores."""
    prompt = "test"
    species = 1
    
    # Teacher scores use seed_offset 0 (default)
    teacher = generate_deterministic_scores(prompt, species, seed_offset=0)
    # Human annotations use seed_offset 9999
    human = generate_human_annotations(prompt, species)
    
    # They should be different due to different offsets
    assert teacher != human
    # But both should be deterministic
    assert human == generate_human_annotations(prompt, species)

def test_script_execution_creates_file(tmp_path):
    """Test that the script actually creates the output file."""
    import subprocess
    
    output_file = tmp_path / "test_output.parquet"
    
    # Run the script
    result = subprocess.run(
        [
            sys.executable, 
            "-m", "generate_test_dataset", 
            "--n-samples", "5", 
            "--seed", "42", 
            "--output", str(output_file)
        ],
        cwd=Path(__file__).parent.parent.parent / "code",
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert output_file.exists(), "Output file was not created"
    
    # Verify content
    df = pd.read_parquet(output_file)
    assert len(df) == 5
    assert "teacher_scores" in df.columns
    assert "human_annotations" in df.columns
    assert "student_scalar" in df.columns
    
    # Verify structure of list columns
    assert all(len(x) == 4 for x in df["teacher_scores"])
    assert all(len(x) == 4 for x in df["human_annotations"])