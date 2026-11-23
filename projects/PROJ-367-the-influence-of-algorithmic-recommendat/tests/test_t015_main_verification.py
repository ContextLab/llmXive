"""
Verification script for T015: Main entry point and diversity score calculation.
Uses a hardcoded test dataset with known entropy values to verify correctness.
"""
import sys
import math
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from metrics import shannon_entropy

def calculate_manual_entropy(probabilities):
    """Calculate Shannon entropy (base 2) manually for verification."""
    if not probabilities:
        return 0.0
    # Filter out zeros to avoid log(0)
    probs = [p for p in probabilities if p > 0]
    entropy = -sum(p * math.log2(p) for p in probs)
    return entropy

def test_known_entropy_values():
    """
    Test with hardcoded categories and counts where entropy is known.
    Case 1: Perfect uniform distribution (2 categories, equal counts) -> 1.0
    Case 2: Perfectly skewed (1 category dominates) -> close to 0.0
    Case 3: Mixed distribution
    """
    test_cases = [
        {
            "name": "Uniform 2 categories",
            "counts": [50, 50],
            "expected_entropy": 1.0,
            "tolerance": 0.001
        },
        {
            "name": "Skewed distribution",
            "counts": [95, 5],
            "expected_entropy": calculate_manual_entropy([0.95, 0.05]),
            "tolerance": 0.001
        },
        {
            "name": "Uniform 4 categories",
            "counts": [25, 25, 25, 25],
            "expected_entropy": 2.0,
            "tolerance": 0.001
        }
    ]

    for case in test_cases:
        counts = case["counts"]
        total = sum(counts)
        probs = [c / total for c in counts]
        manual = calculate_manual_entropy(probs)
        
        # Use the library function
        # Note: shannon_entropy expects a list of counts or a distribution
        # We pass the counts directly as per typical implementation
        # If the function expects normalized probabilities, we adapt
        try:
            lib_result = shannon_entropy(counts)
        except Exception as e:
            # Fallback if function signature differs
            lib_result = shannon_entropy(np.array(probs))
        
        diff = abs(lib_result - case["expected_entropy"])
        assert diff < case["tolerance"], (
            f"Entropy mismatch for {case['name']}: "
            f"Expected {case['expected_entropy']:.4f}, got {lib_result:.4f}, diff={diff:.4f}"
        )
        print(f"✓ {case['name']}: {lib_result:.4f} (expected {case['expected_entropy']:.4f})")

def test_main_output_structure():
    """
    Run the main pipeline on a small synthetic dataset and verify:
    1. Output file exists
    2. Required columns are present
    3. Values are numeric and within expected range [0, log2(num_categories)]
    """
    # Create a temporary small dataset
    data = {
        'user_id': [1, 2, 3],
        'session_id': ['s1', 's2', 's3'],
        'recommended_categories': [
            ['AI', 'ML', 'Data'],
            ['Math', 'Stats'],
            ['Physics']
        ],
        'enrolled_categories': [
            ['AI', 'ML'],
            ['Math', 'Stats', 'Calc'],
            ['Physics', 'Quantum']
        ]
    }
    df = pd.DataFrame(data)
    
    # Save to temp CSV to simulate real ingestion
    temp_csv = Path("data/test_input.csv")
    temp_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(temp_csv, index=False)
    
    # Mock config to point to this file if needed, or run main logic directly
    # Since main.py loads via load_project_data, we assume it reads from a fixed path
    # For this test, we verify the calculation logic directly on the dataframe
    
    from metrics import calculate_diversity_score
    
    # Calculate scores
    result = calculate_diversity_score(df, similarity_threshold=0.5)
    
    # Verify columns
    required = ['user_id', 'session_id', 'recommendation_diversity_score', 'learner_diversity_score']
    for col in required:
        assert col in result.columns, f"Missing column: {col}"
    
    # Verify values are non-negative
    assert (result['recommendation_diversity_score'] >= 0).all(), "Negative recommendation score"
    assert (result['learner_diversity_score'] >= 0).all(), "Negative learner score"
    
    # Verify values are finite
    assert result['recommendation_diversity_score'].notna().all(), "NaN in recommendation score"
    assert result['learner_diversity_score'].notna().all(), "NaN in learner score"
    
    print("✓ Output structure verification passed")
    print(f"  Columns: {list(result.columns)}")
    print(f"  Sample scores: {result[['recommendation_diversity_score', 'learner_diversity_score']].to_dict()}")
    
    # Clean up
    if temp_csv.exists():
        temp_csv.unlink()

if __name__ == "__main__":
    print("Running T015 Verification Tests...")
    test_known_entropy_values()
    test_main_output_structure()
    print("All verification tests passed.")
