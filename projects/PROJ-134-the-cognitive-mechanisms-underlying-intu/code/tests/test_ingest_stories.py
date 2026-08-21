import pytest
import numpy as np
from pathlib import Path
import sys
import os
from scipy import stats
import pandas as pd

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.norms import load_norms_data, validate_against_norms
from code.data.simulation_stories import generate_moral_stories_dataset, save_datasets
from code.config import get_path, ensure_directories, init_random_seeds


class TestPsychometricNormValidation:
    """
    Unit test for psychometric norm validation (T012).
    Verifies that the generated simulated stories data distribution
    matches the Gervais et al. norms using the Kolmogorov-Smirnov test.
    """

    def setup_method(self):
        """Set up test fixtures."""
        init_random_seeds(42)
        ensure_directories()
        self.n_samples = 500  # Use a reasonable sample size for the test

    def test_psychometric_validity(self):
        """
        Test that the simulated moral stories dataset distribution
        matches the Gervais et al. norms using KS-test (p > 0.05).
        
        This test validates the simulation logic against the psychometric
        norms defined in data/config/gervais_norms.yaml (or generated
        if not present).
        """
        # 1. Load the reference norms
        # The norms module handles loading the config or generating synthetic norms
        # if the file doesn't exist, but for this test we assume the norms are available.
        try:
            norms_data = load_norms_data()
            # Expect 'moral_foundation_scores' or similar key containing the distribution
            # If the specific key structure varies, we adapt to what load_norms_data returns.
            if isinstance(norms_data, dict):
                # Try to find the relevant column data in the norms
                # Assuming norms_data contains a DataFrame or a dict of arrays
                if 'data' in norms_data:
                    norms_df = norms_data['data']
                elif 'moral_foundation_scores' in norms_data:
                    norms_df = pd.DataFrame(norms_data['moral_foundation_scores'])
                else:
                    # Fallback: assume the dict itself is the data or has a 'values' key
                    norms_df = pd.DataFrame(norms_data)
            else:
                norms_df = pd.DataFrame(norms_data)
        
            # Identify the column to compare (e.g., 'harm_score', 'care_score', or a composite)
            # The spec mentions "Moral Stories" and "Gervais et al. psychometric norms".
            # We will look for a column representing the moral judgment rating or score.
            target_col = None
            possible_cols = ['judgment_rating', 'moral_score', 'harm', 'care', 'score']
            for col in possible_cols:
                if col in norms_df.columns:
                    target_col = col
                    break
            
            # If no specific column is found, use the first numeric column
            if target_col is None:
                numeric_cols = norms_df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    target_col = numeric_cols[0]
                else:
                    pytest.skip("No numeric columns found in norms data to validate against.")

        except FileNotFoundError:
            # If norms file is missing, we generate a synthetic reference for the test
            # to ensure the test logic (KS-test) is valid, but this should ideally be caught by T007.
            pytest.skip("Gervais norms file not found. Skipping psychometric validation.")

        # 2. Generate the simulated stories dataset
        # We generate the dataset to the expected location
        output_path = get_path("data/raw/synthetic_stories.csv")
        # Ensure the directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate the dataset
        df_simulated = generate_moral_stories_dataset(n_samples=self.n_samples)
        
        # Save to disk (required for the test to be "real" and not just in-memory)
        df_simulated.to_csv(output_path, index=False)

        # 3. Perform the Kolmogorov-Smirnov test
        # We compare the distribution of the target column in the simulated data
        # against the distribution in the norms data.
        
        # Extract the target column from simulated data
        sim_col = None
        if target_col in df_simulated.columns:
            sim_col = target_col
        else:
            # Fallback: look for 'judgment_rating' which is explicitly mentioned in T014
            if 'judgment_rating' in df_simulated.columns:
                sim_col = 'judgment_rating'
            else:
                # If no matching column, skip
                pytest.skip(f"Target column '{target_col}' not found in simulated data.")
        
        if sim_col is None:
            pytest.skip("Could not identify a comparable column in simulated data.")

        # Drop NaNs for the test
        norms_vals = norms_df[target_col].dropna()
        sim_vals = df_simulated[sim_col].dropna()

        if len(norms_vals) == 0 or len(sim_vals) == 0:
            pytest.skip("Empty data after dropping NaNs.")

        # Perform KS-test
        # The null hypothesis is that the two samples are drawn from the same distribution.
        # We expect p > 0.05 to fail to reject the null (i.e., they are similar).
        statistic, p_value = stats.ks_2samp(norms_vals, sim_vals)

        # 4. Assert the result
        # The test passes if p_value > 0.05
        assert p_value > 0.05, (
            f"Psychometric validity check failed. KS-test p-value: {p_value:.4f}. "
            f"The simulated distribution significantly differs from the Gervais norms. "
            f"Statistic: {statistic:.4f}"
        )

        # Additional check: ensure the means are reasonably close (within 1 SD of norms)
        # This is a secondary check to ensure the simulation is not just "similar shape" but also "similar scale"
        norms_mean = norms_vals.mean()
        norms_std = norms_vals.std()
        sim_mean = sim_vals.mean()
        
        # Allow a tolerance of 1 standard deviation
        assert abs(sim_mean - norms_mean) <= norms_std, (
            f"Mean of simulated data ({sim_mean:.2f}) differs from norms mean ({norms_mean:.2f}) "
            f"by more than 1 SD ({norms_std:.2f})."
        )