"""
Integration test for quickstart validation (Task T034).

This test verifies that the quickstart validation script runs successfully
and produces all expected artifacts.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import load_config
from sieve import compute_phi_linear_sieve, compute_residues, save_residue_dataset
from stats import run_full_statistical_analysis, save_statistical_result
from visualize import plot_bar_frequencies, plot_residual_qq, generate_visualization_report

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test artifacts."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    # Create required directory structure
    os.makedirs("code", exist_ok=True)
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("results/plots", exist_ok=True)
    os.makedirs("results/reports", exist_ok=True)
    os.makedirs("tests/unit", exist_ok=True)
    os.makedirs("tests/integration", exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_quickstart_validation_smoke(temp_test_dir):
    """
    Smoke test for quickstart validation.
    
    Verifies that the pipeline runs end-to-end for a small N value
    and produces all expected output artifacts.
    """
    # Configuration for test
    n_val = 1000
    prime = 3
    
    # Step 1: Compute phi values
    phi_values = compute_phi_linear_sieve(n_val)
    assert len(phi_values) == n_val, f"Expected {n_val} phi values, got {len(phi_values)}"
    
    # Step 2: Compute residues
    residue_counts = compute_residues(phi_values, prime)
    assert len(residue_counts) == prime, f"Expected {prime} residue counts, got {len(residue_counts)}"
    assert sum(residue_counts) == n_val, "Residue counts should sum to N"
    
    # Step 3: Save residue dataset
    residue_path = Path(f"data/raw/residues_{prime}_{n_val}.json")
    save_residue_dataset(residue_counts, prime, n_val, residue_path)
    assert residue_path.exists(), "Residue dataset file should exist"
    
    # Verify JSON structure
    with open(residue_path, 'r') as f:
        residue_data = json.load(f)
    assert 'prime_modulus' in residue_data
    assert 'total_count' in residue_data
    assert 'frequency_map' in residue_data
    assert residue_data['prime_modulus'] == prime
    assert residue_data['total_count'] == n_val
    
    # Step 4: Run statistical analysis
    stats_result = run_full_statistical_analysis(residue_counts, prime, n_val)
    
    # Step 5: Save statistical result
    stats_path = Path(f"data/processed/stats_{prime}_{n_val}.json")
    save_statistical_result(stats_result, stats_path)
    assert stats_path.exists(), "Statistical results file should exist"
    
    # Verify JSON structure
    with open(stats_path, 'r') as f:
        stats_data = json.load(f)
    assert 'test_type' in stats_data
    assert 'p_value' in stats_data
    assert 'method' in stats_data
    assert 'pass_fail_flag' in stats_data
    
    # Step 6: Generate visualizations
    plot_bar_frequencies(residue_counts, prime, n_val)
    plot_residual_qq(stats_result, prime, n_val)
    
    # Check for plot files (they should be created in results/plots/)
    plot_files = list(Path("results/plots").glob(f"*_{prime}_{n_val}.png"))
    assert len(plot_files) >= 2, f"Expected at least 2 plot files, found {len(plot_files)}"
    
    # Step 7: Generate report
    report_path = Path(f"results/reports/summary_{n_val}.md")
    generate_visualization_report(stats_result, prime, n_val, report_path)
    assert report_path.exists(), "Summary report should exist"
    
    # Verify report content
    with open(report_path, 'r') as f:
        report_content = f.read()
    assert f"Prime: {prime}" in report_content
    assert f"N: {n_val}" in report_content
    
    print("✓ Quickstart validation smoke test passed")

def test_error_handling_in_validation(temp_test_dir):
    """
    Test that error handling works correctly during validation.
    
    Verifies that the pipeline fails gracefully when encountering
    invalid inputs or unexpected conditions.
    """
    # Test with invalid prime (should handle gracefully)
    n_val = 100
    invalid_prime = 4  # Not a prime number, but the code should handle it
    
    phi_values = compute_phi_linear_sieve(n_val)
    residue_counts = compute_residues(phi_values, invalid_prime)
    
    # Should produce residue counts for modulus 4
    assert len(residue_counts) == invalid_prime
    
    # Save and verify
    residue_path = Path(f"data/raw/residues_{invalid_prime}_{n_val}.json")
    save_residue_dataset(residue_counts, invalid_prime, n_val, residue_path)
    assert residue_path.exists()
    
    # Statistical analysis should still run (even if results are unexpected)
    stats_result = run_full_statistical_analysis(residue_counts, invalid_prime, n_val)
    assert stats_result is not None
    
    print("✓ Error handling validation test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])