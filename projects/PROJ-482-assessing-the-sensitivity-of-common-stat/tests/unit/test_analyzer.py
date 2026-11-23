import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from analyzer import (
    StabilityResult,
    load_simulation_results,
    aggregate_results,
    compute_bootstrap_ci,
    analyze_stability_trend,
    plot_stability_trend,
    export_stability_results,
    analyze_and_export
)

def test_stability_result_to_dict():
    result = StabilityResult(
        slope=0.005, intercept=0.04, r_squared=0.1, p_value=0.03, success=True, message="OK"
    )
    d = result.to_dict()
    assert d['slope'] == 0.005
    assert d['success'] is True
    assert 'slope' in d
    assert 'intercept' in d

def test_aggregate_results():
    data = {
        'sample_size': [10, 10, 20, 20],
        'distribution_type': ['normal', 'uniform', 'normal', 'uniform'],
        'test_type': ['t-test', 't-test', 't-test', 't-test'],
        'type1_rate': [0.05, 0.06, 0.04, 0.05]
    }
    df = pd.DataFrame(data)
    agg = aggregate_results(df)
    assert len(agg) == 4
    assert 'type1_rate_mean' in agg.columns
    assert agg.loc[agg['sample_size'] == 10, 'type1_rate_mean'].iloc[0] > 0

def test_compute_bootstrap_ci():
    data = np.array([0.05, 0.06, 0.04, 0.05, 0.05])
    lower, upper = compute_bootstrap_ci(data, n_resamples=100)
    assert lower <= upper
    assert 0.04 <= lower <= 0.06
    assert 0.04 <= upper <= 0.06

def test_analyze_stability_trend():
    # Create a dataset where error rate is constant (slope ~ 0)
    data = {
        'sample_size': [10, 20, 50, 100],
        'type1_rate': [0.05, 0.05, 0.05, 0.05]
    }
    df = pd.DataFrame(data)
    result = analyze_stability_trend(df, threshold_slope=0.01)
    assert result.success is True
    assert abs(result.slope) < 0.01

def test_analyze_stability_trend_unstable():
    # Create a dataset where error rate increases significantly
    data = {
        'sample_size': [10, 20, 50, 100],
        'type1_rate': [0.05, 0.10, 0.15, 0.20]
    }
    df = pd.DataFrame(data)
    result = analyze_stability_trend(df, threshold_slope=0.01)
    assert result.success is False
    assert result.slope > 0.01

def test_plot_stability_trend():
    data = {
        'sample_size': [10, 20, 50, 100],
        'type1_rate': [0.05, 0.06, 0.05, 0.05]
    }
    df = pd.DataFrame(data)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, 'test_plot.png')
        plot_stability_trend(df, out_path)
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0

def test_export_stability_results():
    result = StabilityResult(0.001, 0.05, 0.0, 0.9, True, "Test")
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, 'test_results.csv')
        export_stability_results(result, out_path)
        assert os.path.exists(out_path)
        df = pd.read_csv(out_path)
        assert 'slope' in df.columns
        assert df['slope'].iloc[0] == 0.001

def test_analyze_and_export():
    data = {
        'sample_size': [10, 20, 50, 100],
        'type1_rate': [0.05, 0.05, 0.05, 0.05]
    }
    df = pd.DataFrame(data)
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.csv')
        df.to_csv(input_path, index=False)
        out_dir = os.path.join(tmpdir, 'output')
        
        result = analyze_and_export(input_path, out_dir)
        
        assert result.success is True
        assert os.path.exists(os.path.join(out_dir, 'stability_trend.csv'))
        assert os.path.exists(os.path.join(out_dir, 'plots', 'stability_trend.png'))
