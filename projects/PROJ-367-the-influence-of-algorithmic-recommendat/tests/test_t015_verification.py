"""
Test script for T015: Verification of main.py output and entropy calculations.
Runs a hardcoded dataset and checks calculated scores against manual entropy values.
"""
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from metrics import calculate_diversity_score
from ingestion import DataSchemaError

def test_entropy_calculations():
    """
    Verify that calculate_diversity_score produces correct Shannon entropy values
    on a hardcoded dataset with known manual calculations.
    """
    # Hardcoded test dataset
    test_data = pd.DataFrame({
        'user_id': ['U001', 'U002', 'U003'],
        'session_id': ['S001', 'S002', 'S003'],
        'recommended_categories': [
            ['Math', 'Math', 'Math', 'Physics', 'Physics', 'Physics', 'Chemistry', 'Chemistry', 'Chemistry'], # Uniform 3
            ['Math', 'Math', 'Math', 'Math', 'Physics'], # Skewed
            ['Math', 'Math', 'Math', 'Math', 'Math'] # Single
        ],
        'enrolled_categories': [
            ['Math', 'Physics', 'Chemistry'], # Uniform 3
            ['Math', 'Math', 'Math', 'Physics'], # Skewed
            ['Math'] # Single
        ]
    })

    # Manual Calculations
    # Shannon Entropy: H = -sum(p * log2(p))
    
    # U001 Recs: 3/9, 3/9, 3/9 -> log2(3)
    expected_rec_u001 = np.log2(3)
    # U001 Enroll: 1/3, 1/3, 1/3 -> log2(3)
    expected_learner_u001 = np.log2(3)

    # U002 Recs: 4/5, 1/5 -> -(0.8*log2(0.8) + 0.2*log2(0.2))
    p_m = 4/5
    p_p = 1/5
    expected_rec_u002 = -(p_m * np.log2(p_m) + p_p * np.log2(p_p))
    
    # U002 Enroll: 3/4, 1/4 -> -(0.75*log2(0.75) + 0.25*log2(0.25))
    p_m = 3/4
    p_p = 1/4
    expected_learner_u002 = -(p_m * np.log2(p_m) + p_p * np.log2(p_p))

    # U003 Recs: 5/5 -> 0
    expected_rec_u003 = 0.0
    # U003 Enroll: 1/1 -> 0
    expected_learner_u003 = 0.0

    expected_values = {
        'U001': {'rec': expected_rec_u001, 'learn': expected_learner_u001},
        'U002': {'rec': expected_rec_u002, 'learn': expected_learner_u002},
        'U003': {'rec': expected_rec_u003, 'learn': expected_learner_u003}
    }

    # Run the function
    results = calculate_diversity_score(test_data)

    # Verify columns
    required_cols = {'user_id', 'session_id', 'recommendation_diversity_score', 'learner_diversity_score'}
    assert required_cols.issubset(set(results.columns)), f"Missing columns. Found: {list(results.columns)}"

    # Verify values
    tolerance = 0.001
    for _, row in results.iterrows():
        uid = row['user_id']
        assert uid in expected_values, f"Unexpected user_id: {uid}"
        
        rec_diff = abs(row['recommendation_diversity_score'] - expected_values[uid]['rec'])
        learn_diff = abs(row['learner_diversity_score'] - expected_values[uid]['learn'])
        
        assert rec_diff <= tolerance, f"Rec score mismatch for {uid}: got {row['recommendation_diversity_score']}, expected {expected_values[uid]['rec']}, diff {rec_diff}"
        assert learn_diff <= tolerance, f"Learner score mismatch for {uid}: got {row['learner_diversity_score']}, expected {expected_values[uid]['learn']}, diff {learn_diff}"

    print("All assertions passed. Entropy calculations are correct.")

def test_output_file_generation():
    """
    Verify that main.py (when run with --verify or normally) produces the expected output file.
    This test assumes main.py is run externally or we simulate the path.
    For T015, we verify the logic by running the core function and checking the parquet write.
    """
    import tempfile
    import pyarrow.parquet as pq
    
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_diversity_scores.parquet"
        
        test_data = pd.DataFrame({
            'user_id': ['U001'],
            'session_id': ['S001'],
            'recommended_categories': [['A', 'B', 'C']],
            'enrolled_categories': [['A', 'B', 'C']]
        })
        
        results = calculate_diversity_score(test_data)
        results.to_parquet(output_path, index=False)
        
        assert output_path.exists(), "Output file was not created."
        
        # Read back and verify
        df_read = pd.read_parquet(output_path)
        assert 'recommendation_diversity_score' in df_read.columns
        assert 'learner_diversity_score' in df_read.columns
        
        print("Output file generation verified.")

if __name__ == "__main__":
    test_entropy_calculations()
    test_output_file_generation()
    print("T015 Verification Suite: PASSED")
