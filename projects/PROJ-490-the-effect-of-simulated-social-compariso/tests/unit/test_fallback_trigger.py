import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import json
import os

from data.download import (
    check_fallback_trigger, 
    generate_synthetic_dataset, 
    DataFetchError,
    NoRealDataFoundError
)
from data.config import get_config, reset_config

class TestFallbackTrigger:
    
    def test_fallback_when_no_real_data(self):
        """
        Test that fallback triggers when discover_real_datasets returns False.
        """
        with patch('data.download.discover_real_datasets', return_value=(False, None, None)):
            decision = check_fallback_trigger()
            
            assert decision['decision'] == 'synthetic'
            assert 'No real dataset found' in decision['reason']
            assert decision['source'] is None

    def test_fallback_when_irb_missing(self):
        """
        Test that fallback triggers when IRB verification fails.
        """
        mock_metadata = {'consent_form_url': 'http://example.com/missing'}
        with patch('data.download.discover_real_datasets', return_value=(True, 'fake_ds', mock_metadata)):
            with patch('data.download.verify_irb_consent', return_value=False):
                decision = check_fallback_trigger()
                
                assert decision['decision'] == 'synthetic'
                assert 'IRB/Consent verification failed' in decision['reason']
                assert decision['source'] == 'fake_ds'

    def test_synthetic_generation_parameters(self):
        """
        Test that synthetic generation uses correct ground truth parameters.
        """
        df = generate_synthetic_dataset(n_samples=10, seed=42)
        
        assert len(df) == 10
        assert set(df.columns) == {
            'participant_id', 'pre_self_esteem', 'post_self_esteem', 
            'comparison_tendency', 'avatar_condition'
        }
        assert df['avatar_condition'].isin([0, 1]).all()

    def test_fallback_trigger_logs_decision(self):
        """
        Test that the decision is logged correctly.
        """
        with patch('data.download.discover_real_datasets', return_value=(False, None, None)):
            with patch('data.download.write_state_decision') as mock_state:
                with patch('data.download.log_fallback_decision') as mock_log:
                    decision = check_fallback_trigger()
                    
                    mock_state.assert_called_once()
                    mock_log.assert_called_once()
                    mock_log.assert_called_with(decision)