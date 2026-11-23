"""
Integration tests for GAMM modeling convergence.

This module tests the convergence of GAMM models on synthetic data
to ensure the modeling pipeline functions correctly before running
on real data.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.gamm_fit import fit_species_year_gamm
from src.config import SEED

# Set random seed for reproducibility
np.random.seed(SEED)


def generate_synthetic_gamm_data(
    n_species: int = 3,
    n_years: int = 3,
    n_observations_per_species_year: int = 50,
    include_convergence_issues: bool = False
) -> pd.DataFrame:
    """
    Generate synthetic data for GAMM convergence testing.
    
    Args:
        n_species: Number of distinct species in the dataset
        n_years: Number of years in the dataset
        n_observations_per_species_year: Number of observations per species-year
        include_convergence_issues: If True, generate some problematic data points
        
    Returns:
        DataFrame with columns: species, year, temp, precip, extreme_weather_index, 
        phenology_metric, lat, lon
    """
    species_list = [f"Species_{i}" for i in range(n_species)]
    years = list(range(2020, 2020 + n_years))
    
    data = []
    
    for species in species_list:
        for year in years:
            for _ in range(n_observations_per_species_year):
                # Generate realistic covariates
                temp = np.random.normal(15.0, 5.0)  # Temperature in Celsius
                precip = np.random.exponential(10.0)  # Precipitation in mm
                extreme_weather_index = np.random.beta(2, 5) * 10  # Index 0-10
                
                # Generate response variable with some true relationship
                # phenology_metric = f(temp, precip) + noise
                base_phenology = 100.0
                temp_effect = -2.0 * temp
                precip_effect = 0.5 * precip
                extreme_effect = -1.0 * extreme_weather_index
                
                phenology_metric = base_phenology + temp_effect + precip_effect + extreme_effect
                
                # Add some noise
                phenology_metric += np.random.normal(0, 5.0)
                
                # Occasionally create problematic data points if requested
                if include_convergence_issues and np.random.random() < 0.05:
                    # Create extreme outliers
                    phenology_metric += np.random.choice([-100, 100])
                
                # Generate spatial coordinates (random points in a region)
                lat = np.random.uniform(30.0, 50.0)
                lon = np.random.uniform(-120.0, -70.0)
                
                data.append({
                    'species': species,
                    'year': year,
                    'temp': temp,
                    'precip': precip,
                    'extreme_weather_index': extreme_weather_index,
                    'phenology_metric': phenology_metric,
                    'lat': lat,
                    'lon': lon
                })
    
    return pd.DataFrame(data)


@pytest.fixture
def synthetic_gamm_data():
    """Generate synthetic GAMM data for testing."""
    return generate_synthetic_gamm_data(
        n_species=2,
        n_years=2,
        n_observations_per_species_year=30,
        include_convergence_issues=False
    )


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_gamm_convergence(synthetic_gamm_data, temp_data_dir):
    """
    Test that GAMM models converge on synthetic data.
    
    This test verifies:
    1. The model fitting process completes without convergence errors
    2. The output contains expected columns (coefficients, p-values, fit statistics)
    3. Results are reasonable (finite values, expected ranges)
    """
    # Ensure output directory exists
    output_dir = temp_data_dir / "model_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "test_convergence_results.parquet"
    
    # Run the GAMM fitting pipeline
    # We use a subset of data for faster testing
    test_data = synthetic_gamm_data.head(100)
    
    try:
        results = fit_species_year_gamm(
            data=test_data,
            output_path=str(output_file),
            max_iter=100,
            convergence_threshold=1e-6
        )
        
        # Verify results exist and are not empty
        assert results is not None, "GAMM fitting returned None"
        assert len(results) > 0, "GAMM fitting returned empty results"
        
        # Check that results have expected columns
        expected_columns = [
            'species', 'year', 'coefficients', 'p_values', 
            'convergence_status', 'deviance_explained', 'edf'
        ]
        
        for col in expected_columns:
            assert col in results.columns, f"Missing expected column: {col}"
        
        # Verify convergence status
        # Most models should converge successfully
        convergence_counts = results['convergence_status'].value_counts()
        successful_convergence = convergence_counts.get('converged', 0)
        
        # At least 50% of models should converge (allowing for some edge cases)
        assert successful_convergence >= len(results) * 0.5, \
            f"Too many convergence failures: {successful_convergence}/{len(results)}"
        
        # Verify coefficient values are finite and reasonable
        # Extract coefficients as a list of dicts and check values
        for _, row in results.iterrows():
            coeffs = row['coefficients']
            if isinstance(coeffs, dict):
                for key, value in coeffs.items():
                    assert np.isfinite(value), f"Non-finite coefficient value: {key}={value}"
            
            # Check p-values are valid probabilities
            p_values = row['p_values']
            if isinstance(p_values, dict):
                for key, value in p_values.items():
                    assert 0 <= value <= 1, f"Invalid p-value: {key}={value}"
                    assert np.isfinite(value), f"Non-finite p-value: {key}={value}"
        
        # Verify deviance explained is in valid range
        for _, row in results.iterrows():
            deviance = row['deviance_explained']
            assert 0 <= deviance <= 100, f"Invalid deviance explained: {deviance}"
            assert np.isfinite(deviance), f"Non-finite deviance: {deviance}"
        
        # Verify EDF (effective degrees of freedom) are reasonable
        for _, row in results.iterrows():
            edf = row['edf']
            assert edf > 0, f"Invalid EDF: {edf}"
            assert np.isfinite(edf), f"Non-finite EDF: {edf}"
        
        # Verify output file was created
        assert output_file.exists(), f"Output file not created: {output_file}"
        
        # Verify file is not empty
        assert output_file.stat().st_size > 0, f"Output file is empty: {output_file}"
        
        # Log success
        print(f"GAMM convergence test passed. Successfully fitted {len(results)} models.")
        print(f"Convergence rate: {successful_convergence}/{len(results)} ({100*successful_convergence/len(results):.1f}%)")
        
    except Exception as e:
        pytest.fail(f"GAMM convergence test failed with exception: {str(e)}")


def test_gamm_convergence_with_problematic_data(temp_data_dir):
    """
    Test GAMM convergence with intentionally problematic data.
    
    This test verifies that the model handles edge cases gracefully
    and reports convergence issues appropriately.
    """
    # Generate data with some problematic points
    problematic_data = generate_synthetic_gamm_data(
        n_species=1,
        n_years=1,
        n_observations_per_species_year=20,
        include_convergence_issues=True
    )
    
    output_dir = temp_data_dir / "problematic_model_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "problematic_results.parquet"
    
    try:
        results = fit_species_year_gamm(
            data=problematic_data,
            output_path=str(output_file),
            max_iter=100,
            convergence_threshold=1e-6
        )
        
        # Even with problematic data, we should get some results
        assert results is not None, "GAMM fitting returned None for problematic data"
        
        # Check that convergence status is recorded for all models
        assert 'convergence_status' in results.columns, "Missing convergence_status column"
        
        # Verify that at least some models converged (even with problematic data)
        # or that convergence failures are properly recorded
        convergence_counts = results['convergence_status'].value_counts()
        
        # Either we have successful convergence or properly recorded failures
        has_converged = 'converged' in convergence_counts
        has_failed = 'failed' in convergence_counts or 'warning' in convergence_counts
        
        assert has_converged or has_failed, \
            "No convergence status recorded for any model"
        
        print(f"Problematic data test passed. Convergence distribution: {dict(convergence_counts)}")
        
    except Exception as e:
        # If the model crashes completely, that's a failure
        pytest.fail(f"GAMM failed catastrophically on problematic data: {str(e)}")