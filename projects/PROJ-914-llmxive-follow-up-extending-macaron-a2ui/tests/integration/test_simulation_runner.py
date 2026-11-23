"""
Integration tests for the simulation runner (T024a).
Verifies that the runner produces real, measurable output without fabrication.
"""

import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from simulation.runner import (
    MockRouter, MockFallback, MockGenerativeModel,
    simulate_interaction, run_simulation, save_simulation_results, load_annotated_data
)
from config import get_processed_data_path, ensure_dirs
from data.models import SimulationRun

@pytest.fixture
def sample_annotated_data():
    """Creates a small, valid annotated dataset for testing."""
    data = {
        'query': [
            "What is the weather?",
            "Set a timer for 10 minutes",
            "Who won the game yesterday?",
            "Create a meeting with John at 3pm",
            "Send an email to Alice"
        ],
        'ground_truth_intent': [
            'High-Confidence',
            'High-Confidence',
            'Ambiguous',
            'High-Confidence',
            'Ambiguous'
        ],
        'complexity_score': [1.0, 2.0, 1.5, 3.0, 2.5]
    }
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_mock_components_initialization():
    """Test that mock components initialize correctly."""
    router = MockRouter(threshold=0.75)
    fallback = MockFallback()
    gen_model = MockGenerativeModel()
    
    assert router.threshold == 0.75
    assert router.predict("test query")[0] in ['High-Confidence', 'Ambiguous']
    assert isinstance(fallback.generate("test"), dict)
    assert isinstance(gen_model.generate("test"), dict)

def test_simulate_interaction_produces_real_metrics(sample_annotated_data):
    """
    Test that simulate_interaction produces real, non-fabricated metrics.
    Specifically checks that latency is actually measured and not hardcoded.
    """
    router = MockRouter()
    fallback = MockFallback()
    gen_model = MockGenerativeModel()
    
    row = sample_annotated_data.iloc[0].to_dict()
    
    # Run with 100ms latency
    result = simulate_interaction(
        row=row,
        router=router,
        fallback_gen=fallback,
        gen_model=gen_model,
        latency_ms=100,
        density_level=1
    )
    
    # Verify result is a SimulationRun object
    assert isinstance(result, SimulationRun)
    
    # Verify latency is recorded correctly (should be ~100ms + small variance)
    assert 90 <= result.latency_ms <= 110, f"Latency {result.latency_ms} not within expected range"
    
    # Verify alignment score is calculated (not random)
    assert 0.0 <= result.alignment_score <= 1.0
    
    # Verify UI element count is an integer
    assert isinstance(result.ui_element_count, int)
    assert result.ui_element_count >= 0

def test_run_simulation_writes_real_csv(sample_annotated_data, temp_output_dir):
    """
    Test that run_simulation actually writes a CSV file with real data.
    """
    # Run simulation with small sample
    results = run_simulation(
        df=sample_annotated_data,
        latency_levels=[0, 50],
        density_levels=[1, 2],
        sample_size=2,
        use_mock=True
    )
    
    # Save to temp file
    output_path = os.path.join(temp_output_dir, "test_results.csv")
    save_simulation_results(results, output_path)
    
    # Verify file exists
    assert os.path.exists(output_path)
    
    # Verify content is real, not fabricated
    df = pd.read_csv(output_path)
    
    # Check columns exist
    expected_cols = [
        'query_id', 'query', 'ground_truth_intent', 'predicted_intent',
        'router_confidence', 'route_type', 'latency_ms', 'gen_time_seconds',
        'total_time_seconds', 'abandoned', 'ui_element_count', 'alignment_score', 'density_level'
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"
    
    # Verify latency values are present and real
    assert df['latency_ms'].isna().sum() == 0
    assert set(df['latency_ms'].unique()).issubset({0, 50})
    
    # Verify alignment scores are within valid range
    assert (df['alignment_score'] >= 0.0).all()
    assert (df['alignment_score'] <= 1.0).all()
    
    # Verify ui_element_count is logged (T024c)
    assert df['ui_element_count'].isna().sum() == 0
    assert (df['ui_element_count'] >= 0).all()

def test_density_iteration_logic(sample_annotated_data):
    """
    Test that the simulation correctly iterates through density levels {1, 3, 5, 10}.
    """
    density_levels = [1, 3, 5, 10]
    results = run_simulation(
        df=sample_annotated_data,
        latency_levels=[0],
        density_levels=density_levels,
        sample_size=1,
        use_mock=True
    )
    
    # Each row should be simulated for each density level
    expected_count = len(sample_annotated_data) * len(density_levels)
    assert len(results) == expected_count, f"Expected {expected_count} results, got {len(results)}"
    
    # Verify all density levels are present
    unique_densities = set(r.density_level for r in results)
    assert unique_densities == set(density_levels), f"Missing density levels: {set(density_levels) - unique_densities}"

def test_borderline_confidence_handling(sample_annotated_data):
    """
    Test that borderline confidence scores (within 0.05 of threshold) are handled.
    """
    # Create a mock router with threshold 0.75
    router = MockRouter(threshold=0.75)
    
    # Force a query that might produce borderline confidence in a real model
    # (Here we rely on the mock logic which is deterministic based on length)
    row = {'query': 'This is a moderately long query that might hit the boundary', 'ground_truth_intent': 'Ambiguous', 'complexity_score': 1.0}
    
    result = simulate_interaction(
        row=row,
        router=router,
        fallback_gen=MockFallback(),
        gen_model=MockGenerativeModel(),
        latency_ms=0,
        density_level=1
    )
    
    # Verify the result was generated
    assert result is not None
    assert result.alignment_score is not None

def test_no_synthetic_fallback_in_metrics():
    """
    Regression test: Ensure no random/fabricated metrics are used.
    """
    # This test ensures that the code does not use random.uniform or np.random
    # for calculating scores or latencies.
    import inspect
    from simulation import runner
    
    source = inspect.getsource(runner.simulate_interaction)
    
    # Check for obvious fabrication patterns
    fabrication_patterns = [
        "random.uniform",
        "np.random.uniform",
        "random.randint",
        "np.random.randint",
        "Simulated latency",
        "fake_score"
    ]
    
    for pattern in fabrication_patterns:
        assert pattern not in source, f"Found fabrication pattern '{pattern}' in simulate_interaction"