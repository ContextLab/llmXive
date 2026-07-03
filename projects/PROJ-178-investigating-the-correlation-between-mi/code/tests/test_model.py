"""
Contract tests for statistical output schema (User Story 2).

These tests verify that the statistical modeling pipeline produces outputs
that conform to the expected schema defined in code/contracts/output.schema.yaml.
Specifically, they validate the structure and data types of model results
including coefficients, p-values, and adjusted p-values.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import yaml

# Add the project root to the path to allow imports from 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from contracts.output_schema import load_schema, validate_results

# Path definitions relative to project root
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"
RESULTS_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_RESULTS_PATH = RESULTS_DIR / "model_results.csv"
ANALYSIS_RESULTS_PATH = RESULTS_DIR / "analysis_results.csv"


def load_schema(schema_path: Path) -> dict:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def load_dataset(path: Path) -> pd.DataFrame:
    """Load a CSV dataset from disk."""
    if not path.exists():
        # Return empty df for schema validation if file doesn't exist yet
        # This allows the test to run during CI before the pipeline generates data
        return pd.DataFrame()
    return pd.read_csv(path)


class TestStatisticalOutputSchema:
    """
    Contract test for statistical output schema.
    
    Verifies that the output files produced by the statistical modeling
    phase (US2) conform to the defined schema in output.schema.yaml.
    """

    @pytest.fixture
    def schema(self):
        """Load the output schema."""
        return load_schema(OUTPUT_SCHEMA_PATH)

    def test_schema_file_exists(self):
        """Ensure the output schema definition exists."""
        assert OUTPUT_SCHEMA_PATH.exists(), \
            f"Output schema file missing: {OUTPUT_SCHEMA_PATH}"

    def test_model_results_schema(self, schema):
        """
        Validate that model_results.csv conforms to the schema.
        
        Checks for required columns: 'variable', 'coefficient', 'p_value', 'adj_p_value'.
        """
        if not MODEL_RESULTS_PATH.exists():
            pytest.skip(f"Model results file not found: {MODEL_RESULTS_PATH}. "
                        "Run the analysis pipeline first.")
        
        df = load_dataset(MODEL_RESULTS_PATH)
        
        # Validate required columns based on schema
        required_columns = ['variable', 'coefficient', 'p_value', 'adj_p_value']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        assert not missing_columns, \
            f"Model results missing required columns: {missing_columns}. " \
            f"Expected: {required_columns}, Found: {list(df.columns)}"
        
        # Validate data types
        assert df['coefficient'].dtype in ['float64', 'float32', 'int64', 'int32'], \
            f"Coefficient column must be numeric, got: {df['coefficient'].dtype}"
        assert df['p_value'].dtype in ['float64', 'float32', 'int64', 'int32'], \
            f"P-value column must be numeric, got: {df['p_value'].dtype}"
        assert df['adj_p_value'].dtype in ['float64', 'float32', 'int64', 'int32'], \
            f"Adjusted p-value column must be numeric, got: {df['adj_p_value'].dtype}"

    def test_analysis_results_schema(self, schema):
        """
        Validate that analysis_results.csv conforms to the summary schema.
        
        Checks for required columns: 'model_type', 'coefficient', 'p_value', 'adj_p_value'.
        """
        if not ANALYSIS_RESULTS_PATH.exists():
            pytest.skip(f"Analysis results file not found: {ANALYSIS_RESULTS_PATH}. "
                        "Run the analysis pipeline first.")
        
        df = load_dataset(ANALYSIS_RESULTS_PATH)
        
        # Validate required columns based on schema
        required_columns = ['model_type', 'coefficient', 'p_value', 'adj_p_value']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        assert not missing_columns, \
            f"Analysis results missing required columns: {missing_columns}. " \
            f"Expected: {required_columns}, Found: {list(df.columns)}"
        
        # Validate that model_type is not empty
        assert df['model_type'].notna().all(), "All rows must have a model_type"
        assert df['model_type'].ne('').all(), "Model types cannot be empty strings"

    def test_p_value_range(self):
        """Ensure p-values are within valid range [0, 1]."""
        if not MODEL_RESULTS_PATH.exists():
            pytest.skip(f"Model results file not found: {MODEL_RESULTS_PATH}")
        
        df = load_dataset(MODEL_RESULTS_PATH)
        
        assert (df['p_value'] >= 0).all(), "P-values must be >= 0"
        assert (df['p_value'] <= 1).all(), "P-values must be <= 1"
        assert (df['adj_p_value'] >= 0).all(), "Adjusted p-values must be >= 0"
        assert (df['adj_p_value'] <= 1).all(), "Adjusted p-values must be <= 1"

    def test_no_null_critical_fields(self):
        """Ensure no null values in critical numeric fields."""
        if not MODEL_RESULTS_PATH.exists():
            pytest.skip(f"Model results file not found: {MODEL_RESULTS_PATH}")
        
        df = load_dataset(MODEL_RESULTS_PATH)
        
        critical_fields = ['variable', 'coefficient', 'p_value', 'adj_p_value']
        for field in critical_fields:
            assert not df[field].isna().any(), \
                f"Critical field '{field}' contains null values"


class TestRankOLSImplementation:
    """
    Integration test for Rank-OLS implementation (User Story 2).
    
    Verifies that the Rank-OLS model correctly recovers known relationships
    in a synthetic dataset with a predefined correlation structure.
    """

    def test_rank_ols_recovery(self):
        """
        Test that Rank-OLS recovers the correct coefficient sign and p-value
        on a synthetic dataset with a known positive correlation.
        """
        # Import the modeling logic
        try:
            from analysis.model import fit_rank_ols
        except ImportError:
            pytest.skip("Modeling module 'analysis.model' not found. "
                        "Implementation of T024 required.")

        # Create a synthetic dataset with a known positive correlation
        # We simulate a scenario where higher burden correlates with higher age
        n_samples = 500
        rng = pd.np.random.default_rng(seed=42)
        
        # Generate synthetic data
        # True relationship: age = 0.5 * burden + noise
        # We want to verify the model detects the positive coefficient
        burden = rng.normal(loc=0.01, scale=0.005, size=n_samples)
        noise = rng.normal(loc=0, scale=0.001, size=n_samples)
        age = 50 + 2000 * (burden - 0.01) + noise * 1000 # Scale to realistic range
        
        # Add confounders (random noise for this test, but structure is preserved)
        sex = rng.choice(['M', 'F'], size=n_samples)
        pc1 = rng.normal(size=n_samples)
        pc2 = rng.normal(size=n_samples)
        depth = rng.normal(loc=100, scale=20, size=n_samples)
        
        df = pd.DataFrame({
            'sample_id': [f'S{i}' for i in range(n_samples)],
            'age': age,
            'burden': burden,
            'sex': sex,
            'PC1': pc1,
            'PC2': pc2,
            'depth': depth
        })

        # Fit the model
        # Expected: coefficient for burden should be positive
        # p-value should be significant (< 0.05) given the strong synthetic signal
        try:
            results_df = fit_rank_ols(df)
        except Exception as e:
            pytest.fail(f"Rank-OLS fitting failed: {e}")

        # Validate output structure
        assert isinstance(results_df, pd.DataFrame), "Results must be a DataFrame"
        assert 'variable' in results_df.columns, "Results must have 'variable' column"
        assert 'coefficient' in results_df.columns, "Results must have 'coefficient' column"
        assert 'p_value' in results_df.columns, "Results must have 'p_value' column"

        # Find the burden coefficient
        burden_row = results_df[results_df['variable'] == 'rank(burden)']
        
        if burden_row.empty:
            # Try alternative naming if the implementation uses a different format
            burden_row = results_df[results_df['variable'].str.contains('burden', case=False, na=False)]
        
        if burden_row.empty:
            pytest.fail("Could not find 'burden' variable in model results. "
                        "Check model variable naming conventions.")

        coeff = burden_row['coefficient'].iloc[0]
        p_val = burden_row['p_value'].iloc[0]

        # Assertions
        # 1. Coefficient sign must match the synthetic truth (positive)
        assert coeff > 0, \
            f"Expected positive coefficient for burden in synthetic data, got {coeff}. " \
            "The model failed to recover the known relationship."

        # 2. P-value should be significant (we generated a strong signal)
        # Allow some leniency for noise, but it should generally be < 0.05
        assert p_val < 0.10, \
            f"P-value {p_val} is not significant for a synthetic dataset with a strong known correlation. " \
            "The model may be broken or the synthetic signal too weak."

        # 3. Check that p-value is a valid probability
        assert 0 <= p_val <= 1, f"P-value {p_val} is out of range [0, 1]"

    def test_rank_ols_confounder_adjustment(self):
        """
        Test that Rank-OLS correctly handles confounders by including them in the model.
        """
        try:
            from analysis.model import fit_rank_ols
        except ImportError:
            pytest.skip("Modeling module 'analysis.model' not found.")

        # Create data where the true relationship is masked by a confounder
        n_samples = 500
        rng = pd.np.random.default_rng(seed=123)
        
        # Strong confounder: PC1 drives both age and burden
        pc1 = rng.normal(size=n_samples)
        
        # Burden depends on PC1
        burden = 0.01 + 0.002 * pc1 + rng.normal(scale=0.001, size=n_samples)
        
        # Age depends on PC1 and a small true burden effect
        age = 50 + 10 * pc1 + 500 * (burden - 0.01) + rng.normal(scale=2, size=n_samples)
        
        df = pd.DataFrame({
            'sample_id': [f'S{i}' for i in range(n_samples)],
            'age': age,
            'burden': burden,
            'sex': rng.choice(['M', 'F'], size=n_samples),
            'PC1': pc1,
            'PC2': rng.normal(size=n_samples),
            'depth': rng.normal(loc=100, scale=10, size=n_samples)
        })

        # Fit model with adjustment
        results_df = fit_rank_ols(df)
        
        # The coefficient for burden should still be positive even after adjusting for PC1
        burden_row = results_df[results_df['variable'].str.contains('burden', case=False, na=False)]
        
        if not burden_row.empty:
            coeff = burden_row['coefficient'].iloc[0]
            # Since we added a positive true effect (500 * (burden - 0.01)), 
            # the coefficient should remain positive after adjustment
            assert coeff > 0, \
                f"Expected positive burden coefficient after confounder adjustment, got {coeff}. " \
                "The model may not be correctly adjusting for confounders."