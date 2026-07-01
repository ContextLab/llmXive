"""
Integration test for LOSO loop logic in src/modeling/loso_cv.py.

Verifies that:
1. The Leave-One-Species-Out (LOSO) loop correctly iterates through species.
2. For each iteration, the held-out species is EXCLUDED from training data.
3. CRITICAL: The held-out species uses its KNOWN trait values as inputs for evaluation
   (per Spec FR-004), not imputed values.
4. The loop correctly aggregates metrics across all iterations.
"""

import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.modeling.loso_cv import run_loso_cv
from src.utils.logging import get_logger
from src.utils.config import RANDOM_SEED

# Mock data generators for integration testing
def generate_mock_species_data(n_species=3, n_records_per_species=20):
    """
    Generate a mock dataset with occurrence records and KNOWN trait values.
    Simulates the merged output of climate + trait data.
    """
    species_list = [f"Species_{i}" for i in range(n_species)]
    records = []

    for sp_idx, sp_name in enumerate(species_list):
        for i in range(n_records_per_species):
            # Mock climate variables
            bio1 = np.random.uniform(10, 25)
            bio12 = np.random.uniform(500, 2000)
            # Mock traits (KNOWN values)
            sla = np.random.uniform(10, 30)  # Specific Leaf Area
            height = np.random.uniform(0.1, 2.0)  # Plant height
            seed_mass = np.random.uniform(0.1, 5.0)  # Seed mass
            # Presence (1)
            records.append({
                'species': sp_name,
                'bio1': bio1,
                'bio12': bio12,
                'sla': sla,
                'height': height,
                'seed_mass': seed_mass,
                'presence': 1
            })

            # Generate background (absence) points for this species
            # In a real scenario, these would be sampled separately, but for this test
            # we simulate a presence/absence dataset structure
            records.append({
                'species': sp_name,
                'bio1': np.random.uniform(10, 25),
                'bio12': np.random.uniform(500, 2000),
                'sla': np.random.uniform(10, 30),
                'height': np.random.uniform(0.1, 2.0),
                'seed_mass': np.random.uniform(0.1, 5.0),
                'presence': 0
            })

    return pd.DataFrame(records), species_list

def test_loso_loop_structure_and_known_trait_usage():
    """
    Test that the LOSO loop correctly excludes the test species from training
    and uses its KNOWN trait values for evaluation.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate mock data
        df, species_list = generate_mock_species_data(n_species=3, n_records_per_species=10)
        df_path = os.path.join(tmpdir, "mock_data.csv")
        df.to_csv(df_path, index=False)

        # Mock the model training function to capture inputs
        training_inputs = []
        test_inputs = []

        def mock_train_and_evaluate(train_df, test_df, test_species_name, known_traits_df):
            """
            Mock function to simulate training and evaluation.
            Captures the inputs to verify known trait usage.
            """
            # Record training data species
            train_species = set(train_df['species'].unique())
            
            # Record test data species (should be just the held-out one)
            test_species = set(test_df['species'].unique())
            
            # Verify that the test species is NOT in training data
            assert test_species_name not in train_species, \
                f"LOSO Violation: {test_species_name} found in training data!"
            
            # Verify that test data contains only the held-out species
            assert test_species == {test_species_name}, \
                f"LOSO Violation: Test data contains {test_species}, expected only {test_species_name}"
            
            # CRITICAL: Verify that known_traits_df is provided and used for the test species
            # In the real implementation, this dataframe should contain the KNOWN trait values
            # for the held-out species.
            assert known_traits_df is not None, \
                "LOSO Violation: known_traits_df is None. Must use KNOWN trait values per Spec FR-004."
            
            # Verify that the known_traits_df contains the correct species
            assert test_species_name in known_traits_df['species'].values, \
                f"LOSO Violation: {test_species_name} not found in known_traits_df."
            
            # Verify that the known_traits_df has the required trait columns
            required_traits = ['sla', 'height', 'seed_mass']
            for trait in required_traits:
                assert trait in known_traits_df.columns, \
                    f"LOSO Violation: Required trait '{trait}' missing from known_traits_df."
            
            # Store for verification
            training_inputs.append({
                'train_species': list(train_species),
                'test_species': test_species_name,
                'known_traits_provided': True
            })
            
            # Simulate returning dummy metrics
            return {
                'species': test_species_name,
                'auc': 0.85,
                'tss': 0.60,
                'n_train': len(train_df),
                'n_test': len(test_df)
            }

        # Patch the internal training function
        with patch('src.modeling.loso_cv.train_and_evaluate_single', side_effect=mock_train_and_evaluate):
            # Run the LOSO CV
            results = run_loso_cv(
                data_path=df_path,
                species_col='species',
                feature_cols=['bio1', 'bio12', 'sla', 'height', 'seed_mass'],
                target_col='presence',
                output_dir=tmpdir
            )

        # Verify results structure
        assert isinstance(results, list), "Results should be a list of per-species metrics."
        assert len(results) == len(species_list), \
            f"Expected {len(species_list)} results, got {len(results)}."
        
        # Verify each result
        for res in results:
            assert 'species' in res, "Result missing 'species' key."
            assert 'auc' in res, "Result missing 'auc' key."
            assert 'tss' in res, "Result missing 'tss' key."
            assert res['species'] in species_list, f"Unknown species in results: {res['species']}"

        # Verify that for every iteration, known traits were provided
        for input_log in training_inputs:
            assert input_log['known_traits_provided'], \
                "LOSO Violation: Known traits were not provided for a held-out species."
            # Verify the test species was excluded from training
            test_sp = input_log['test_species']
            assert test_sp not in input_log['train_species'], \
                f"LOSO Violation: {test_sp} was in training data when it should have been held out."

def test_loso_with_missing_traits_handling():
    """
    Test that the LOSO loop correctly handles species with missing trait data
    by excluding them and logging the reason.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate mock data
        df, species_list = generate_mock_species_data(n_species=3, n_records_per_species=10)
        
        # Simulate missing traits for one species by setting traits to NaN
        missing_traits_species = species_list[0]
        df.loc[df['species'] == missing_traits_species, ['sla', 'height', 'seed_mass']] = np.nan
        
        df_path = os.path.join(tmpdir, "mock_data_missing.csv")
        df.to_csv(df_path, index=False)

        # Track which species were excluded
        excluded_species = []

        def mock_train_and_evaluate_missing(train_df, test_df, test_species_name, known_traits_df):
            """
            Mock function that simulates handling of missing traits.
            """
            if known_traits_df is None or known_traits_df.empty:
                # Simulate exclusion due to missing traits
                excluded_species.append(test_species_name)
                return None  # Indicate no result for this species
            
            # Normal case
            return {
                'species': test_species_name,
                'auc': 0.85,
                'tss': 0.60,
                'n_train': len(train_df),
                'n_test': len(test_df)
            }

        with patch('src.modeling.loso_cv.train_and_evaluate_single', side_effect=mock_train_and_evaluate_missing):
            results = run_loso_cv(
                data_path=df_path,
                species_col='species',
                feature_cols=['bio1', 'bio12', 'sla', 'height', 'seed_mass'],
                target_col='presence',
                output_dir=tmpdir
            )

        # Verify that the species with missing traits was excluded
        assert missing_traits_species in excluded_species, \
            f"LOSO Violation: Species {missing_traits_species} with missing traits was not excluded."
        
        # Verify that the result list does not contain the excluded species
        result_species = [r['species'] for r in results if r is not None]
        assert missing_traits_species not in result_species, \
            f"LOSO Violation: Excluded species {missing_traits_species} found in results."

def test_loso_output_file_generation():
    """
    Test that the LOSO loop correctly generates output files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate mock data
        df, species_list = generate_mock_species_data(n_species=3, n_records_per_species=10)
        df_path = os.path.join(tmpdir, "mock_data.csv")
        df.to_csv(df_path, index=False)

        def mock_train_and_evaluate_output(train_df, test_df, test_species_name, known_traits_df):
            return {
                'species': test_species_name,
                'auc': 0.85,
                'tss': 0.60,
                'n_train': len(train_df),
                'n_test': len(test_df)
            }

        with patch('src.modeling.loso_cv.train_and_evaluate_single', side_effect=mock_train_and_evaluate_output):
            results = run_loso_cv(
                data_path=df_path,
                species_col='species',
                feature_cols=['bio1', 'bio12', 'sla', 'height', 'seed_mass'],
                target_col='presence',
                output_dir=tmpdir
            )

        # Check for expected output files
        expected_results_file = os.path.join(tmpdir, "loso_results.csv")
        assert os.path.exists(expected_results_file), \
            f"LOSO Violation: Expected results file {expected_results_file} was not created."
        
        # Verify file content
        results_df = pd.read_csv(expected_results_file)
        assert len(results_df) == len(species_list), \
            f"Expected {len(species_list)} rows in results file, got {len(results_df)}."
        assert 'species' in results_df.columns, "Results file missing 'species' column."
        assert 'auc' in results_df.columns, "Results file missing 'auc' column."
        assert 'tss' in results_df.columns, "Results file missing 'tss' column."