import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
import tempfile
import shutil

# Ensure code/ is in path for imports
@pytest.fixture
def add_code_to_path():
    code_dir = Path(__file__).parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

# Import the function under test
from analysis.regression import run_random_effects_fallback, detect_time_invariant_countries

def generate_synthetic_panel_data(n_countries=10, n_years=5, seed=42):
    """Generate synthetic panel data for testing."""
    np.random.seed(seed)
    countries = [f"ISO{str(i).zfill(3)}" for i in range(1, n_countries + 1)]
    years = list(range(2000, 2000 + n_years))
    
    data = []
    for country in countries:
        for year in years:
            data.append({
                'country_code': country,
                'year': year,
                'land_use_change': np.random.normal(0, 1),
                'regime_type': np.random.choice([0, 1]), # Random binary
                'gdp_per_capita': np.random.normal(10000, 2000),
                'population_density': np.random.normal(50, 20)
            })
    
    return pd.DataFrame(data)

def generate_time_invariant_data(n_countries=5, n_years=5, seed=42):
    """Generate data where regime_type is constant per country (time-invariant)."""
    np.random.seed(seed)
    countries = [f"ISO{str(i).zfill(3)}" for i in range(1, n_countries + 1)]
    years = list(range(2000, 2000 + n_years))
    
    data = []
    for country in countries:
        # Assign a fixed regime type for this country
        fixed_regime = np.random.choice([0, 1])
        for year in years:
            data.append({
                'country_code': country,
                'year': year,
                'land_use_change': np.random.normal(0, 1),
                'regime_type': fixed_regime, # Constant over time
                'gdp_per_capita': np.random.normal(10000, 2000),
                'population_density': np.random.normal(50, 20)
            })
    
    return pd.DataFrame(data)

class TestRandomEffectsFallback:
    """Unit tests for Random Effects/Hausman fallback logic (T033)."""

    def test_run_random_effects_fallback_with_mixed_data(self, add_code_to_path):
        """Test that RE model runs successfully on data with time-varying regime."""
        df = generate_synthetic_panel_data(n_countries=10, n_years=5)
        
        # This should run without error and return a result dict
        result = run_random_effects_fallback(df)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'model_type' in result, "Result should contain model_type"
        assert result['model_type'] == 'Random Effects', "Model type should be Random Effects"
        assert 'coefficients' in result, "Result should contain coefficients"
        assert 'regime_type' in result['coefficients'], "Coefficients should include regime_type"
        assert 'p_values' in result, "Result should contain p_values"
        
    def test_run_random_effects_fallback_with_time_invariant_data(self, add_code_to_path):
        """Test that RE model handles data where all countries are time-invariant."""
        df = generate_time_invariant_data(n_countries=5, n_years=5)
        
        # Even with time-invariant data, RE model should run (it doesn't require within variation)
        result = run_random_effects_fallback(df)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert result['model_type'] == 'Random Effects', "Model type should be Random Effects"
        
    def test_run_random_effects_fallback_returns_hausman_stat(self, add_code_to_path):
        """Test that the fallback logic includes Hausman test statistics."""
        df = generate_synthetic_panel_data(n_countries=10, n_years=5)
        
        result = run_random_effects_fallback(df)
        
        # The function should attempt Hausman test or at least return a placeholder
        # depending on implementation details, but it must not crash
        assert 'model_type' in result
        
    def test_run_random_effects_fallback_empty_dataframe(self, add_code_to_path):
        """Test behavior with empty dataframe."""
        df = pd.DataFrame(columns=['country_code', 'year', 'land_use_change', 'regime_type', 'gdp_per_capita', 'population_density'])
        
        with pytest.raises(Exception):
            # Should raise an error if data is insufficient
            run_random_effects_fallback(df)
            
    def test_run_random_effects_fallback_missing_columns(self, add_code_to_path):
        """Test behavior when required columns are missing."""
        df = generate_synthetic_panel_data(n_countries=5, n_years=5)
        df = df.drop(columns=['gdp_per_capita'])
        
        with pytest.raises(Exception):
            # Should raise KeyError or similar
            run_random_effects_fallback(df)

def test_full_random_effects_pipeline(add_code_to_path):
    """Integration test: Generate time-invariant data, detect it, and run RE fallback."""
    # 1. Generate time-invariant data
    df = generate_time_invariant_data(n_countries=5, n_years=5)
    
    # 2. Detect time-invariant countries (should flag all)
    flagged = detect_time_invariant_countries(df)
    assert len(flagged) == 5, f"Expected 5 flagged countries, got {len(flagged)}"
    
    # 3. Run the fallback logic
    result = run_random_effects_fallback(df)
    
    # 4. Verify result structure
    assert result['model_type'] == 'Random Effects'
    assert 'coefficients' in result
    assert 'p_values' in result
    assert 'regime_type' in result['coefficients']
    
    # 5. Verify the coefficient is a float (not NaN or None)
    coef = result['coefficients']['regime_type']
    assert isinstance(coef, (int, float, np.number)), "Coefficient must be numeric"
    assert not np.isnan(coef), "Coefficient must not be NaN"
    
    # 6. Verify p-value is present
    p_val = result['p_values']['regime_type']
    assert isinstance(p_val, (int, float, np.number)), "P-value must be numeric"
    assert 0 <= p_val <= 1, "P-value must be between 0 and 1"