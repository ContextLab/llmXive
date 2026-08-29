import pytest
import math
from code.analysis.meta_analysis import run_analysis_or_synthesis, run_random_effects_meta_analysis
from code.analysis.descriptive_synthesis import DescriptiveSynthesisResult
from code.data.models import EffectSize

class MockEffectSize:
    def __init__(self, study_id: str, effect_size: float, se: float, n_total: int):
        self.study_id = study_id
        self.effect_size = effect_size
        self.se = se
        self.n_total = n_total

def test_meta_analysis_runs_when_n_ge_10(tmp_path):
    """Test that meta-analysis runs when N >= 10."""
    # Create 10 mock effect sizes
    effects = [
        MockEffectSize(f"study_{i}", 0.5 + (i * 0.01), 0.1, 100)
        for i in range(10)
    ]
    
    output_path = str(tmp_path / "result.json")
    
    # This should run meta-analysis
    result = run_analysis_or_synthesis(
        effect_sizes=effects,
        output_path=output_path,
        min_studies_threshold=10
    )
    
    assert result.method == "random_effects"
    assert result.k_studies == 10
    # Check that file was created
    import os
    assert os.path.exists(output_path)

def test_descriptive_synthesis_runs_when_n_lt_10(tmp_path):
    """Test that descriptive synthesis runs when N < 10."""
    # Create 5 mock effect sizes
    effects = [
        MockEffectSize(f"study_{i}", 0.5 + (i * 0.01), 0.1, 100)
        for i in range(5)
    ]
    
    output_path = str(tmp_path / "result.json")
    
    # This should run descriptive synthesis
    result = run_analysis_or_synthesis(
        effect_sizes=effects,
        output_path=output_path,
        min_studies_threshold=10
    )
    
    assert result.method == "descriptive_synthesis"
    assert result.k_studies == 5
    # Check that file was created (report text)
    import os
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        content = f.read()
    assert "Descriptive Synthesis" in content
    assert "Number of Studies: 5" in content

def test_boundary_condition_n_equals_10(tmp_path):
    """Test boundary condition exactly at N=10."""
    effects = [MockEffectSize(f"study_{i}", 0.5, 0.1, 100) for i in range(10)]
    output_path = str(tmp_path / "result.json")
    
    result = run_analysis_or_synthesis(
        effect_sizes=effects,
        output_path=output_path,
        min_studies_threshold=10
    )
    
    # Should run meta-analysis at exactly 10
    assert result.method == "random_effects"

def test_boundary_condition_n_equals_9(tmp_path):
    """Test boundary condition just below N=10."""
    effects = [MockEffectSize(f"study_{i}", 0.5, 0.1, 100) for i in range(9)]
    output_path = str(tmp_path / "result.json")
    
    result = run_analysis_or_synthesis(
        effect_sizes=effects,
        output_path=output_path,
        min_studies_threshold=10
    )
    
    # Should run descriptive synthesis
    assert result.method == "descriptive_synthesis"