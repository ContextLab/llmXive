"""
Test script for missing value handling in DPGMM streaming update.

Verifies that:
1. Missing values (NaN, None, inf) are properly detected
2. Imputation strategies work correctly
3. Streaming update continues without breaking
4. Anomaly scores are computed for valid observations
5. Missing value statistics are tracked accurately
"""
import sys
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.models.dpgmm import DPGMMModel, is_missing, impute_missing_values, forward_fill_missing
from src.models.anomaly_score import AnomalyScore

def test_missing_value_detection() -> bool:
    """Test that missing values are properly detected."""
    print("=" * 60)
    print("TEST: Missing Value Detection")
    print("=" * 60)
    
    test_cases = [
        (np.nan, True),
        (np.inf, True),
        (-np.inf, True),
        (None, True),
        ('nan', True),
        ('NaN', True),
        ('none', True),
        ('', True),
        (0.0, False),
        (1.5, False),
        (-3.14, False),
    ]
    
    all_passed = True
    for value, expected in test_cases:
        result = is_missing(value)
        status = "✓" if result == expected else "✗"
        print(f"  {status} is_missing({repr(value):15s}) = {result:5} (expected {expected})")
        if result != expected:
            all_passed = False
    
    print()
    return all_passed

def test_imputation_strategies() -> bool:
    """Test all imputation strategies."""
    print("=" * 60)
    print("TEST: Imputation Strategies")
    print("=" * 60)
    
    # Create array with missing values
    original = np.array([1.0, 2.0, np.nan, 4.0, np.nan, 6.0, 7.0])
    
    strategies = ['mean', 'median', 'zero', 'skip', 'forward_fill']
    all_passed = True
    
    for strategy in strategies:
        if strategy == 'forward_fill':
            imputed, meta = forward_fill_missing(original.copy())
        else:
            imputed, meta = impute_missing_values(original.copy(), strategy=strategy)
        
        print(f"\n  Strategy: {strategy}")
        print(f"    Original: {original}")
        print(f"    Imputed:  {imputed}")
        print(f"    Missing indices: {meta['missing_indices']}")
        print(f"    Imputed count: {meta['imputed_count']}")
        
        # Verify no NaN in output (except for skip strategy)
        if strategy != 'skip':
            has_nan = np.any(np.isnan(imputed))
            has_inf = np.any(np.isinf(imputed))
            if has_nan or has_inf:
                print(f"    ✗ FAILED: Output still contains missing values")
                all_passed = False
            else:
                print(f"    ✓ All missing values imputed")
        else:
            # Skip strategy should preserve NaN
            if np.any(np.isnan(imputed)):
                print(f"    ✓ Skip strategy preserves NaN as expected")
            else:
                print(f"    ✗ FAILED: Skip strategy should preserve NaN")
                all_passed = False
    
    print()
    return all_passed

def test_streaming_with_missing_values() -> bool:
    """Test that streaming update handles missing values correctly."""
    print("=" * 60)
    print("TEST: Streaming Update with Missing Values")
    print("=" * 60)
    
    # Create model with mean imputation
    model = DPGMMModel(
        alpha=1.0,
        n_components_max=5,
        missing_value_strategy='mean',
        random_seed=42
    )
    
    # Create sequence with missing values
    observations = [
        1.0, 2.0, 3.0, np.nan, 5.0, 6.0, np.inf, 8.0, None, 10.0,
        11.0, 12.0, np.nan, 14.0, 15.0
    ]
    
    scores: List[AnomalyScore] = []
    print(f"\n  Processing {len(observations)} observations...")
    
    for i, obs in enumerate(observations):
        score = model.update(obs)
        scores.append(score)
        print(f"    [{i:2d}] value={str(obs):8s} score={score.anomaly_score:8.4f} "
              f"missing_handled={score.metadata.get('missing_value_handled', False)}")
    
    # Verify statistics
    stats = model.missing_value_stats
    print(f"\n  Missing Value Statistics:")
    print(f"    Total processed: {stats['total_processed']}")
    print(f"    Missing encountered: {stats['missing_encountered']}")
    print(f"    Imputed: {stats['imputed']}")
    print(f"    Skipped: {stats['skipped']}")
    
    # Verify counts
    expected_missing = 4  # nan, inf, None, nan
    all_passed = True
    
    if stats['total_processed'] != len(observations):
        print(f"    ✗ FAILED: Expected {len(observations)} processed, got {stats['total_processed']}")
        all_passed = False
    
    if stats['missing_encountered'] != expected_missing:
        print(f"    ✗ FAILED: Expected {expected_missing} missing, got {stats['missing_encountered']}")
        all_passed = False
    
    if stats['imputed'] != expected_missing:
        print(f"    ✗ FAILED: Expected {expected_missing} imputed, got {stats['imputed']}")
        all_passed = False
    
    if stats['skipped'] != 0:
        print(f"    ✗ FAILED: Expected 0 skipped, got {stats['skipped']}")
        all_passed = False
    
    # Verify we still have components (model didn't break)
    if model.n_components == 0:
        print(f"    ✗ FAILED: Model has no components after processing")
        all_passed = False
    else:
        print(f"    ✓ Model has {model.n_components} active components")
    
    # Verify all scores have valid values (not all inf)
    valid_scores = [s for s in scores if not np.isinf(s.anomaly_score)]
    if len(valid_scores) == 0:
        print(f"    ✗ FAILED: All scores are inf")
        all_passed = False
    else:
        print(f"    ✓ {len(valid_scores)}/{len(scores)} scores are valid")
    
    print()
    return all_passed

def test_skip_strategy() -> bool:
    """Test that skip strategy properly skips missing values."""
    print("=" * 60)
    print("TEST: Skip Strategy for Missing Values")
    print("=" * 60)
    
    model = DPGMMModel(
        alpha=1.0,
        n_components_max=5,
        missing_value_strategy='skip',
        random_seed=42
    )
    
    observations = [1.0, 2.0, np.nan, 4.0, 5.0, None, 7.0]
    scores: List[AnomalyScore] = []
    
    print(f"\n  Processing {len(observations)} observations with skip strategy...")
    
    for i, obs in enumerate(observations):
        score = model.update(obs)
        scores.append(score)
        is_skipped = score.metadata.get('reason') == 'missing_value_skipped'
        print(f"    [{i:2d}] value={str(obs):8s} score={score.anomaly_score:8.4f} "
              f"skipped={is_skipped}")
    
    stats = model.missing_value_stats
    print(f"\n  Missing Value Statistics:")
    print(f"    Total processed: {stats['total_processed']}")
    print(f"    Missing encountered: {stats['missing_encountered']}")
    print(f"    Imputed: {stats['imputed']}")
    print(f"    Skipped: {stats['skipped']}")
    
    all_passed = True
    
    if stats['skipped'] != 2:
        print(f"    ✗ FAILED: Expected 2 skipped, got {stats['skipped']}")
        all_passed = False
    else:
        print(f"    ✓ Correctly skipped 2 missing values")
    
    # Verify skipped observations have inf score
    skipped_scores = [s for s in scores if s.metadata.get('reason') == 'missing_value_skipped']
    if len(skipped_scores) != 2:
        print(f"    ✗ FAILED: Expected 2 skipped scores, got {len(skipped_scores)}")
        all_passed = False
    else:
        print(f"    ✓ All skipped observations have proper scores")
    
    print()
    return all_passed

def test_batch_update_with_missing() -> bool:
    """Test batch update with missing values."""
    print("=" * 60)
    print("TEST: Batch Update with Missing Values")
    print("=" * 60)
    
    model = DPGMMModel(
        alpha=1.0,
        n_components_max=5,
        missing_value_strategy='mean',
        random_seed=42
    )
    
    observations = [1.0, 2.0, np.nan, 4.0, 5.0, np.nan, 7.0, 8.0]
    
    print(f"\n  Processing