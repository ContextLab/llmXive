"""
Test script for concentration parameter tuning logic (T025).

This script verifies that:
1. Active component counting works correctly
2. Concentration parameter adjustment responds to component count
3. Adaptive updates maintain components within target range
"""
import sys
import numpy as np
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.dpgmm import DPGMMModel
from src.models.anomaly_score import AnomalyScore


def test_active_component_counting() -> bool:
    """Test that active component counting works correctly."""
    print("=" * 60)
    print("TEST: Active Component Counting")
    print("=" * 60)
    
    model = DPGMMModel(n_features=1, alpha=1.0)
    
    # Test with no components
    model._mixture_weights = None
    count = model._compute_active_components()
    assert count == 0, f"Expected 0 components, got {count}"
    print("✓ No components case: PASS")
    
    # Test with some active components
    model._mixture_weights = np.array([0.5, 0.3, 0.1, 0.0001])  # 3 active
    count = model._compute_active_components()
    assert count == 3, f"Expected 3 active components, got {count}"
    print("✓ Mixed weights case: PASS")
    
    # Test with all negligible weights
    model._mixture_weights = np.array([1e-10, 1e-12, 1e-15])
    count = model._compute_active_components()
    assert count == 0, f"Expected 0 active components, got {count}"
    print("✓ Negligible weights case: PASS")
    
    return True


def test_concentration_adjustment() -> bool:
    """Test that concentration parameter adjusts correctly."""
    print("\n" + "=" * 60)
    print("TEST: Concentration Parameter Adjustment")
    print("=" * 60)
    
    model = DPGMMModel(n_features=1, alpha=1.0)
    
    # Test increase when too few components
    model._mixture_weights = np.array([0.99])  # Only 1 active
    old_alpha = model._alpha
    new_alpha = model._tune_concentration_parameter(
        target_min_components=2,
        target_max_components=5,
        adjustment_factor=1.1
    )
    assert new_alpha > old_alpha, "Alpha should increase when too few components"
    print(f"✓ Too few components: alpha {old_alpha:.4f} → {new_alpha:.4f}")
    
    # Test decrease when too many components
    model._mixture_weights = np.array([0.3, 0.25, 0.2, 0.15, 0.05, 0.03, 0.02])  # 7 active
    old_alpha = model._alpha
    new_alpha = model._tune_concentration_parameter(
        target_min_components=2,
        target_max_components=5,
        adjustment_factor=1.1
    )
    assert new_alpha < old_alpha, "Alpha should decrease when too many components"
    print(f"✓ Too many components: alpha {old_alpha:.4f} → {new_alpha:.4f}")
    
    # Test no change when within range
    model._mixture_weights = np.array([0.4, 0.35, 0.25])  # 3 active, within [2, 5]
    old_alpha = model._alpha
    new_alpha = model._tune_concentration_parameter(
        target_min_components=2,
        target_max_components=5,
        adjustment_factor=1.1
    )
    assert np.isclose(new_alpha, old_alpha), "Alpha should not change when within range"
    print(f"✓ Within range: alpha unchanged at {new_alpha:.4f}")
    
    return True


def test_adaptive_update() -> bool:
    """Test the adaptive update method."""
    print("\n" + "=" * 60)
    print("TEST: Adaptive Concentration Update")
    print("=" * 60)
    
    model = DPGMMModel(n_features=1, alpha=1.0)
    
    # Simulate observations at update interval
    model._mixture_weights = np.array([0.5, 0.3, 0.15, 0.05])  # 4 active
    
    # Call at update interval
    result = model.adaptive_concentration_update(
        n_observations=100,
        min_active_components=2,
        max_active_components=5,
        update_interval=100,
        adjustment_factor=1.1
    )
    
    assert result is not None, "Should return result at update interval"
    assert result['n_observations'] == 100
    assert result['active_components'] == 4
    print(f"✓ Adaptive update at 100 obs: {result}")
    
    # Call between intervals (should return None)
    result = model.adaptive_concentration_update(
        n_observations=150,
        min_active_components=2,
        max_active_components=5,
        update_interval=100,
        adjustment_factor=1.1
    )
    assert result is None, "Should return None between update intervals"
    print("✓ No update between intervals: PASS")
    
    return True


def test_concentration_status() -> bool:
    """Test getting concentration status."""
    print("\n" + "=" * 60)
    print("TEST: Concentration Status")
    print("=" * 60)
    
    model = DPGMMModel(n_features=1, alpha=2.5)
    model._mixture_weights = np.array([0.6, 0.3, 0.09, 0.01])
    
    status = model.get_concentration_status()
    
    assert 'concentration_parameter' in status
    assert 'active_components' in status
    assert status['concentration_parameter'] == 2.5
    assert status['active_components'] == 3  # Last one is negligible
    print(f"✓ Status: {status}")
    
    return True


def test_alpha_bounds() -> bool:
    """Test that alpha stays within bounds."""
    print("\n" + "=" * 60)
    print("TEST: Alpha Bounds Enforcement")
    print("=" * 60)
    
    model = DPGMMModel(n_features=1, alpha=0.001)  # Below min
    model._mixture_weights = np.array([0.99])  # Too few components
    
    new_alpha = model._tune_concentration_parameter(
        target_min_components=2,
        target_max_components=5,
        adjustment_factor=1.1
    )
    
    assert new_alpha >= 0.01, f"Alpha should be bounded below by 0.01, got {new_alpha}"
    print(f"✓ Lower bound enforced: alpha = {new_alpha:.4f}")
    
    model = DPGMMModel(n_features=1, alpha=500.0)  # Above max
    model._mixture_weights = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])  # Many components
    
    new_alpha = model._tune_concentration_parameter(
        target_min_components=2,
        target_max_components=5,
        adjustment_factor=1.1
    )
    
    assert new_alpha <= 100.0, f"Alpha should be bounded above by 100.0, got {new_alpha}"
    print(f"✓ Upper bound enforced: alpha = {new_alpha:.4f}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("CONCENTRATION PARAMETER TUNING TEST SUITE (T025)")
    print("=" * 70 + "\n")
    
    tests = [
        ("Active Component Counting", test_active_component_counting),
        ("Concentration Adjustment", test_concentration_adjustment),
        ("Adaptive Update", test_adaptive_update),
        ("Concentration Status", test_concentration_status),
        ("Alpha Bounds", test_alpha_bounds),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    for name, passed, error in results:
        status = "✓ PASS" if passed else f"✗ FAIL: {error}"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED - Concentration tuning logic verified!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
