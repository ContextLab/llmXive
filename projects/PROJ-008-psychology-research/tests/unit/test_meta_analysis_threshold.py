import pytest
from code.analysis.meta_analysis import run_analysis_or_synthesis
from code.analysis.descriptive_synthesis import DescriptiveSynthesisResult

def test_meta_analysis_runs_when_n_ge_10():
    """Test that meta-analysis runs when N >= 10."""
    # Create 10 dummy studies and effect sizes
    studies = [{"id": i} for i in range(10)]
    effect_sizes = [{"effect": 0.5, "se": 0.1} for _ in range(10)]
    
    result = run_analysis_or_synthesis(studies, effect_sizes, min_n_for_meta=10)
    
    assert result["k"] == 10
    assert result["decision"] == "meta_analysis"
    assert "meta_analysis" in result
    assert "descriptive_synthesis" not in result
    assert "warning" not in result or "Insufficient studies" not in result["warning"]

def test_descriptive_synthesis_runs_when_n_lt_10():
    """Test that descriptive synthesis runs when N < 10."""
    # Create 5 dummy studies and effect sizes
    studies = [{"id": i} for i in range(5)]
    effect_sizes = [{"effect": 0.5, "se": 0.1} for _ in range(5)]
    
    result = run_analysis_or_synthesis(studies, effect_sizes, min_n_for_meta=10)
    
    assert result["k"] == 5
    assert result["decision"] == "descriptive_synthesis"
    assert "descriptive_synthesis" in result
    assert "meta_analysis" not in result
    assert "warning" in result
    assert "Insufficient studies" in result["warning"]
    assert "descriptive synthesis" in result["warning"].lower()

def test_custom_threshold():
    """Test that custom threshold works."""
    studies = [{"id": i} for i in range(5)]
    effect_sizes = [{"effect": 0.5, "se": 0.1} for _ in range(5)]
    
    # Threshold is 3, so N=5 should run meta-analysis
    result = run_analysis_or_synthesis(studies, effect_sizes, min_n_for_meta=3)
    
    assert result["decision"] == "meta_analysis"
    
    # Threshold is 6, so N=5 should run descriptive synthesis
    result = run_analysis_or_synthesis(studies, effect_sizes, min_n_for_meta=6)
    
    assert result["decision"] == "descriptive_synthesis"
