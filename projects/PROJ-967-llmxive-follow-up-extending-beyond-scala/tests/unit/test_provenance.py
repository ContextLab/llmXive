import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
import json

# Import functions from the provenance module
import sys
sys.path.insert(0, 'code')
from provenance import (
    load_dataset,
    verify_provenance_independence,
    save_verification_report
)

@pytest.fixture
def temp_parquet_file():
    """Create a temporary parquet file with test data for provenance verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_data.parquet")
        
        # Create test data where human_annotations are INDEPENDENT of teacher_scores
        n_samples = 100
        
        # Generate deterministic teacher_scores based on species_id and prompt_text
        # (simulating the actual data generation process)
        species_ids = np.random.randint(1, 50, n_samples)
        prompts = [f"Image of species {i} in natural setting" for i in range(n_samples)]
        
        # Teacher scores: deterministic function of species_id and prompt
        teacher_scores = []
        for i in range(n_samples):
            seed_val = hash(f"{species_ids[i]}_{prompts[i]}") % 10000
            scores = [
                (seed_val + i * 7) % 100 / 100.0,
                (seed_val + i * 11) % 100 / 100.0,
                (seed_val + i * 13) % 100 / 100.0,
                (seed_val + i * 17) % 100 / 100.0
            ]
            teacher_scores.append(scores)
        
        # Student scalar: derived from teacher_scores (mean)
        student_scalars = [np.mean(scores) for scores in teacher_scores]
        
        # Human annotations: deterministic function of species_id and prompt ONLY
        # NO dependency on teacher_scores
        human_annotations = []
        for i in range(n_samples):
            seed_val = hash(f"{species_ids[i]}_{prompts[i]}") % 10000
            # Use a DIFFERENT hash pattern to ensure independence from teacher_scores
            scores = [
                (seed_val + i * 23) % 100 / 100.0,  # Different multiplier
                (seed_val + i * 29) % 100 / 100.0,
                (seed_val + i * 31) % 100 / 100.0,
                (seed_val + i * 37) % 100 / 100.0
            ]
            human_annotations.append(scores)
        
        # Create DataFrame
        df = pd.DataFrame({
            "image_path": [f"image_{i}.jpg" for i in range(n_samples)],
            "species_id": species_ids,
            "prompt_text": prompts,
            "teacher_scores": teacher_scores,
            "student_scalar": student_scalars,
            "human_annotations": human_annotations
        })
        
        # Save to parquet
        df.to_parquet(filepath, index=False)
        
        yield filepath

def test_load_dataset_success(temp_parquet_file):
    """Test that load_dataset successfully loads a parquet file."""
    import logging
    logger = logging.getLogger(__name__)
    
    df = load_dataset(temp_parquet_file, logger)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "teacher_scores" in df.columns
    assert "human_annotations" in df.columns

def test_verify_provenance_independence_passes(temp_parquet_file):
    """Test that provenance verification passes when human_annotations are independent."""
    import logging
    logger = logging.getLogger(__name__)
    
    df = load_dataset(temp_parquet_file, logger)
    result = verify_provenance_independence(df, logger)
    
    assert result["verification_passed"] is True
    assert result["sample_count"] > 0
    assert result["linear_regression_r2_from_teacher"] < 0.01
    assert result["linear_regression_r2_from_student_scalar"] < 0.01
    assert "independent" in result["message"].lower()

def test_verify_provenance_independence_fails_with_dependent_data():
    """Test that verification fails when human_annotations depend on teacher_scores."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "dependent_data.parquet")
        
        n_samples = 100
        species_ids = np.random.randint(1, 50, n_samples)
        prompts = [f"Image of species {i}" for i in range(n_samples)]
        
        # Create data where human_annotations DEPEND on teacher_scores
        teacher_scores = []
        human_annotations = []
        
        for i in range(n_samples):
            seed_val = hash(f"{species_ids[i]}_{prompts[i]}") % 10000
            teacher_scores_i = [
                (seed_val + i * 7) % 100 / 100.0,
                (seed_val + i * 11) % 100 / 100.0,
                (seed_val + i * 13) % 100 / 100.0,
                (seed_val + i * 17) % 100 / 100.0
            ]
            # Human annotations are a direct function of teacher_scores (dependency!)
            human_scores_i = [
                t * 0.9 + 0.05 for t in teacher_scores_i  # Strong linear dependency
            ]
            
            teacher_scores.append(teacher_scores_i)
            human_annotations.append(human_scores_i)
        
        student_scalars = [np.mean(scores) for scores in teacher_scores]
        
        df = pd.DataFrame({
            "image_path": [f"image_{i}.jpg" for i in range(n_samples)],
            "species_id": species_ids,
            "prompt_text": prompts,
            "teacher_scores": teacher_scores,
            "student_scalar": student_scalars,
            "human_annotations": human_annotations
        })
        
        df.to_parquet(filepath, index=False)
        
        import logging
        logger = logging.getLogger(__name__)
        
        loaded_df = load_dataset(filepath, logger)
        result = verify_provenance_independence(loaded_df, logger)
        
        # Should fail because there IS a dependency
        assert result["verification_passed"] is False
        assert result["linear_regression_r2_from_teacher"] > 0.5  # High R² due to dependency

def test_save_verification_report(temp_parquet_file):
    """Test that verification report is saved correctly."""
    import logging
    logger = logging.getLogger(__name__)
    
    df = load_dataset(temp_parquet_file, logger)
    result = verify_provenance_independence(df, logger)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "report.json")
        save_verification_report(result, output_path, logger)
        
        assert os.path.exists(output_path)
        
        with open(output_path, "r") as f:
            saved_result = json.load(f)
        
        assert saved_result["verification_passed"] == result["verification_passed"]
        assert saved_result["sample_count"] == result["sample_count"]

def test_load_dataset_missing_file():
    """Test that load_dataset raises FileNotFoundError for missing file."""
    import logging
    logger = logging.getLogger(__name__)
    
    with pytest.raises(FileNotFoundError):
        load_dataset("/nonexistent/path/data.parquet", logger)

def test_verify_provenance_missing_columns(temp_parquet_file):
    """Test that verification fails when required columns are missing."""
    import logging
    logger = logging.getLogger(__name__)
    
    df = load_dataset(temp_parquet_file, logger)
    
    # Remove a required column
    df_no_teacher = df.drop(columns=["teacher_scores"])
    
    with pytest.raises(ValueError) as exc_info:
        verify_provenance_independence(df_no_teacher, logger)
    
    assert "Missing required columns" in str(exc_info.value)
    assert "teacher_scores" in str(exc_info.value)
