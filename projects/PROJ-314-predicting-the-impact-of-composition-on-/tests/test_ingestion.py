import pytest
import pandas as pd
import numpy as np
from code.ingestion import (
    derive_primary_anion_cation_group,
    filter_valid_sample_count,
    filter_valid_stoichiometry,
    handle_range_values,
    impute_missing_params,
    clean_data_pipeline
)

class TestDerivePrimaryAnionCationGroup:
    def test_alumina(self):
        # Al2O3 -> O-Al (Anion-Cation)
        result = derive_primary_anion_cation_group("Al2O3")
        assert "O" in result
        assert "Al" in result
        assert result.count("-") == 1

    def test_silicon_carbide(self):
        # SiC -> C-Si (Anion-Cation)
        result = derive_primary_anion_cation_group("SiC")
        assert "C" in result
        assert "Si" in result

    def test_invalid_composition(self):
        result = derive_primary_anion_cation_group("Invalid!!")
        assert result == "Unknown"

    def test_empty_composition(self):
        result = derive_primary_anion_cation_group("")
        assert result == "Unknown"

class TestFilterValidSampleCount:
    def test_filter_below_threshold(self):
        df = pd.DataFrame({
            'composition': ['Al2O3', 'SiC'],
            'sample_count': [10, 50],
            'weibull_modulus': [10, 20]
        })
        result = filter_valid_sample_count(df)
        assert len(result) == 1
        assert result.iloc[0]['sample_count'] == 50

    def test_filter_no_column(self):
        df = pd.DataFrame({
            'composition': ['Al2O3'],
            'weibull_modulus': [10]
        })
        result = filter_valid_sample_count(df)
        assert len(result) == 0

class TestFilterValidStoichiometry:
    def test_valid_stoichiometry(self):
        df = pd.DataFrame({
            'composition': ['Al2O3', 'SiC'],
            'weibull_modulus': [10, 20]
        })
        result = filter_valid_stoichiometry(df)
        assert len(result) == 2

    def test_invalid_stoichiometry(self):
        df = pd.DataFrame({
            'composition': ['Al2O3', 'Invalid!!'],
            'weibull_modulus': [10, 20]
        })
        result = filter_valid_stoichiometry(df)
        assert len(result) == 1

class TestHandleRangeValues:
    def test_range_input(self):
        df = pd.DataFrame({
            'weibull_modulus': ['10-20', 15.0, None]
        })
        result = handle_range_values(df)
        assert result['weibull_modulus'].iloc[0] == 15.0
        assert result['is_range_flag'].iloc[0] == True
        assert result['range_uncertainty'].iloc[0] == 10.0
        assert result['weibull_modulus'].iloc[1] == 15.0
        assert result['is_range_flag'].iloc[1] == False

class TestImputeMissingParams:
    def test_impute_with_group(self):
        df = pd.DataFrame({
            'composition': ['Al2O3', 'Al2O3', 'SiC'],
            'primary_anion_cation_group': ['O-Al', 'O-Al', 'C-Si'],
            'sintering_temp': [1000.0, np.nan, 2000.0]
        })
        result = impute_missing_params(df)
        # The NaN should be imputed to 1000.0 (group median of O-Al)
        assert result['sintering_temp'].iloc[1] == 1000.0
        assert result['is_imputed'].iloc[1] == True

class TestCleanDataPipeline:
    def test_full_pipeline(self):
        df = pd.DataFrame({
            'composition': ['Al2O3', 'SiC', 'Invalid', 'Al2O3'],
            'sample_count': [50, 10, 50, 50], # SiC has N=10 (<30), Invalid is bad
            'weibull_modulus': [15.0, 20.0, '10-20', 18.0],
            'sintering_temp': [1500.0, 1800.0, np.nan, 1600.0]
        })
        result = clean_data_pipeline(df)
        # Should keep Al2O3 (50), drop SiC (10), drop Invalid (bad comp)
        # Should have 2 rows: Al2O3, Al2O3
        assert len(result) == 2
        assert 'primary_anion_cation_group' in result.columns
        assert 'weibull_modulus' in result.columns
        assert 'is_range_flag' in result.columns
        assert 'is_imputed' in result.columns