import pytest
import random
from utils.io import cap_dataset_stratified

def test_cap_dataset_under_limit():
    """Test that dataset under limit is returned unchanged."""
    data = [
        {"composition": "A", "alloy_system": "Fe", "phase": "amorphous"},
        {"composition": "B", "alloy_system": "Fe", "phase": "crystalline"},
    ]
    result = cap_dataset_stratified(data, max_size=100)
    assert len(result) == 2
    assert result == data

def test_cap_dataset_exact_limit():
    """Test that dataset exactly at limit is returned unchanged."""
    data = [{"composition": f"i", "alloy_system": "Fe", "phase": "amorphous"} for i in range(100)]
    result = cap_dataset_stratified(data, max_size=100)
    assert len(result) == 100

def test_cap_dataset_stratification_preserved():
    """Test that stratified sampling preserves proportions."""
    # Create a dataset with 80% Fe and 20% Cu
    data = []
    for i in range(800):
        data.append({"composition": f"Fe_{i}", "alloy_system": "Fe", "phase": "amorphous"})
    for i in range(200):
        data.append({"composition": f"Cu_{i}", "alloy_system": "Cu", "phase": "amorphous"})
    
    # Cap at 100
    result = cap_dataset_stratified(data, max_size=100)
    
    # Check total size
    assert len(result) == 100
    
    # Check proportions (allowing for small rounding errors)
    fe_count = sum(1 for item in result if item["alloy_system"] == "Fe")
    cu_count = sum(1 for item in result if item["alloy_system"] == "Cu")
    
    # Expected: 80 Fe, 20 Cu
    assert fe_count == 80
    assert cu_count == 20

def test_cap_dataset_missing_system_key():
    """Test handling of missing alloy_system key."""
    data = [
        {"composition": "A", "phase": "amorphous"}, # missing key
        {"composition": "B", "alloy_system": "Fe", "phase": "amorphous"},
    ]
    # Should not crash and should handle 'unknown'
    result = cap_dataset_stratified(data, max_size=10)
    assert len(result) == 2

def test_cap_dataset_randomness():
    """Test that sampling is random (different runs yield different samples)."""
    # Create a large dataset where we can sample multiple subsets
    data = [{"composition": f"i", "alloy_system": "Fe", "phase": "amorphous"} for i in range(1000)]
    
    # Run twice
    random.seed(42)
    result1 = cap_dataset_stratified(data, max_size=100)
    
    random.seed(43)
    result2 = cap_dataset_stratified(data, max_size=100)
    
    # They should be different sets of compositions
    ids1 = set(item["composition"] for item in result1)
    ids2 = set(item["composition"] for item in result2)
    
    # Probability of them being identical is extremely low for N=1000, K=100
    assert ids1 != ids2, "Stratified sampling should produce different results with different seeds"
