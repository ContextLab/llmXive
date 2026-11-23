import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import sys
import tempfile
import shutil
from src.data_generator import inject_outliers, generate_normal_distribution

class TestDataGenerator:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_inject_outliers_cauchy(self, temp_dir):
        """Test Cauchy outlier injection creates expected files and profile."""
        # Generate clean data
        n = 1000
        clean_df, _ = generate_normal_distribution(n, 0, 1, seed=42)
        clean_path = temp_dir / "clean.csv"
        clean_df.to_csv(clean_path, index=False)

        # Inject outliers
        output_path = temp_dir / "contaminated"
        rates = [0.0, 0.1]
        
        profile = inject_outliers(
            input_path=clean_path,
            output_path=output_path,
            contamination_rates=rates,
            outlier_method='cauchy',
            cauchy_scale=10.0,
            seed=42
        )

        # Verify profile exists and has correct structure
        assert 'contamination_rates' in profile
        assert profile['contamination_rates'] == rates
        assert profile['outlier_method'] == 'cauchy'
        
        # Verify output files exist
        assert output_path.parent.exists()
        
        # Check specific files
        rate_0_file = output_path.parent / "contaminated_clean_0p00.csv"
        rate_1_file = output_path.parent / "contaminated_clean_0p10.csv"
        
        assert rate_0_file.exists()
        assert rate_1_file.exists()

        # Verify data integrity
        df_0 = pd.read_csv(rate_0_file)
        df_1 = pd.read_csv(rate_1_file)
        
        assert len(df_0) == n
        assert len(df_1) == n
        
        # Check that 0% contamination has same variance (approx) as clean
        clean_var = clean_df['value'].var()
        var_0 = df_0['value'].var()
        # Allow small floating point differences
        assert np.isclose(clean_var, var_0, rtol=1e-5)

        # Check that 10% contamination has higher variance
        var_1 = df_1['value'].var()
        assert var_1 > clean_var

    def test_inject_outliers_extreme(self, temp_dir):
        """Test Extreme outlier injection creates expected files."""
        # Generate clean data
        n = 500
        clean_df, _ = generate_normal_distribution(n, 10, 2, seed=123)
        clean_path = temp_dir / "clean_ext.csv"
        clean_df.to_csv(clean_path, index=False)

        output_path = temp_dir / "contaminated_ext"
        rates = [0.05]
        
        profile = inject_outliers(
            input_path=clean_path,
            output_path=output_path,
            contamination_rates=rates,
            outlier_method='extreme',
            extreme_multiplier=10.0,
            seed=42
        )

        assert profile['outlier_method'] == 'extreme'
        
        file_path = output_path.parent / "contaminated_clean_ext_0p05.csv"
        assert file_path.exists()
        
        df = pd.read_csv(file_path)
        # Verify outliers are present (max value should be much larger than original max)
        original_max = clean_df['value'].max()
        contaminated_max = df['value'].max()
        
        assert contaminated_max > original_max * 5  # Should be significantly larger

    def test_injection_profile_json(self, temp_dir):
        """Test that injection_profile.json is created correctly."""
        clean_df, _ = generate_normal_distribution(100, 0, 1, seed=42)
        clean_path = temp_dir / "clean_json.csv"
        clean_df.to_csv(clean_path, index=False)

        output_path = temp_dir / "contaminated_json"
        rates = [0.0, 0.05]
        
        inject_outliers(
            input_path=clean_path,
            output_path=output_path,
            contamination_rates=rates,
            outlier_method='cauchy',
            seed=42
        )

        profile_path = output_path.parent / "injection_profile.json"
        assert profile_path.exists()
        
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        
        assert 'source_file' in profile
        assert 'original_count' in profile
        assert 'results' in profile
        assert len(profile['results']) == len(rates)