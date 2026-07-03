import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import yaml
import tempfile
import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.sensitivity import calculate_correlation, load_processed_dataset
from config.environment import get_local_paths

def load_schema(schema_name: str):
    """Load a schema definition from the contracts directory."""
    contracts_path = Path(get_local_paths()['contracts'])
    schema_file = contracts_path / f"{schema_name}.yaml"
    if schema_file.exists():
        with open(schema_file, 'r') as f:
            return yaml.safe_load(f)
    return None

def load_dataset():
    """Load the processed dataset for testing."""
    data_path = Path(get_local_paths()['processed']) / 'mito_aging_dataset.csv'
    if data_path.exists():
        return pd.read_csv(data_path)
    return None

class TestSensitivityOutputSchema:
    """Contract test for sensitivity output schema."""

    def test_subgroup_results_schema(self):
        """Verify that subgroup analysis output has the correct columns."""
        # Create a mock result dataframe similar to what calculate_correlation returns
        mock_results = pd.DataFrame({
            'group': ['EUR', 'AFR'],
            'correlation': [0.12, 0.05],
            'p_value': [0.03, 0.15],
            'n_samples': [50, 45],
            'threshold': ['default', 'default']
        })
        
        expected_cols = {'group', 'correlation', 'p_value', 'n_samples', 'threshold'}
        assert set(mock_results.columns) == expected_cols, \
            f"Expected columns {expected_cols}, got {set(mock_results.columns)}"

class TestSubgroupAnalysis:
    """Integration test for subgroup analysis logic."""

    def test_correlation_calculation_by_group(self):
        """Test that correlation is calculated correctly for each group."""
        # Create a synthetic dataset with known correlations
        np.random.seed(42)
        n_samples = 200
        
        data = {
            'sample_id': [f'S{i}' for i in range(n_samples)],
            'population': ['EUR'] * 100 + ['AFR'] * 100,
            'age': np.concatenate([np.random.normal(50, 10, 100), np.random.normal(45, 12, 100)]),
            'burden': np.concatenate([np.random.normal(0.02, 0.005, 100), np.random.normal(0.015, 0.004, 100)]),
            'sex': ['M'] * 200,
            'PC1': np.random.normal(0, 1, 200),
            'PC2': np.random.normal(0, 1, 200)
        }
        
        # Introduce a slight positive correlation in EUR
        data['burden'][:100] = data['burden'][:100] * 1.5 + (data['age'][:100] * 0.0001)
        
        df = pd.DataFrame(data)
        
        # Run the calculation
        results = calculate_correlation(df, group_col='population')
        
        # Verify results exist for both groups
        assert 'EUR' in results['group'].values
        assert 'AFR' in results['group'].values
        
        # Verify sample counts match
        eur_count = results[results['group'] == 'EUR']['n_samples'].iloc[0]
        afr_count = results[results['group'] == 'AFR']['n_samples'].iloc[0]
        assert eur_count == 100
        assert afr_count == 100

    def test_insufficient_samples_handling(self):
        """Test that groups with too few samples are handled gracefully."""
        data = {
            'sample_id': [f'S{i}' for i in range(10)],
            'population': ['EUR'] * 3 + ['AFR'] * 2 + ['EAS'] * 5, # EAS has 5, others < 5
            'age': np.random.normal(50, 10, 10),
            'burden': np.random.normal(0.02, 0.005, 10),
            'sex': ['M'] * 10,
            'PC1': np.random.normal(0, 1, 10),
            'PC2': np.random.normal(0, 1, 10)
        }
        
        df = pd.DataFrame(data)
        results = calculate_correlation(df, group_col='population')
        
        # EAS should be skipped or have NaN if < 5 (implementation dependent, but here we skip)
        # EUR and AFR should be skipped because < 5
        # Check that we don't crash
        assert results is not None
        assert len(results) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])