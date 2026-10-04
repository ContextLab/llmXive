import json
import os
import pytest
from stats import StatisticalResult, save_statistical_result, load_statistical_result, run_sieve_analysis

def test_save_statistical_result(tmp_path):
    """Test that StatisticalResult is correctly serialized to JSON."""
    result = StatisticalResult(
        prime=3,
        N=1000,
        chi_squared_statistic=2.5,
        chi_squared_p_value=0.28,
        exact_test_p_value=None,
        block_bootstrap_p_value=0.30,
        error_term_residual=1.2,
        primary_pass_fail=True,
        bonferroni_pass_fail=True,
        degrees_of_freedom=2,
        observed_counts={0: 330, 1: 340, 2: 330},
        expected_counts={0: 333.33, 1: 333.33, 2: 333.33}
    )
    
    output_file = tmp_path / "stats_3_1000.json"
    save_statistical_result(result, str(output_file))
    
    assert output_file.exists()
    
    # Verify content
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert data['prime'] == 3
    assert data['N'] == 1000
    assert abs(data['chi_squared_statistic'] - 2.5) < 0.01
    assert data['primary_pass_fail'] is True

def test_load_statistical_result(tmp_path):
    """Test loading a StatisticalResult from JSON."""
    result = StatisticalResult(
        prime=5,
        N=5000,
        chi_squared_statistic=10.0,
        chi_squared_p_value=0.04,
        exact_test_p_value=0.03,
        block_bootstrap_p_value=0.05,
        error_term_residual=0.9,
        primary_pass_fail=False,
        bonferroni_pass_fail=False,
        degrees_of_freedom=4,
        observed_counts={0: 1000, 1: 1000, 2: 1000, 3: 1000, 4: 1000},
        expected_counts={0: 1000.0, 1: 1000.0, 2: 1000.0, 3: 1000.0, 4: 1000.0}
    )
    
    output_file = tmp_path / "stats_5_5000.json"
    save_statistical_result(result, str(output_file))
    
    loaded = load_statistical_result(str(output_file))
    
    assert loaded.prime == 5
    assert loaded.N == 5000
    assert loaded.chi_squared_p_value == 0.04
    assert loaded.exact_test_p_value == 0.03
    assert loaded.primary_pass_fail is False

def test_run_sieve_analysis_integration(tmp_path):
    """
    Integration test for run_sieve_analysis.
    Requires input data to be present.
    This test creates dummy input data and verifies the output file is created.
    """
    # Setup directories
    data_raw = tmp_path / "data" / "raw"
    data_processed = tmp_path / "data" / "processed"
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    
    # Create dummy residue counts file (T013 output)
    input_file = data_raw / "residues_3_100.json"
    input_data = {
        "counts": {"0": 33, "1": 34, "2": 33},
        "prime": 3,
        "N": 100
    }
    with open(input_file, 'w') as f:
        json.dump(input_data, f)
    
    # Create dummy residue sequence file (for Bootstrap)
    seq_file = data_raw / "residues_sequence_3_100.json"
    seq_data = [0] * 33 + [1] * 34 + [2] * 33 # Dummy sequence
    with open(seq_file, 'w') as f:
        json.dump(seq_data, f)
    
    # Run analysis
    # Note: This will use placeholder logic for stats, but should produce a file.
    try:
        results = run_sieve_analysis(N=100, primes=[3], seed=42)
        assert 3 in results
        output_file = results[3]
        assert os.path.exists(output_file)
        
        # Verify structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        assert 'chi_squared_statistic' in data
        assert 'block_bootstrap_p_value' in data
        assert 'error_term_residual' in data
    except Exception as e:
        # If dependencies (like scipy) are missing or logic fails, we catch it.
        # But for the task to be "completed", the code must be runnable.
        # We assume scipy is available or the placeholder logic handles it.
        pytest.fail(f"run_sieve_analysis failed: {e}")