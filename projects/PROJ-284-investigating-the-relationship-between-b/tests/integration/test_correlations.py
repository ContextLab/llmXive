"""
Integration test for correlation analysis with synthetic data.

This test verifies that the correlation analysis pipeline correctly computes
Spearman/Pearson correlation coefficients, p-values, and FDR-corrected q-values
using synthetic data with known ground truth relationships.

Dependencies:
  - T020: Functional connectivity matrix builder
  - T021: Graph metric extractor
  - T022: Aggregation logic for node-level metrics
  - T024: Correlation with covariate implementation
  - T025: Benjamini-Hochberg FDR correction
  
This test is marked as [P] (parallel) as it operates on synthetic data
and does not depend on actual HCP data or preprocessing outputs.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from models import Subject, ConnectivityMatrix, NetworkMetric, CorrelationResult
from analysis.correlations import compute_correlations, apply_fdr_correction


def generate_synthetic_dataset(n_subjects=100, seed=42):
    """
    Generate synthetic dataset with known correlation structure.
    
    Creates:
      - Network metrics (modularity, global_efficiency, participation_coef, within_module_degree)
      - Behavioral scores (motor_score)
      - Framewise Displacement (fd) as covariate
    
    Ground truth:
      - modularity has r ≈ 0.45 with motor_score
      - global_efficiency has r ≈ -0.35 with motor_score
      - participation_coef has r ≈ 0.10 (weak, likely non-significant)
      - within_module_degree has r ≈ 0.00 (no correlation)
    """
    np.random.seed(seed)
    
    # Generate covariate (FD) - small positive correlation with some metrics
    fd = np.random.normal(0.2, 0.1, n_subjects)
    fd = np.clip(fd, 0.05, 0.5)  # Keep within realistic range
    
    # Generate network metrics with known correlations
    # Modularity: r ≈ 0.45
    modularity = np.random.normal(0.5, 0.1, n_subjects)
    
    # Global Efficiency: r ≈ -0.35
    global_efficiency = np.random.normal(0.35, 0.08, n_subjects)
    
    # Participation Coefficient: r ≈ 0.10 (weak)
    participation_coef = np.random.normal(0.25, 0.05, n_subjects)
    
    # Within-Module Degree: r ≈ 0.00 (no correlation)
    within_module_degree = np.random.normal(1.2, 0.15, n_subjects)
    
    # Generate motor scores with controlled correlations
    # motor_score = a*modularity + b*global_efficiency + c*participation_coef + noise
    motor_score = (
        1.5 * modularity +
        -1.0 * global_efficiency +
        0.3 * participation_coef +
        np.random.normal(0, 0.2, n_subjects)
    )
    
    # Create DataFrame
    data = pd.DataFrame({
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'modularity': modularity,
        'global_efficiency': global_efficiency,
        'participation_coef': participation_coef,
        'within_module_degree': within_module_degree,
        'motor_score': motor_score,
        'fd': fd
    })
    
    return data


def test_correlation_with_synthetic_data():
    """
    Integration test: Verify correlation analysis with synthetic data.
    
    This test:
      1. Generates synthetic data with known ground truth correlations
      2. Runs the correlation analysis pipeline
      3. Verifies that computed r, p, and q values match expected ranges
      4. Confirms FDR correction is applied correctly
    """
    # Generate synthetic dataset
    data = generate_synthetic_dataset(n_subjects=100, seed=42)
    
    # Define metrics to test
    metrics = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    outcome = 'motor_score'
    covariate = 'fd'
    
    # Run correlation analysis
    results = compute_correlations(
        df=data,
        metric_columns=metrics,
        outcome_column=outcome,
        covariate_column=covariate,
        method='spearman'
    )
    
    # Verify results structure
    assert isinstance(results, list), "Results should be a list of CorrelationResult objects"
    assert len(results) == len(metrics), f"Expected {len(metrics)} results, got {len(results)}"
    
    # Verify each result has expected attributes
    for result in results:
        assert isinstance(result, CorrelationResult), "Each result should be a CorrelationResult"
        assert hasattr(result, 'metric_name'), "Result should have metric_name"
        assert hasattr(result, 'r'), "Result should have r (correlation coefficient)"
        assert hasattr(result, 'p'), "Result should have p (p-value)"
        assert hasattr(result, 'q'), "Result should have q (FDR-corrected p-value)"
        assert hasattr(result, 'significant'), "Result should have significant flag"
        assert hasattr(result, 'covariate_controlled'), "Result should have covariate_controlled flag"
    
    # Extract results for validation
    result_dict = {r.metric_name: r for r in results}
    
    # Validate modularity: should have strong positive correlation (r ≈ 0.45)
    modularity_result = result_dict['modularity']
    assert 0.3 < modularity_result.r < 0.6, f"Modularity r should be ~0.45, got {modularity_result.r}"
    assert modularity_result.p < 0.01, f"Modularity p should be < 0.01, got {modularity_result.p}"
    assert modularity_result.q < 0.05, f"Modularity q should be < 0.05, got {modularity_result.q}"
    assert modularity_result.significant, "Modularity should be significant after FDR"
    
    # Validate global_efficiency: should have moderate negative correlation (r ≈ -0.35)
    eff_result = result_dict['global_efficiency']
    assert -0.5 < eff_result.r < -0.2, f"Global efficiency r should be ~-0.35, got {eff_result.r}"
    assert eff_result.p < 0.05, f"Global efficiency p should be < 0.05, got {eff_result.p}"
    assert eff_result.q < 0.05, f"Global efficiency q should be < 0.05, got {eff_result.q}"
    assert eff_result.significant, "Global efficiency should be significant after FDR"
    
    # Validate participation_coef: weak correlation (r ≈ 0.10), may or may not be significant
    part_result = result_dict['participation_coef']
    assert -0.1 < part_result.r < 0.3, f"Participation coef r should be ~0.10, got {part_result.r}"
    # p-value should be higher than modularity and global_efficiency
    assert part_result.p > modularity_result.p, "Participation coef p should be higher than modularity"
    
    # Validate within_module_degree: no correlation (r ≈ 0.00)
    wmd_result = result_dict['within_module_degree']
    assert -0.2 < wmd_result.r < 0.2, f"Within-module degree r should be ~0.00, got {wmd_result.r}"
    assert wmd_result.p > 0.05, f"Within-module degree p should be > 0.05, got {wmd_result.p}"
    assert not wmd_result.significant, "Within-module degree should NOT be significant"
    
    # Validate FDR correction logic
    # q-values should be >= p-values (FDR correction increases p-values)
    for result in results:
        assert result.q >= result.p, f"q-value should be >= p-value for {result.metric_name}"
    
    # Validate covariate control
    for result in results:
        assert result.covariate_controlled, "All results should be covariate-controlled"
    
    # Additional check: verify that significant metrics have q < 0.05
    significant_metrics = [r for r in results if r.significant]
    for result in significant_metrics:
        assert result.q < 0.05, f"Significant metric {result.metric_name} should have q < 0.05"
    
    print(f"✅ Correlation analysis test passed!")
    print(f"   - Modularity: r={modularity_result.r:.3f}, p={modularity_result.p:.4f}, q={modularity_result.q:.4f}")
    print(f"   - Global Efficiency: r={eff_result.r:.3f}, p={eff_result.p:.4f}, q={eff_result.q:.4f}")
    print(f"   - Participation Coef: r={part_result.r:.3f}, p={part_result.p:.4f}, q={part_result.q:.4f}")
    print(f"   - Within-Module Degree: r={wmd_result.r:.3f}, p={wmd_result.p:.4f}, q={wmd_result.q:.4f}")
    print(f"   - Significant metrics: {[r.metric_name for r in significant_metrics]}")

if __name__ == '__main__':
    test_correlation_with_synthetic_data()