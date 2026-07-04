"""
Integration test for the end-to-end analysis pipeline on a small synthetic dataset.

This test verifies that the statistical analysis module (T021) correctly
calculates Spearman correlation and p-values, and that the visualization
module (T023) generates valid output files.

Since the full data collection pipeline (US1) is not yet fully implemented
or populated with real data in this context, this test uses a small,
deterministic synthetic dataset to validate the logic of the analysis
and visualization components without external API dependencies.

The synthetic data is generated in-memory to simulate the output of T018.
"""
import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.data_models import Dependency, AnalysisResult
from src.analysis.correlation import calculate_spearman_correlation
from src.analysis.visualizer import generate_scatter_plot

# Synthetic dataset generator
def generate_synthetic_dataset(n_samples: int = 100) -> pd.DataFrame:
    """
    Generates a synthetic dataset mimicking the structure of data/processed/dependencies_raw.csv.
    
    The data is constructed to have a known correlation structure for verification.
    We create a positive correlation between age_in_days and vulnerability_count.
    """
    np.random.seed(42)  # Reproducibility
    
    # Generate age_in_days (0 to 3650 days)
    age = np.random.exponential(scale=500, size=n_samples)
    age = np.clip(age, 0, 3650)
    
    # Generate vulnerability_count with correlation to age
    # y = 0.005 * x + noise
    noise = np.random.normal(0, 2, n_samples)
    vuln = 0.005 * age + noise
    vuln = np.clip(vuln, 0, 50).astype(int)
    
    # Create DataFrame
    df = pd.DataFrame({
        'package_name': [f'pkg_{i}' for i in range(n_samples)],
        'dependency_name': [f'dep_{i}' for i in range(n_samples)],
        'age_in_days': age,
        'vulnerability_count': vuln,
        'last_release_date': [datetime.now().isoformat() for _ in range(n_samples)],
        'last_commit_date': [datetime.now().isoformat() for _ in range(n_samples)]
    })
    
    return df

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def synthetic_data(temp_data_dir):
    """Generate and save synthetic data to a CSV file."""
    df = generate_synthetic_dataset(n_samples=100)
    csv_path = temp_data_dir / "synthetic_dependencies.csv"
    df.to_csv(csv_path, index=False)
    return csv_path, df

def test_analysis_pipeline_end_to_end(synthetic_data, temp_data_dir):
    """
    End-to-end test of the analysis pipeline:
    1. Load synthetic data
    2. Calculate Spearman correlation
    3. Verify correlation coefficient and p-value are within expected bounds
    4. Generate scatter plot
    5. Verify plot file exists and is non-empty
    """
    csv_path, df = synthetic_data
    
    # Step 1: Load data (simulating T018 output)
    loaded_df = pd.read_csv(csv_path)
    assert len(loaded_df) == 100, "Dataset should have 100 rows"
    assert 'age_in_days' in loaded_df.columns, "age_in_days column missing"
    assert 'vulnerability_count' in loaded_df.columns, "vulnerability_count column missing"
    
    # Step 2: Calculate Spearman correlation (T021 logic)
    try:
        rho, p_value = calculate_spearman_correlation(
            loaded_df['age_in_days'], 
            loaded_df['vulnerability_count']
        )
    except Exception as e:
        pytest.fail(f"Correlation calculation failed: {e}")
    
    # Step 3: Verify correlation bounds
    # Spearman rho must be in [-1, 1]
    assert -1.0 <= rho <= 1.0, f"Correlation coefficient {rho} out of bounds [-1, 1]"
    
    # P-value must be in [0, 1]
    assert 0.0 <= p_value <= 1.0, f"P-value {p_value} out of bounds [0, 1]"
    
    # Check that we have a positive correlation (as constructed)
    # Allow some tolerance due to noise
    assert rho > 0, f"Expected positive correlation, got {rho}"
    
    # Step 4: Generate visualization (T023 logic)
    plot_path = temp_data_dir / "synthetic_scatter.png"
    try:
        generate_scatter_plot(
            loaded_df['age_in_days'],
            loaded_df['vulnerability_count'],
            str(plot_path),
            title="Synthetic Analysis Test: Age vs Vulnerabilities"
        )
    except Exception as e:
        pytest.fail(f"Visualization generation failed: {e}")
    
    # Step 5: Verify plot file exists and is non-empty
    assert plot_path.exists(), f"Plot file not created at {plot_path}"
    assert plot_path.stat().st_size > 0, "Plot file is empty"
    
    # Optional: Verify it's a valid PNG (starts with PNG signature)
    with open(plot_path, 'rb') as f:
        header = f.read(8)
        assert header[:4] == b'\x89PNG', "File does not appear to be a valid PNG"

def test_null_handling_in_correlation(synthetic_data, temp_data_dir):
    """
    Test that the correlation calculation handles missing/null values correctly.
    According to FR-010, dependencies with missing release metadata should
    have null age_in_days but still be included in vulnerability counts.
    This test ensures the correlation function can handle such data.
    """
    csv_path, df = synthetic_data
    
    # Introduce some null values in age_in_days
    df_with_nulls = df.copy()
    df_with_nulls.loc[0:9, 'age_in_days'] = None
    
    temp_csv = temp_data_dir / "null_test.csv"
    df_with_nulls.to_csv(temp_csv, index=False)
    
    loaded_df = pd.read_csv(temp_csv)
    
    # Calculate correlation - should handle NaNs by dropping them
    rho, p_value = calculate_spearman_correlation(
        loaded_df['age_in_days'],
        loaded_df['vulnerability_count']
    )
    
    # Should still produce valid results
    assert -1.0 <= rho <= 1.0, "Correlation with nulls should be in bounds"
    assert 0.0 <= p_value <= 1.0, "P-value with nulls should be in bounds"

def test_empty_dataset_handling(temp_data_dir):
    """
    Test behavior with an empty dataset.
    """
    empty_df = pd.DataFrame(columns=['age_in_days', 'vulnerability_count'])
    csv_path = temp_data_dir / "empty.csv"
    empty_df.to_csv(csv_path, index=False)
    
    loaded_df = pd.read_csv(csv_path)
    
    # Should raise a meaningful error or return None for empty data
    with pytest.raises((ValueError, TypeError)):
        calculate_spearman_correlation(
            loaded_df['age_in_days'],
            loaded_df['vulnerability_count']
        )