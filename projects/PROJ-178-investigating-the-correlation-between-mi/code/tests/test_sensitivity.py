"""
Test suite for User Story 3: Sensitivity and Robustness Analysis.

This module contains contract tests for the sensitivity analysis output schema
and integration tests for subgroup analysis functionality.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import yaml
import tempfile
import shutil

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Constants for expected schema
SENSITIVITY_OUTPUT_PATH = PROJECT_ROOT / "code" / "data" / "processed" / "sensitivity_analysis.csv"

# Expected columns based on T032, T033, T038 requirements
EXPECTED_COLUMNS = [
    "analysis_type",       # e.g., "threshold_sweep", "subgroup_ancestry", "depth_stratified"
    "parameter_value",     # e.g., VAF threshold (0.005, 0.01, 0.02) or ancestry (EUR, AFR)
    "coefficient",         # Regression coefficient
    "std_error",           # Standard error of the coefficient
    "p_value",             # Raw p-value
    "adj_p_value",         # Benjamini-Hochberg adjusted p-value
    "n_samples",           # Number of samples in the subset
    "r_squared"            # Optional: R-squared for the fit
]

def load_schema():
    """Load the expected schema definition if available, otherwise use hardcoded defaults."""
    schema_path = PROJECT_ROOT / "code" / "contracts" / "output.schema.yaml"
    if schema_path.exists():
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    return None

def load_dataset(path: Path):
    """Load the sensitivity analysis dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity analysis output not found at {path}")
    return pd.read_csv(path)

class TestSensitivityOutputSchema:
    """Contract tests for the sensitivity analysis output file."""

    def test_output_file_exists(self):
        """Verify that the sensitivity analysis output file exists."""
        # Note: This test may fail if the analysis script hasn't been run yet.
        # In a CI/CD pipeline, the analysis script should be run before these tests.
        assert SENSITIVITY_OUTPUT_PATH.exists(), (
            f"Sensitivity analysis output file not found at {SENSITIVITY_OUTPUT_PATH}. "
            "Ensure code/analysis/sensitivity.py has been executed."
        )

    def test_schema_columns_present(self):
        """Verify that all required columns are present in the output."""
        df = load_dataset(SENSITIVITY_OUTPUT_PATH)
        
        missing_columns = set(EXPECTED_COLUMNS) - set(df.columns)
        assert not missing_columns, (
            f"Missing required columns in sensitivity analysis output: {missing_columns}. "
            f"Expected columns: {EXPECTED_COLUMNS}, Found: {list(df.columns)}"
        )

    def test_column_data_types(self):
        """Verify that numeric columns contain numeric data."""
        df = load_dataset(SENSITIVITY_OUTPUT_PATH)
        
        numeric_columns = ["coefficient", "std_error", "p_value", "adj_p_value", "n_samples"]
        
        for col in numeric_columns:
            if col in df.columns:
                assert pd.api.types.is_numeric_dtype(df[col]) or \
                       pd.to_numeric(df[col], errors='coerce').notna().all(), \
                       f"Column '{col}' should be numeric but contains non-numeric values."

    def test_no_missing_critical_values(self):
        """Verify that critical result columns do not have NaN values."""
        df = load_dataset(SENSITIVITY_OUTPUT_PATH)
        
        critical_columns = ["analysis_type", "parameter_value", "coefficient", "p_value"]
        
        for col in critical_columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                assert missing_count == 0, (
                    f"Column '{col}' contains {missing_count} missing values. "
                    "Critical result columns must not have missing values."
                )

    def test_analysis_types_valid(self):
        """Verify that analysis_type values match expected categories."""
        df = load_dataset(SENSITIVITY_OUTPUT_PATH)
        
        if "analysis_type" in df.columns:
            valid_types = {"threshold_sweep", "subgroup_ancestry", "depth_stratified", "measurement_error"}
            found_types = set(df["analysis_type"].unique())
            
            invalid_types = found_types - valid_types
            assert not invalid_types, (
                f"Found invalid analysis types: {invalid_types}. "
                f"Valid types are: {valid_types}"
            )

    def test_p_value_range(self):
        """Verify that p-values are within the valid range [0, 1]."""
        df = load_dataset(SENSITIVITY_OUTPUT_PATH)
        
        if "p_value" in df.columns:
            assert (df["p_value"] >= 0).all() and (df["p_value"] <= 1).all(), \
                "All p-values must be between 0 and 1."
        
        if "adj_p_value" in df.columns:
            assert (df["adj_p_value"] >= 0).all() and (df["adj_p_value"] <= 1).all(), \
                "All adjusted p-values must be between 0 and 1."

    def test_n_samples_positive(self):
        """Verify that sample counts are positive integers."""
        df = load_dataset(SENSITIVITY_OUTPUT_PATH)
        
        if "n_samples" in df.columns:
            assert (df["n_samples"] > 0).all(), "Sample counts must be positive."
            assert (df["n_samples"] == df["n_samples"].astype(int)).all(), \
                "Sample counts must be integers."

class TestSubgroupAnalysis:
    """Integration tests for subgroup analysis functionality."""

    @pytest.fixture
    def sample_dataset(self):
        """Create a temporary sample dataset for testing subgroup analysis."""
        # Create a temporary directory for test data
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Create a sample dataset with ancestry information
        data = {
            'sample_id': [f'S{i:04d}' for i in range(100)],
            'burden': [0.01 * i for i in range(100)],
            'age': [30 + (i % 50) for i in range(100)],
            'sex': ['M' if i % 2 == 0 else 'F' for i in range(100)],
            'population': ['EUR' if i % 3 == 0 else 'AFR' if i % 3 == 1 else 'EAS' for i in range(100)],
            'PC1': [i * 0.1 for i in range(100)],
            'PC2': [i * 0.05 for i in range(100)],
            'depth': [30 + (i % 10) for i in range(100)]
        }
        
        df = pd.DataFrame(data)
        temp_file = temp_path / "sample_mito_dataset.csv"
        df.to_csv(temp_file, index=False)
        
        yield temp_file, temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_subgroup_filtering_by_ancestry(self, sample_dataset):
        """Test that subgroup analysis correctly filters by ancestry."""
        from analysis.sensitivity import filter_by_subgroup
        
        temp_file, temp_dir = sample_dataset
        df = pd.read_csv(temp_file)
        
        # Test filtering by EUR
        eur_df = filter_by_subgroup(df, 'population', 'EUR')
        assert len(eur_df) > 0
        assert all(eur_df['population'] == 'EUR')
        
        # Test filtering by AFR
        afr_df = filter_by_subgroup(df, 'population', 'AFR')
        assert len(afr_df) > 0
        assert all(afr_df['population'] == 'AFR')
        
        # Test filtering by EAS
        eas_df = filter_by_subgroup(df, 'population', 'EAS')
        assert len(eas_df) > 0
        assert all(eas_df['population'] == 'EAS')

    def test_subgroup_analysis_results(self, sample_dataset):
        """Test that subgroup analysis produces valid results for each ancestry group."""
        from analysis.sensitivity import run_subgroup_analysis
        
        temp_file, temp_dir = sample_dataset
        df = pd.read_csv(temp_file)
        
        # Run subgroup analysis
        results = run_subgroup_analysis(df, 'population')
        
        # Verify results structure
        assert isinstance(results, pd.DataFrame)
        assert 'analysis_type' in results.columns
        assert 'parameter_value' in results.columns
        assert 'coefficient' in results.columns
        assert 'p_value' in results.columns
        assert 'n_samples' in results.columns
        
        # Verify we have results for each ancestry group
        assert len(results) == 3  # EUR, AFR, EAS
        assert set(results['parameter_value']) == {'EUR', 'AFR', 'EAS'}
        
        # Verify sample counts are positive
        assert all(results['n_samples'] > 0)

    def test_subgroup_analysis_with_missing_groups(self, sample_dataset):
        """Test handling of missing ancestry groups in the dataset."""
        from analysis.sensitivity import run_subgroup_analysis
        
        temp_file, temp_dir = sample_dataset
        df = pd.read_csv(temp_file)
        
        # Create a dataset with only EUR and AFR (missing EAS)
        subset_df = df[df['population'].isin(['EUR', 'AFR'])]
        
        results = run_subgroup_analysis(subset_df, 'population')
        
        # Verify we only have results for present groups
        assert len(results) == 2
        assert set(results['parameter_value']) == {'EUR', 'AFR'}
        assert 'EAS' not in results['parameter_value'].values

    def test_subgroup_analysis_empty_result(self, sample_dataset):
        """Test handling of empty dataset."""
        from analysis.sensitivity import run_subgroup_analysis
        
        # Create empty dataframe with correct columns
        empty_df = pd.DataFrame(columns=['sample_id', 'burden', 'age', 'sex', 'population', 'PC1', 'PC2', 'depth'])
        
        results = run_subgroup_analysis(empty_df, 'population')
        
        # Verify empty result
        assert isinstance(results, pd.DataFrame)
        assert len(results) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])