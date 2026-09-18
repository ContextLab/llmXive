import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.main import run_pipeline, load_config
from src.analysis.causal import DataUnavailableError
from src.models.schemas import AnalysisResult, GracefulDegradationStatus

def test_pipeline_halts_on_balance_failure_and_missing_longitudinal_data():
    """
    Test T053: Verify that the pipeline halts with a clear error message
    when PSM balance fails and longitudinal data is missing (DiD impossible).
    """
    # Mock config
    mock_config = {
        'seeds': {'numpy': 42, 'pandas': 42, 'python': 42},
        'paths': {
            'eia_url': 'http://fake.url',
            'acs_tract_ids': ['123'],
            'output_json': '/tmp/test_output.json'
        },
        'thresholds': {
            'smd_limit': 0.1
        },
        'analysis': {
            'cluster_var': 'pair_id',
            'calipers': [0.1, 0.2]
        }
    }

    # Mock data ingestion
    mock_eia = pd.DataFrame({'income': [10000], 'energy_cost': [500], 'solar_installation': [0]})
    mock_acs = pd.DataFrame({'tract_id': ['123'], 'median_income': [30000]})

    # Mock preprocessing to return a dataframe
    mock_processed = pd.DataFrame({
        'income': [10000, 20000],
        'energy_cost': [500, 600],
        'treatment': [1, 0],
        'housing_type': ['rent', 'own'],
        'location': ['rural', 'urban']
    })

    # Mock PSM to simulate balance failure
    # We need to make iterative_matching return a status that indicates failure
    # or we need to mock the balance check logic inside run_pipeline
    
    # Instead of mocking the whole pipeline, we mock the specific check
    # that leads to the DataUnavailableError
    
    with patch('src.main.fetch_eia_rec', return_value=mock_eia), \
         patch('src.main.fetch_acs', return_value=mock_acs), \
         patch('src.main.preprocess_pipeline', return_value=mock_processed), \
         patch('src.main.iterative_matching', return_value=(mock_processed, "failed")), \
         patch('src.main.calculate_smd', return_value={'income': 0.2}), \
         patch('src.main.check_placebo_significance', return_value=False):
         
        # The pipeline should raise DataUnavailableError because balance failed
        # and longitudinal data is missing (by design of the project)
        with pytest.raises(DataUnavailableError) as excinfo:
            run_pipeline(mock_config)
        
        assert "Causal Identification Failure" in str(excinfo.value)
        assert "DiD Fallback Impossible" in str(excinfo.value)

def test_pipeline_succeeds_on_balance_pass():
    """
    Test that the pipeline proceeds to OLS if balance passes.
    """
    mock_config = {
        'seeds': {'numpy': 42, 'pandas': 42, 'python': 42},
        'paths': {
            'eia_url': 'http://fake.url',
            'acs_tract_ids': ['123'],
            'output_json': '/tmp/test_output_success.json'
        },
        'thresholds': {
            'smd_limit': 0.1
        },
        'analysis': {
            'cluster_var': 'pair_id',
            'calipers': [0.1, 0.2]
        }
    }

    mock_eia = pd.DataFrame({'income': [10000], 'energy_cost': [500], 'solar_installation': [0]})
    mock_acs = pd.DataFrame({'tract_id': ['123'], 'median_income': [30000]})
    mock_processed = pd.DataFrame({
        'income': [10000, 20000],
        'energy_cost': [500, 600],
        'treatment': [1, 0],
        'housing_type': ['rent', 'own'],
        'location': ['rural', 'urban']
    })

    # Mock successful PSM and balance
    with patch('src.main.fetch_eia_rec', return_value=mock_eia), \
         patch('src.main.fetch_acs', return_value=mock_acs), \
         patch('src.main.preprocess_pipeline', return_value=mock_processed), \
         patch('src.main.iterative_matching', return_value=(mock_processed, "passed")), \
         patch('src.main.calculate_smd', return_value={'income': 0.05}), \
         patch('src.main.check_placebo_significance', return_value=True), \
         patch('src.main.run_ols') as mock_ols, \
         patch('src.main.estimate_causal_effect', return_value=(0.5, 0.01, (0.1, 0.9))), \
         patch('src.main.sweep_caliper', return_value={}), \
         patch('src.main.save_analysis_result'):
         
        mock_ols.return_value = MagicMock()
        
        result = run_pipeline(mock_config)
        
        assert result.status == "success"
        assert result.att_estimate == 0.5
        assert result.graceful_degradation_status is None
