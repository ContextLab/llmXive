"""
Unit tests for T037c: generate_synthetic_fallback.py

These tests verify the synthetic data generation logic without actually running the full pipeline.
"""
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Import the module under test
from code.generate_synthetic_fallback import (
    generate_synthetic_prompt,
    generate_synthetic_image_url,
    generate_teacher_scores,
    generate_student_scalar,
    generate_human_annotations,
    generate_primary_dimension,
    generate_synthetic_dataset,
    save_config,
    update_research_md
)

@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        # Create necessary directories
        (project_root / "data" / "raw").mkdir(parents=True)
        (project_root / "data" / "processed").mkdir(parents=True)
        (project_root / "specs" / "001-llmxive-follow-up-extending-beyond-scala").mkdir(parents=True)
        yield project_root

def test_generate_synthetic_prompt():
    """Test prompt generation."""
    prompts = generate_synthetic_prompt(n_samples=5, seed=42)
    assert len(prompts) == 5
    assert all(isinstance(p, str) for p in prompts)
    assert all(len(p) > 0 for p in prompts)

def test_generate_synthetic_image_url():
    """Test image URL generation."""
    urls = generate_synthetic_image_url(n_samples=5, seed=42)
    assert len(urls) == 5
    assert all(isinstance(u, str) for u in urls)
    assert all(u.startswith("https://example.com/images/synthetic_") for u in urls)

def test_generate_teacher_scores():
    """Test teacher score generation."""
    scores = generate_teacher_scores(n_samples=5, seed=42)
    assert scores.shape == (5, 4)
    assert all(np.isfinite(scores))
    # Verify distribution parameters (loc=5, scale=2)
    assert np.mean(scores) > 3 and np.mean(scores) < 7

def test_generate_student_scalar():
    """Test student scalar generation."""
    scalars = generate_student_scalar(n_samples=5, seed=42)
    assert scalars.shape == (5,)
    assert all(np.isfinite(scalars))

def test_generate_human_annotations():
    """Test human annotation generation."""
    annotations = generate_human_annotations(n_samples=5, seed=42)
    assert annotations.shape == (5, 4)
    assert all(np.isfinite(annotations))

def test_generate_primary_dimension():
    """Test primary dimension generation."""
    dimensions = generate_primary_dimension(n_samples=5, seed=42)
    assert len(dimensions) == 5
    valid_dims = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    assert all(d in valid_dims for d in dimensions)

def test_generate_synthetic_dataset():
    """Test full synthetic dataset generation."""
    df = generate_synthetic_dataset(n_samples=10, seed=42)
    
    # Check required columns
    required_columns = [
        'prompt', 'image_url', 'teacher_scores', 
        'student_scalar', 'human_annotations', 'primary_dimension'
    ]
    assert all(col in df.columns for col in required_columns)
    
    # Check row count
    assert len(df) == 10
    
    # Check data types
    assert df['prompt'].dtype == 'object'
    assert df['image_url'].dtype == 'object'
    assert df['student_scalar'].dtype in ['float32', 'float64']
    assert df['primary_dimension'].dtype == 'object'

def test_save_config(temp_project_root):
    """Test config saving."""
    config_path = temp_project_root / "data/processed"
    save_config(config_path, is_synthetic=True)
    
    config_file = temp_project_root / "data/processed" / "config.json"
    assert config_file.exists()
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    assert config['IS_SYNTHETIC_RUN'] is True
    assert config['source_type'] == 'synthetic'

def test_update_research_md(temp_project_root):
    """Test research.md update."""
    research_md_path = temp_project_root / "specs/001-llmxive-follow-up-extending-beyond-scala/research.md"
    
    # Create initial research.md
    research_md_path.write_text("# Research\n\nverified_datasets:\n  - dataset_id: test\n")
    
    update_research_md(research_md_path, note="test_fallback")
    
    content = research_md_path.read_text()
    assert "synthetic_fallback" in content or "test_fallback" in content

def test_synthetic_data_independence():
    """
    Verify that teacher scores and human annotations use different seeds,
    ensuring independent noise structures as required by the spec.
    """
    seed = 42
    teacher_scores = generate_teacher_scores(n_samples=100, seed=seed)
    human_annotations = generate_human_annotations(n_samples=100, seed=seed)
    
    # They should be different (not identical)
    assert not np.array_equal(teacher_scores, human_annotations)
    
    # Correlation should not be perfect
    correlation = np.corrcoef(teacher_scores.flatten(), human_annotations.flatten())[0, 1]
    assert abs(correlation) < 1.0