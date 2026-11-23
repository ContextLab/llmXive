"""
Simulate blind pre-test for visual indistinguishability of AI vs Human images.

This script generates N=30 mock participant ratings based on the literature-based
distribution (Normal(0, 1)) as specified in Plan Phase 0. It performs a two-sample
t-test to verify visual indistinguishability (p > 0.05) and writes the results
to data/pretest/results.json.

The simulation uses a fixed random seed (42) for reproducibility.
"""
import os
import json
import numpy as np
from scipy import stats

# Constants from Plan Phase 0
RANDOM_SEED = 42
N_PARTICIPANTS = 30
MOCK_RATING_MEAN = 0.0
MOCK_RATING_STD = 1.0
OUTPUT_PATH = "data/pretest/results.json"

def run_pretest_simulation():
    """
    Simulate blind pre-test with N=30 participants rating AI vs Human images.
    
    Returns:
        dict: Results containing p-value, t-statistic, and conclusion.
    """
    # Set random seed for reproducibility
    np.random.seed(RANDOM_SEED)
    
    # Generate mock ratings for AI images (N=30)
    ai_ratings = np.random.normal(
        loc=MOCK_RATING_MEAN,
        scale=MOCK_RATING_STD,
        size=N_PARTICIPANTS
    )
    
    # Generate mock ratings for Human images (N=30)
    human_ratings = np.random.normal(
        loc=MOCK_RATING_MEAN,
        scale=MOCK_RATING_STD,
        size=N_PARTICIPANTS
    )
    
    # Perform two-sample t-test for visual indistinguishability
    t_stat, p_value = stats.ttest_ind(ai_ratings, human_ratings)
    
    # Determine conclusion
    is_indistinguishable = p_value > 0.05
    
    results = {
        "n_participants": N_PARTICIPANTS,
        "ai_mean_rating": float(np.mean(ai_ratings)),
        "ai_std_rating": float(np.std(ai_ratings)),
        "human_mean_rating": float(np.mean(human_ratings)),
        "human_std_rating": float(np.std(human_ratings)),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "is_indistinguishable": is_indistinguishable,
        "conclusion": "PASS" if is_indistinguishable else "FAIL",
        "seed": RANDOM_SEED
    }
    
    return results

def main():
    """
    Main entry point for pre-test simulation.
    
    Ensures output directory exists and writes results to data/pretest/results.json.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_PATH)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Run simulation
    results = run_pretest_simulation()
    
    # Write results to JSON
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Pre-test simulation completed. Results written to {OUTPUT_PATH}")
    print(f"P-value: {results['p_value']:.4f}")
    print(f"Conclusion: {results['conclusion']}")
    
    return results

if __name__ == "__main__":
    main()
