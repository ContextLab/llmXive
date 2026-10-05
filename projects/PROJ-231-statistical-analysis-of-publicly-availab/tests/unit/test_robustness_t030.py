import json
import pickle
import numpy as np
import pytest
from pathlib import Path
import tempfile
import shutil

from robustness import calculate_stability_metrics, run_loo_jackknife, STABILITY_THRESHOLD

@pytest.fixture
def temp_artifacts_dir():
    """Create a temporary directory for artifacts."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_stability_metrics_identifies_unstable_components():
    """Test that stability metrics correctly identify unstable components."""
    # Create mock full results
    num_components = 3
    num_samples = 100
    
    full_eigenfunctions = [np.random.randn(num_samples) for _ in range(num_components)]
    full_results = {
        'eigenfunctions': full_eigenfunctions,
        'num_components': num_components
    }
    
    # Create mock LOO results where component 1 is unstable
    loo_results_list = []
    for i in range(5):
        loo_eigenfunctions = []
        for comp_idx in range(num_components):
            if comp_idx == 1:
                # Make component 1 unstable (low correlation)
                loo_func = np.random.randn(num_samples) * 0.1  # Very different
            else:
                # Make other components stable
                loo_func = full_eigenfunctions[comp_idx] + np.random.randn(num_samples) * 0.01
            loo_eigenfunctions.append(loo_func)
        loo_results_list.append({'eigenfunctions': loo_eigenfunctions})
    
    ensemble_members = [f"model_{i}" for i in range(5)]
    
    metrics = calculate_stability_metrics(full_results, loo_results_list, ensemble_members)
    
    # Check that component 1 is flagged as unstable
    assert len(metrics['unstable_components']) > 0
    unstable_indices = [c['component_index'] for c in metrics['unstable_components']]
    assert 1 in unstable_indices, "Component 1 should be flagged as unstable"
    
    # Check that mean correlation is below threshold
    for comp in metrics['unstable_components']:
        assert comp['mean_correlation'] < STABILITY_THRESHOLD

def test_stability_metrics_identifies_instability_sources():
    """Test that instability sources are correctly identified."""
    num_components = 2
    num_samples = 50
    
    full_eigenfunctions = [np.random.randn(num_samples) for _ in range(num_components)]
    full_results = {
        'eigenfunctions': full_eigenfunctions,
        'num_components': num_components
    }
    
    # Create LOO results where specific members cause instability
    loo_results_list = []
    for i in range(5):
        loo_eigenfunctions = []
        for comp_idx in range(num_components):
            if i == 2 and comp_idx == 0:  # Model 2 causes instability in component 0
                loo_func = np.random.randn(num_samples) * 0.1
            else:
                loo_func = full_eigenfunctions[comp_idx] + np.random.randn(num_samples) * 0.01
            loo_eigenfunctions.append(loo_func)
        loo_results_list.append({'eigenfunctions': loo_eigenfunctions})
    
    ensemble_members = [f"model_{i}" for i in range(5)]
    
    metrics = calculate_stability_metrics(full_results, loo_results_list, ensemble_members)
    
    # Check instability sources
    assert 'instability_sources' in metrics
    assert 'component_0' in metrics['instability_sources']
    
    instability_source = metrics['instability_sources']['component_0']
    assert 'causing_members' in instability_source
    assert len(instability_source['causing_members']) > 0

def test_run_loo_jackknife_creates_unstable_modes_file(temp_artifacts_dir):
    """Test that run_loo_jackknife creates the unstable_modes.json file."""
    # Setup mock data
    num_components = 2
    num_samples = 50
    num_members = 3
    
    artifacts_dir = temp_artifacts_dir
    
    # Create full FPCA results
    full_eigenfunctions = [np.random.randn(num_samples) for _ in range(num_components)]
    full_results = {
        'eigenfunctions': full_eigenfunctions,
        'num_components': num_components,
        'ensemble_members': [f"model_{i}" for i in range(num_members)]
    }
    
    full_results_path = artifacts_dir / "fpca_results.pkl"
    with open(full_results_path, 'wb') as f:
        pickle.dump(full_results, f)
    
    # Create LOO subsamples
    for i in range(num_members):
        loo_eigenfunctions = []
        for comp_idx in range(num_components):
            if i == 1 and comp_idx == 0:  # Make one component unstable
                loo_func = np.random.randn(num_samples) * 0.1
            else:
                loo_func = full_eigenfunctions[comp_idx] + np.random.randn(num_samples) * 0.01
            loo_eigenfunctions.append(loo_func)
        
        loo_result = {'eigenfunctions': loo_eigenfunctions}
        loo_file = artifacts_dir / f"loo_subsample_{i}.pkl"
        with open(loo_file, 'wb') as f:
            pickle.dump(loo_result, f)
    
    # Run LOO jackknife
    unstable_modes_path = artifacts_dir / "unstable_modes.json"
    result = run_loo_jackknife(
        full_results_path=full_results_path,
        unstable_modes_path=unstable_modes_path
    )
    
    # Verify file was created
    assert unstable_modes_path.exists(), "unstable_modes.json should be created"
    
    # Verify content
    with open(unstable_modes_path, 'r') as f:
        content = json.load(f)
    
    assert 'threshold' in content
    assert 'unstable_components' in content
    assert 'instability_sources' in content
    assert 'summary' in content
    assert content['threshold'] == STABILITY_THRESHOLD
    
    # Verify summary
    assert content['summary']['num_unstable'] >= 0
    assert content['summary']['num_stable'] >= 0
    assert content['summary']['num_unstable'] + content['summary']['num_stable'] == num_components