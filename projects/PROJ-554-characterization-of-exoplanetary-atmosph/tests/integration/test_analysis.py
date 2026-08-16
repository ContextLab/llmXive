"""
Integration test for correlation and regression analysis on mock data.

This test validates the full analysis pipeline (T025b, T025c, T027, T030)
by running it on a generated mock dataset that mimics the structure of
real exoplanet data (including censored values).

The test verifies:
1. Data loading handles mixed resolved/censored data correctly.
2. Kendall's tau calculation returns a valid statistic.
3. Bootstrap confidence intervals are computed and non-trivial.
4. Tobit regression converges and produces coefficients.
5. Final statistics are generated and written to disk.

NOTE: This test uses a deterministic mock dataset to ensure reproducibility
without requiring external API calls or large real datasets. The mock data
is generated to satisfy the schema requirements of the analysis module.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import (
    load_analysis_data,
    compute_censored_kendall_tau,
    run_tobit_regression,
    generate_final_statistics
)
from config import get_config, set_random_seed
from data_models import PlanetCategory, CensorshipStatus


class MockDataGenerator:
    """
    Generates a deterministic mock dataset for integration testing.
    
    The data mimics the output of T012 (metadata) and T020 (retrieval results)
    combined, with realistic distributions and intentional censored values
    to test the survival analysis logic.
    """
    
    def __init__(self, seed: int = 42, n_samples: int = 50):
        self.seed = seed
        self.n_samples = n_samples
        np.random.seed(seed)
        
    def generate(self) -> pd.DataFrame:
        """Generate a mock dataset with required columns."""
        # Base parameters
        temperatures = np.random.uniform(800, 2500, self.n_samples)
        masses = np.random.uniform(0.3, 3.0, self.n_samples)  # Jupiter masses
        metallicities = np.random.uniform(-0.5, 0.5, self.n_samples)
        snr = np.random.uniform(5, 50, self.n_samples)
        resolution = np.random.uniform(50, 300, self.n_samples)
        
        # Generate water mixing ratio with correlation to temperature
        # y = beta0 + beta1 * T + noise
        beta0 = -5.0
        beta1 = 0.002
        true_water = beta0 + beta1 * temperatures + np.random.normal(0, 0.5, self.n_samples)
        true_water = np.clip(true_water, -10, -2)  # Log scale, reasonable range
        
        # Introduce censoring: low SNR -> upper limits
        # If SNR < 15, mark as censored and set observed value to detection limit
        is_censored = snr < 15
        detection_limit = -8.0  # Arbitrary detection limit in log10 mixing ratio
        
        observed_water = np.where(
            is_censored,
            detection_limit + np.random.normal(0, 0.1, self.n_samples), # Slight noise around limit
            true_water
        )
        
        # Ensure censored values are below the true limit (conservative)
        observed_water = np.where(
            is_censored & (observed_water > detection_limit),
            detection_limit - 0.1,
            observed_water
        )
        
        # Planet categories
        categories = []
        for T, R in zip(temperatures, masses):
            if R > 0.8 and T > 1000:
                categories.append(PlanetCategory.HOT_JUPITER)
            elif R < 1.6 and T < 1000:
                categories.append(PlanetCategory.TEMPERATE_SUPER_EARTH)
            else:
                categories.append(PlanetCategory.OTHER)
        
        # Censorship status
        censorship_status = [
            CensorshipStatus.UPPER_LIMIT if c else CensorshipStatus.RESOLVED
            for c in is_censored
        ]
        
        df = pd.DataFrame({
            'planet_name': [f"Planet_{i}" for i in range(self.n_samples)],
            'temperature': temperatures,
            'mass': masses,
            'metallicity': metallicities,
            'snr': snr,
            'resolution': resolution,
            'water_mixing_ratio': observed_water,
            'is_upper_limit': is_censored,
            'detection_limit': np.where(is_censored, detection_limit, np.nan),
            'planet_category': [c.value for c in categories],
            'censorship_status': [c.value for c in censorship_status],
            'instrument': np.random.choice(['HST', 'JWST', 'Spitzer'], self.n_samples),
            'wavelength_range': np.random.choice(['1.0-5.0', '0.6-2.8'], self.n_samples)
        })
        
        return df


@pytest.fixture
def mock_dataset_path(tmp_path: Path) -> Path:
    """Generate and save a mock dataset to a temporary file."""
    generator = MockDataGenerator(seed=42, n_samples=50)
    df = generator.generate()
    
    output_path = tmp_path / "mock_analysis_data.csv"
    df.to_csv(output_path, index=False)
    return output_path


@pytest.fixture
def config_with_temp_dirs(tmp_path: Path) -> Dict[str, Any]:
    """Create a temporary directory structure for test outputs."""
    data_dir = tmp_path / "data" / "processed"
    results_dir = tmp_path / "results"
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Patch config to use temp dirs
    original_get_config = get_config
    
    def mock_get_config():
        cfg = original_get_config()
        cfg['paths']['data_processed'] = str(data_dir)
        cfg['paths']['results'] = str(results_dir)
        return cfg
    
    # Temporarily replace
    import analysis
    analysis.get_config = mock_get_config
    
    yield {
        'data_processed': str(data_dir),
        'results': str(results_dir)
    }
    
    # Restore
    analysis.get_config = original_get_config


def test_load_analysis_data(mock_dataset_path: Path):
    """Test that load_analysis_data correctly reads and parses the mock CSV."""
    df = load_analysis_data(str(mock_dataset_path))
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    required_cols = [
        'temperature', 'water_mixing_ratio', 'is_upper_limit',
        'metallicity', 'mass', 'censorship_status'
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Verify data types
    assert df['is_upper_limit'].dtype == bool
    assert 'censored' in df['censorship_status'].str.lower().values


def test_compute_censored_kendall_tau(mock_dataset_path: Path):
    """Test Kendall's tau calculation on censored data."""
    df = load_analysis_data(str(mock_dataset_path))
    
    # Test Hot Jupiters vs Super-Earths correlation
    tau, p_value, ci_lower, ci_upper = compute_censored_kendall_tau(
        df, 
        x_col='temperature', 
        y_col='water_mixing_ratio',
        censored_col='is_upper_limit',
        n_bootstrap=100  # Reduced for speed in test
    )
    
    assert isinstance(tau, float)
    assert isinstance(p_value, float)
    assert -1 <= tau <= 1
    assert 0 <= p_value <= 1
    assert ci_lower is not None
    assert ci_upper is not None
    assert ci_lower <= tau <= ci_upper


def test_run_tobit_regression(mock_dataset_path: Path):
    """Test Tobit regression convergence and output structure."""
    df = load_analysis_data(str(mock_dataset_path))
    
    results = run_tobit_regression(
        df,
        dependent='water_mixing_ratio',
        independent=['temperature', 'mass', 'metallicity'],
        censored_col='is_upper_limit'
    )
    
    assert 'coefficients' in results
    assert 'p_values' in results
    assert 'log_likelihood' in results
    assert 'converged' in results
    
    assert results['converged'] is True, "Tobit regression did not converge"
    assert len(results['coefficients']) == 3  # temperature, mass, metallicity
    assert len(results['p_values']) == 3


def test_generate_final_statistics(mock_dataset_path: Path, config_with_temp_dirs: Dict[str, Any]):
    """Test end-to-end generation of final statistics and output files."""
    df = load_analysis_data(str(mock_dataset_path))
    
    # Run the full pipeline
    final_stats = generate_final_statistics(
        df,
        bootstrap_iterations=100,
        output_dir=config_with_temp_dirs['results']
    )
    
    # Verify output files were created
    results_dir = Path(config_with_temp_dirs['results'])
    assert (results_dir / "bootstrap_ci.json").exists()
    assert (results_dir / "regression_results.json").exists()
    assert (results_dir / "analysis_results.json").exists()
    
    # Verify content of analysis_results.json
    with open(results_dir / "analysis_results.json", 'r') as f:
        analysis_results = json.load(f)
    
    assert 'kendall_tau' in analysis_results
    assert 'p_value' in analysis_results
    assert 'ci_width' in analysis_results
    assert 'model_fit' in analysis_results
    assert 'min_detectable_concentration' in analysis_results
    
    # Verify statistical sanity
    assert -1 <= analysis_results['kendall_tau'] <= 1
    assert analysis_results['ci_width'] > 0


def test_mock_data_represents_censored_structure(mock_dataset_path: Path):
    """Verify the mock data generator actually creates censored data structure."""
    df = load_analysis_data(str(mock_dataset_path))
    
    # Check that we have a mix of resolved and censored
    n_censored = df['is_upper_limit'].sum()
    n_resolved = (~df['is_upper_limit']).sum()
    
    assert n_censored > 0, "Mock data should contain censored values"
    assert n_resolved > 0, "Mock data should contain resolved values"
    assert (n_censored + n_resolved) == len(df)

if __name__ == "__main__":
    # Allow running directly for debugging
    pytest.main([__file__, "-v"])
