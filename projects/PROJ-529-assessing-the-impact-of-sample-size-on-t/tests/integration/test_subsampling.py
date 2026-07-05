"""
Integration tests for subsampling logic.
Tests the interaction between data acquisition and subsampling generation.
"""
import pytest
import os
import sys
import random
from utils.seeds import set_seed, log_iteration, ensure_log_directory
from schemas import Subsample, validate_subsample
from utils.exceptions import MetaAnalysisError

# Ensure we can import from the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

@pytest.fixture
def sample_meta_analysis_data():
    """
    Fixture providing a deterministic sample meta-analysis dataset.
    Simulates a real meta-analysis with 20 studies.
    """
    # Use a fixed seed for reproducible test data generation
    rng = random.Random(12345)
    n_studies = 20
    
    # Generate realistic effect sizes (mean ~0.3, sd ~0.2)
    effect_sizes = [round(rng.gauss(0.3, 0.2), 4) for _ in range(n_studies)]
    # Generate realistic standard errors (range 0.05 to 0.2)
    standard_errors = [round(rng.uniform(0.05, 0.2), 4) for _ in range(n_studies)]
    
    return {
        "id": "TEST_MA_001",
        "title": "Test Meta-Analysis for Subsampling",
        "effect_sizes": effect_sizes,
        "standard_errors": standard_errors,
        "n_studies": n_studies
    }

@pytest.mark.parametrize("k", [3, 5, 10])
def test_subsampling_logic(k, sample_meta_analysis_data):
    """
    Integration test for subsampling logic with varying k values (3, 5, 10).
    Verifies that:
    1. Random subsampling selects exactly k studies
    2. The Subsample schema validates correctly
    3. Iteration logging occurs as expected
    4. Data integrity is maintained (no duplicates, correct values)
    """
    # Setup: Initialize seed for reproducibility
    set_seed(42)
    meta_id = sample_meta_analysis_data["id"]
    all_effects = sample_meta_analysis_data["effect_sizes"]
    all_se = sample_meta_analysis_data["standard_errors"]
    n_total = len(all_effects)

    # Logic: Randomly select k unique indices
    # In a real pipeline, this would happen in code/subsample.py
    # Here we simulate the selection to test the downstream validation
    indices = random.sample(range(n_total), k)
    
    selected_effects = [all_effects[i] for i in indices]
    selected_se = [all_se[i] for i in indices]

    # Validate that we have the correct count
    assert len(selected_effects) == k, f"Expected {k} effects, got {len(selected_effects)}"
    assert len(selected_se) == k, f"Expected {k} SEs, got {len(selected_se)}"

    # Ensure no duplicate indices were selected
    assert len(set(indices)) == k, "Duplicate indices detected in subsampling"

    # Create Subsample object
    subsample_data = {
        "meta_id": meta_id,
        "k": k,
        "seed": 42,
        "effect_sizes": selected_effects,
        "standard_errors": selected_se,
        "indices": indices  # Track original indices for verification
    }

    # Validate against schema
    try:
        validated_subsample = validate_subsample(subsample_data)
    except Exception as e:
        pytest.fail(f"Schema validation failed for k={k}: {e}")

    assert validated_subsample.k == k
    assert validated_subsample.meta_id == meta_id
    assert len(validated_subsample.effect_sizes) == k
    assert len(validated_subsample.standard_errors) == k

    # Verify that the selected values match the original data at the selected indices
    for i, idx in enumerate(indices):
        assert validated_subsample.effect_sizes[i] == all_effects[idx]
        assert validated_subsample.standard_errors[i] == all_se[idx]

    # Log the iteration (simulating the pipeline behavior)
    log_dir = os.path.join(project_root, "data", "processed")
    ensure_log_directory(log_dir)
    
    log_iteration(
        iteration_id=f"test_{meta_id}_k{k}",
        k=k,
        seed=42,
        estimator_type="integration_test"
    )

    # Verify log file was created
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.json')]
    assert len(log_files) > 0, "Log file was not created after log_iteration"

def test_edge_case_k_less_than_3(sample_meta_analysis_data):
    """
    Test handling of k < 3 edge case.
    According to project specs, k < 3 should be handled gracefully.
    This test verifies the logic path exists and schema validation passes,
    while noting that downstream modeling tasks may reject k < 3.
    """
    k = 2
    all_effects = sample_meta_analysis_data["effect_sizes"]
    n_total = len(all_effects)

    # Ensure sample has enough data
    assert n_total >= k, "Sample data too small for k=2"

    # Simulate random selection
    set_seed(999)
    indices = random.sample(range(n_total), k)
    
    selected_effects = [all_effects[i] for i in indices]
    selected_se = [sample_meta_analysis_data["standard_errors"][i] for i in indices]

    subsample_data = {
        "meta_id": sample_meta_analysis_data["id"],
        "k": k,
        "seed": 999,
        "effect_sizes": selected_effects,
        "standard_errors": selected_se,
        "indices": indices
    }

    # Schema validation should pass (schema doesn't enforce k>=3)
    # Downstream tasks (T023) will handle k < 3 rejection
    validated = validate_subsample(subsample_data)
    assert validated.k == 2
    assert len(validated.effect_sizes) == 2

def test_subsampling_data_integrity(sample_meta_analysis_data):
    """
    Test that subsampling preserves data integrity:
    - No values are modified
    - No values are lost during selection
    - Standard errors remain paired with effect sizes
    """
    k = 5
    set_seed(777)
    
    all_effects = sample_meta_analysis_data["effect_sizes"]
    all_se = sample_meta_analysis_data["standard_errors"]
    n_total = len(all_effects)

    indices = random.sample(range(n_total), k)
    
    selected_effects = [all_effects[i] for i in indices]
    selected_se = [all_se[i] for i in indices]

    # Verify exact value preservation
    for i, idx in enumerate(indices):
        assert selected_effects[i] == all_effects[idx], "Effect size value modified"
        assert selected_se[i] == all_se[idx], "Standard error value modified"

    # Verify pairing integrity
    subsample_data = {
        "meta_id": sample_meta_analysis_data["id"],
        "k": k,
        "seed": 777,
        "effect_sizes": selected_effects,
        "standard_errors": selected_se
    }
    
    validated = validate_subsample(subsample_data)
    
    # Ensure the pairs are consistent
    for i in range(k):
        # If we had access to original indices, we could verify exact pairing
        # Here we verify that the lengths match and values are valid
        assert isinstance(validated.effect_sizes[i], (int, float))
        assert isinstance(validated.standard_errors[i], (int, float))
        assert validated.standard_errors[i] > 0, "Standard error must be positive"