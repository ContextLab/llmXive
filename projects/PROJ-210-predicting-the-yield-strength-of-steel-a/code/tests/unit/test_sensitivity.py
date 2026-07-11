import pytest
import pandas as pd
import numpy as np
from src.models.sensitivity import (
    calculate_jaccard_index,
    calculate_spearman_correlation,
    calculate_kuncheva_index,
    run_feature_selection_with_threshold,
    run_sensitivity_sweep,
    save_sensitivity_report,
    run_sensitivity_pipeline
)

@pytest.fixture
def sample_data():
    """Create sample feature importance data for testing."""
    features = ['Fe', 'C', 'Mn', 'Cr', 'Ni', 'Temp', 'CoolingRate', 'HoldTime']
    importance_1 = pd.Series(np.random.rand(len(features)), index=features)
    importance_2 = pd.Series(np.random.rand(len(features)), index=features)
    importance_3 = pd.Series(np.random.rand(len(features)), index=features)
    return {
        'model_xgb': importance_1,
        'model_rf': importance_2,
        'model_gam': importance_3
    }

def test_calculate_jaccard_index():
    set_a = {'a', 'b', 'c', 'd'}
    set_b = {'c', 'd', 'e', 'f'}
    # Intersection: {c, d} (2), Union: {a, b, c, d, e, f} (6) -> 2/6 = 0.333
    jaccard = calculate_jaccard_index(set_a, set_b)
    assert abs(jaccard - 0.3333) < 0.001

    # Identical sets
    assert calculate_jaccard_index(set_a, set_a) == 1.0

    # Empty sets
    assert calculate_jaccard_index(set(), set()) == 0.0

def test_calculate_spearman_correlation():
    ranks_a = [1.0, 2.0, 3.0, 4.0]
    ranks_b = [1.0, 2.0, 3.0, 4.0]
    corr, p_val = calculate_spearman_correlation(ranks_a, ranks_b)
    assert abs(corr - 1.0) < 0.001

    # Reverse order
    ranks_b_rev = [4.0, 3.0, 2.0, 1.0]
    corr_rev, _ = calculate_spearman_correlation(ranks_a, ranks_b_rev)
    assert abs(corr_rev - (-1.0)) < 0.001

def test_calculate_kuncheva_index():
    set_a = {'a', 'b', 'c'}
    set_b = {'a', 'b', 'd'}
    # N=4, k1=3, k2=3, J=2
    # Num: 2*(3) - (9/4) = 6 - 2.25 = 3.75
    # Den: (9/4)*3 - (9/4) = 6.75 - 2.25 = 4.5
    # Res: 3.75 / 4.5 = 0.8333
    kuncheva = calculate_kuncheva_index(set_a, set_b, total_features=4)
    assert abs(kuncheva - 0.8333) < 0.001

def test_run_feature_selection_with_threshold():
    data = pd.Series([0.1, 0.5, 0.8, 0.2, 0.9], index=['a', 'b', 'c', 'd', 'e'])
    
    # Absolute threshold
    selected = run_feature_selection_with_threshold(data, 0.6)
    assert set(selected) == {'c', 'e'}
    
    # Relative threshold (50% of max 0.9 -> 0.45)
    selected_rel = run_feature_selection_with_threshold(data, 0.5, method='relative')
    assert set(selected_rel) == {'b', 'c', 'e'}

def test_run_sensitivity_sweep(sample_data):
    thresholds = [0.1, 0.5, 0.9]
    results = run_sensitivity_sweep(sample_data, thresholds)
    
    assert 'thresholds' in results
    assert 'selected_features' in results
    assert 'stability_metrics' in results
    assert 'stability_status' in results
    
    # Check that stability status is either 'stable' or 'unstable'
    for thresh in thresholds:
        assert results['stability_status'][thresh] in ['stable', 'unstable']
        
        # Check metrics exist
        metrics = results['stability_metrics'][thresh]
        assert 'jaccard' in metrics
        assert 'spearman' in metrics
        assert 'kuncheva' in metrics
        
        # Check Jaccard range
        assert 0.0 <= metrics['jaccard'] <= 1.0

def test_run_sensitivity_pipeline(sample_data, tmp_path):
    output_file = tmp_path / "sensitivity_report.md"
    thresholds = [0.05, 0.10]
    
    results = run_sensitivity_pipeline(
        sample_data, 
        thresholds=thresholds, 
        output_path=str(output_file)
    )
    
    assert output_file.exists()
    content = output_file.read_text()
    assert "Sensitivity Analysis Report" in content
    assert "Threshold Sweep Results" in content
    assert "Stability Metrics" in content
    
    # Verify the 'unstable' flag logic in the report (if Jaccard < 0.8)
    # This depends on random data, so we just check the structure is correct

def test_save_sensitivity_report(tmp_path):
    results = {
        'thresholds': [0.05, 0.10],
        'stability_metrics': {
            0.05: {'jaccard': 0.9, 'spearman': 0.8, 'kuncheva': 0.85},
            0.10: {'jaccard': 0.7, 'spearman': 0.6, 'kuncheva': 0.75}
        },
        'stability_status': {
            0.05: 'stable',
            0.10: 'unstable'
        },
        'selected_features': {}
    }
    
    output_file = tmp_path / "test_report.md"
    save_sensitivity_report(results, str(output_file), justification_text="Test justification.")
    
    content = output_file.read_text()
    assert "unstable" in content
    assert "stable" in content
    assert "Test justification." in content