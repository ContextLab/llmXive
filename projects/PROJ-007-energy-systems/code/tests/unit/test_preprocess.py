import pytest
import pandas as pd
import numpy as np
from src.data.preprocess import (
    filter_low_income,
    winsorize,
    construct_treatment,
    check_adopter_power,
    PowerError,
    handle_missing_values,
    preprocess_pipeline
)


@pytest.fixture
def sample_data():
    """Create a sample DataFrame for testing."""
    data = {
        'household_id': range(100),
        'income_fpl_ratio': np.random.uniform(0.5, 3.0, 100),
        'solar_installation': np.random.choice([0, 1], 100, p=[0.9, 0.1]),
        'energy_cost': np.random.exponential(500, 100),
        'income': np.random.exponential(40000, 100),
        'housing_type': np.random.choice(['rent', 'own'], 100),
        'location': np.random.choice(['urban', 'rural'], 100)
    }
    return pd.DataFrame(data)


@pytest.fixture
def data_with_missing():
    """Create a DataFrame with intentional missing values."""
    df = pd.DataFrame({
        'income': [1000.0, 2000.0, np.nan, 4000.0, 5000.0],
        'housing_type': ['rent', np.nan, 'own', 'rent', 'own'],
        'energy_cost': [100.0, 200.0, 300.0, np.nan, 500.0]
    })
    return df


def test_filter_low_income(sample_data):
    """Test that filter_low_income correctly filters for income < 150% FPL."""
    result = filter_low_income(sample_data)

    # All remaining rows should have income_fpl_ratio < 1.5
    assert all(result['income_fpl_ratio'] < 1.5)
    assert len(result) < len(sample_data)


def test_filter_low_income_missing_column(sample_data):
    """Test that filter_low_income raises KeyError if column is missing."""
    df = sample_data.drop(columns=['income_fpl_ratio'])
    with pytest.raises(KeyError):
        filter_low_income(df)


def test_winsorize(sample_data):
    """Test that winsorize caps values at specified percentiles."""
    # Create data with extreme outliers
    df = sample_data.copy()
    df.loc[0, 'energy_cost'] = 100000  # Extreme outlier
    df.loc[1, 'energy_cost'] = 0.001   # Extreme low

    result = winsorize(df, lower=0.01, upper=0.99)

    # Check that extreme values are capped
    # The exact values depend on the random seed, but they should be within bounds
    q1 = df['energy_cost'].quantile(0.01)
    q99 = df['energy_cost'].quantile(0.99)

    assert result['energy_cost'].min() >= q1
    assert result['energy_cost'].max() <= q99


def test_construct_treatment(sample_data):
    """Test that construct_treatment creates a binary treatment column."""
    result = construct_treatment(sample_data)

    assert 'treatment' in result.columns
    assert result['treatment'].isin([0, 1]).all()
    assert len(result[result['treatment'] == 1]) > 0  # Should have some adopters


def test_construct_treatment_missing_column(sample_data):
    """Test that construct_treatment raises KeyError if indicator is missing."""
    df = sample_data.drop(columns=['solar_installation'])
    with pytest.raises(KeyError):
        construct_treatment(df)


def test_check_adopter_power(sample_data):
    """Test that check_adopter_power raises PowerError if adopters < 50."""
    # First construct treatment to ensure column exists
    df = construct_treatment(sample_data)

    # If we have > 50 adopters, it should pass
    if df['treatment'].sum() >= 50:
        check_adopter_power(df)  # Should not raise
    else:
        with pytest.raises(PowerError):
            check_adopter_power(df)


def test_check_adopter_power_fails(sample_data):
    """Test that check_adopter_power raises PowerError with insufficient adopters."""
    # Create data with very few adopters
    df = sample_data.copy()
    df['solar_installation'] = 0
    df.loc[0, 'solar_installation'] = 1  # Only 1 adopter

    df = construct_treatment(df)

    with pytest.raises(PowerError):
        check_adopter_power(df, min_adopters=50)


def test_median_imputation_continuous(data_with_missing):
    """Test median imputation for continuous variables."""
    result = handle_missing_values(data_with_missing)

    assert result['income'].isnull().sum() == 0
    assert result['energy_cost'].isnull().sum() == 0

    # Check that imputed value is the median
    expected_median = data_with_missing['income'].median()
    assert result.loc[2, 'income'] == expected_median


def test_missing_flag_categorical(data_with_missing):
    """Test 'Missing' flag for categorical variables."""
    result = handle_missing_values(data_with_missing)

    assert result['housing_type'].isnull().sum() == 0
    assert result.loc[1, 'housing_type'] == 'Missing'


def test_no_silent_data_loss(data_with_missing):
    """Ensure no data is dropped during imputation."""
    assert len(data_with_missing) == len(handle_missing_values(data_with_missing))


def test_nonexistent_columns():
    """Test pipeline with missing required columns."""
    df = pd.DataFrame({'random_col': [1, 2, 3]})
    with pytest.raises(KeyError):
        preprocess_pipeline(df)


def test_preprocess_pipeline(sample_data):
    """Test the full pipeline execution."""
    # Ensure we have enough adopters for the test
    sample_data['solar_installation'] = 1  # Force all to be adopters for power check

    result = preprocess_pipeline(sample_data)

    assert 'treatment' in result.columns
    assert all(result['income_fpl_ratio'] < 1.5)
    assert result.isnull().sum().sum() == 0  # No missing values left
    assert len(result) > 0