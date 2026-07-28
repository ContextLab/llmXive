"""
Tests for T017: Functional Role Derivation
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.derive_roles import (
    load_marginal_frequencies,
    load_positional_ranks,
    calculate_functional_role,
    verify_exclusion_of_co_occurrence,
    save_output
)

def test_load_marginal_frequencies():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy data
        df = pd.DataFrame({
            'ingredient_id': ['A', 'B', 'C'],
            'count': [100, 200, 300]
        })
        path = os.path.join(tmpdir, 'test_counts.parquet')
        df.to_parquet(path)
        
        result = load_marginal_frequencies(path)
        
        assert 'ingredient_id' in result.columns
        assert 'marginal_frequency' in result.columns
        assert len(result) == 3
        assert result.loc[result['ingredient_id'] == 'B', 'marginal_frequency'].values[0] == 200

def test_load_positional_ranks_derived():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy data
        df = pd.DataFrame({
            'ingredient_id': ['A', 'B', 'C'],
            'count': [100, 200, 300]
        })
        path = os.path.join(tmpdir, 'test_counts.parquet')
        df.to_parquet(path)
        
        # Should derive ranks if specific file missing
        result = load_positional_ranks(path)
        
        assert 'positional_rank' in result.columns
        assert len(result) == 3
        # Rank should be inversely related to count (highest count = rank 1)
        # A=100, B=200, C=300 -> Ranks: C=1, B=2, A=3
        ranks = {row['ingredient_id']: row['positional_rank'] for _, row in result.iterrows()}
        assert ranks['C'] == 1
        assert ranks['B'] == 2
        assert ranks['A'] == 3

def test_calculate_functional_role():
    marginal_df = pd.DataFrame({
        'ingredient_id': ['A', 'B'],
        'marginal_frequency': [100, 200]
    })
    positional_df = pd.DataFrame({
        'ingredient_id': ['A', 'B'],
        'positional_rank': [2, 1] # B is higher position (rank 1)
    })
    
    result = calculate_functional_role(marginal_df, positional_df)
    
    assert 'functional_role_score' in result.columns
    assert len(result) == 2
    
    # Check normalization logic
    # B has higher freq and better rank, so should have higher score
    score_b = result[result['ingredient_id'] == 'B']['functional_role_score'].values[0]
    score_a = result[result['ingredient_id'] == 'A']['functional_role_score'].values[0]
    assert score_b > score_a

def test_verify_exclusion():
    role_df = pd.DataFrame({
        'ingredient_id': ['A', 'B', 'C', 'D', 'E'],
        'functional_role_score': [0.1, 0.2, 0.3, 0.4, 0.5]
    })
    
    co_occurrence_df = pd.DataFrame({
        'ingredient_id_1': ['A', 'B', 'C', 'D', 'E'],
        'ingredient_id_2': ['B', 'C', 'D', 'E', 'A'],
        'count': [10, 20, 30, 40, 50]
    })
    
    corr = verify_exclusion_of_co_occurrence(role_df, co_occurrence_df)
    
    # Just check it returns a float between -1 and 1
    assert isinstance(corr, float)
    assert -1.0 <= corr <= 1.0

def test_save_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        df = pd.DataFrame({
            'ingredient_id': ['A'],
            'functional_role_score': [0.5]
        })
        output_path = os.path.join(tmpdir, 'test_output.parquet')
        
        save_output(df, output_path, 0.05)
        
        assert os.path.exists(output_path)
        assert os.path.exists(output_path.replace('.parquet', '_verification.json'))
        
        with open(output_path.replace('.parquet', '_verification.json')) as f:
            log = json.load(f)
            assert log['constraint_met'] == True
            assert log['correlation_with_co_occurrence'] == 0.05

if __name__ == "__main__":
    test_load_marginal_frequencies()
    test_load_positional_ranks_derived()
    test_calculate_functional_role()
    test_verify_exclusion()
    test_save_output()
    print("All tests passed.")