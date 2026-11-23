import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the functions we want to test
# Note: We assume simulate.py is in the code/ directory relative to tests/
# or that code/ is in the PYTHONPATH.
# For this test, we will import directly from the file if needed,
# but standard practice is to have code/ as a package or in sys.path.
# Assuming code/simulate.py is importable as 'simulate' or via relative import.
# Since the project structure puts code/ at root, we might need to adjust sys.path.

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from simulate import (
    generate_sample,
    generate_teacher_scores,
    generate_student_scalar,
    generate_human_annotations,
    derive_primary_dimension,
    run_simulation,
    save_dataset
)

def test_derive_primary_dimension():
    # Hash function behavior can vary between Python versions/installs,
    # but for a fixed seed and input in a single run, it should be consistent.
    # We test that it returns an integer in [0, 3].
    dim = derive_primary_dimension(12345)
    assert 0 <= dim <= 4

def test_generate_teacher_scores_shape():
    import numpy as np
    rng = np.random.default_rng(42)
    scores = generate_teacher_scores(rng)
    assert len(scores) == 4
    assert all(0.0 <= v <= 1.0 for v in scores.values())

def test_generate_student_scalar_range():
    import numpy as np
    rng = np.random.default_rng(42)
    val = generate_student_scalar(rng)
    assert 0.0 <= val <= 1.0

def test_generate_human_annotations_shape():
    import numpy as np
    rng = np.random.default_rng(42)
    ann = generate_human_annotations(rng)
    assert len(ann) == 4
    assert all(0.0 <= v <= 1.0 for v in ann.values())

def test_generate_sample_structure():
    import numpy as np
    rng = np.random.default_rng(42)
    sample = generate_sample(1, rng, 100)
    assert "sample_id" in sample
    assert "image_path" in sample
    assert "species_id" in sample
    assert "teacher_scores" in sample
    assert "student_scalar" in sample
    assert "human_annotations" in sample
    assert "primary_dimension" in sample
    assert isinstance(sample["teacher_scores"], dict)
    assert isinstance(sample["human_annotations"], dict)

def test_run_simulation_dataframe():
    df = run_simulation(n_samples=10, seed=42)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 10
    required_cols = [
        "sample_id", "image_path", "species_id", 
        "teacher_scores", "student_scalar", 
        "human_annotations", "primary_dimension"
    ]
    assert all(col in df.columns for col in required_cols)

def test_save_dataset_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_output.parquet")
        df = run_simulation(n_samples=5, seed=42)
        save_dataset(df, output_path)
        assert os.path.exists(output_path)
        # Verify we can read it back
        df_read = pd.read_parquet(output_path)
        assert len(df_read) == 5
