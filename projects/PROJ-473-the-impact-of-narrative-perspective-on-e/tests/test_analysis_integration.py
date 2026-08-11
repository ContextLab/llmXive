import os
import json
import tempfile
import pandas as pd
import pytest
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analysis import run_analysis_pipeline, run_regression_analysis, apply_bonferroni_correction

@pytest.fixture
def sample_aligned_dataset(tmp_path):
    """Create a temporary aligned dataset for testing."""
    data = {
        'story_id': [f's{i}' for i in range(1, 51)],
        'perspective_score': [0.1 + i * 0.02 for i in range(50)],  # 0.1 to 1.0
        'empathy_score': [3.0 + i * 0.05 + (i % 3) * 0.2 for i in range(50)],
        'moral_judgement_score': [2.5 + i * 0.04 + (i % 2) * 0.3 for i in range(50)]
    }
    df = pd.DataFrame(data)
    output_path = os.path.join(tmp_path, 'aligned_dataset.csv')
    df.to_csv(output_path, index=False)
    return output_path

def test_run_analysis_pipeline_creates_output(sample_aligned_dataset, tmp_path):
    """Test that the analysis pipeline produces valid JSON output."""
    output_path = os.path.join(tmp_path, 'analysis_results.json')
    
    # Run pipeline
    results = run_analysis_pipeline(sample_aligned_dataset)
    
    # Write to file (simulating main.py behavior)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Verify file exists
    assert os.path.exists(output_path)
    
    # Verify JSON structure
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    
    assert 'moral_judgement' in loaded
    assert 'empathy' in loaded
    assert 'summary' in loaded
    assert 'slope' in loaded['moral_judgement']
    assert 'p_value' in loaded['moral_judgement']
    assert 'r_squared' in loaded['moral_judgement']
    
    # Verify plot was created
    assert os.path.exists(loaded['plot_path'])

def test_bonferroni_correction_logic():
    """Test Bonferroni correction calculation."""
    p_values = [0.01, 0.04, 0.03]
    corrected = apply_bonferroni_correction(p_values)
    
    # With k=3, 0.01 * 3 = 0.03, etc.
    assert corrected[0] == 0.03
    assert corrected[1] == 0.12
    assert corrected[2] == 0.09

def test_regression_recovery(sample_aligned_dataset):
    """Test that regression returns expected structure."""
    results = run_regression_analysis(sample_aligned_dataset)
    
    assert 'moral_judgement' in results
    assert 'empathy' in results
    assert results['moral_judgement']['n_samples'] == 50
    assert 0 <= results['moral_judgement']['r_squared'] <= 1