import pytest
import os
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.download import load_or_generate_data, discover_real_datasets, verify_irb_consent, generate_synthetic_dataset
from data.config import Config, get_config, reset_config

class TestDataPathDecision:
    """Test T039: Synthetic data generator trigger conditions."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup temporary config for each test."""
        self.tmp_dir = tmp_path
        self.logs_dir = self.tmp_dir / 'logs'
        self.logs_dir.mkdir()
        self.raw_data_dir = self.tmp_dir / 'data' / 'raw'
        self.raw_data_dir.mkdir(parents=True)
        
        # Create a temporary config
        self.config = Config(
            project_root=str(self.tmp_dir),
            logs_path=str(self.logs_dir),
            raw_data_path=str(self.raw_data_dir),
            processed_data_path=str(self.tmp_dir / 'data' / 'processed'),
            state_path=str(self.tmp_dir / 'state'),
            data_path=str(self.tmp_dir / 'data'),
            figures_path=str(self.tmp_dir / 'figures')
        )
        
        # Reset and set config
        reset_config()
        get_config()  # This will use the default, we'll mock it in tests
        
    def test_synthetic_triggered_no_real_data(self):
        """Test: Synthetic triggered when systematic search finds no real datasets."""
        with patch('data.download.discover_real_datasets') as mock_discover:
            mock_discover.return_value = (None, "No real datasets found")
            
            with patch('data.download.get_config') as mock_config:
                mock_config.return_value = self.config
                
                data_source_type, message, output_path = load_or_generate_data()
                
                assert data_source_type == "synthetic"
                assert "No real data found" in message
                assert output_path.exists()
                
                # Check decision log
                log_path = self.logs_dir / 'data_path_decision.log'
                assert log_path.exists()
                with open(log_path, 'r') as f:
                    log_content = f.read()
                assert "SYNTHETIC TRIGGERED" in log_content
                assert "Systematic search found no real datasets" in log_content
                
                # Check seed file
                seed_path = self.raw_data_dir / 'synthetic_seed.json'
                assert seed_path.exists()
                with open(seed_path, 'r') as f:
                    seed_data = json.load(f)
                assert 'ground_truth' in seed_data

    def test_synthetic_triggered_no_irb(self):
        """Test: Synthetic triggered when real data exists but lacks IRB/Consent."""
        mock_dataset_info = {'type': 'huggingface', 'dataset_id': 'test_dataset'}
        
        with patch('data.download.discover_real_datasets') as mock_discover:
            mock_discover.return_value = (mock_dataset_info, "Found dataset")
            
            with patch('data.download.verify_irb_consent') as mock_verify:
                mock_verify.return_value = (False, "No IRB documentation")
                
                with patch('data.download.get_config') as mock_config:
                    mock_config.return_value = self.config
                    
                    data_source_type, message, output_path = load_or_generate_data()
                    
                    assert data_source_type == "synthetic"
                    assert "Real data found but no IRB/Consent" in message
                    assert output_path.exists()
                    
                    # Check decision log
                    log_path = self.logs_dir / 'data_path_decision.log'
                    with open(log_path, 'r') as f:
                        log_content = f.read()
                    assert "SYNTHETIC TRIGGERED" in log_content
                    assert "IRB/Consent verification failed" in log_content

    def test_real_data_approved(self):
        """Test: Real data used when available with valid IRB/Consent."""
        mock_dataset_info = {'type': 'huggingface', 'dataset_id': 'test_dataset'}
        
        with patch('data.download.discover_real_datasets') as mock_discover:
            mock_discover.return_value = (mock_dataset_info, "Found dataset")
            
            with patch('data.download.verify_irb_consent') as mock_verify:
                mock_verify.return_value = (True, "IRB verified")
                
                with patch('data.download.get_config') as mock_config:
                    mock_config.return_value = self.config
                    
                    with patch('data.download.load_dataset') as mock_load:
                        # Mock a dataset with required columns
                        mock_df = MagicMock()
                        mock_df.to_pandas.return_value = MagicMock(columns=['participant_id', 'avatar_condition', 'pre_self_esteem', 'post_self_esteem', 'comparison_tendency'])
                        mock_load.return_value = mock_df
                        
                        data_source_type, message, output_path = load_or_generate_data()
                        
                        assert data_source_type == "real"
                        assert "Loaded real dataset" in message
                        assert output_path.exists()
                        
                        # Check decision log
                        log_path = self.logs_dir / 'data_path_decision.log'
                        with open(log_path, 'r') as f:
                            log_content = f.read()
                        assert "REAL DATA APPROVED" in log_content

    def test_synthetic_ground_truth_parameters(self):
        """Test: Synthetic data uses correct ground truth parameters."""
        df, message = generate_synthetic_dataset(n_samples=100, seed=42)
        
        assert len(df) == 100
        assert set(df.columns) == {'participant_id', 'avatar_condition', 'pre_self_esteem', 'post_self_esteem', 'comparison_tendency'}
        
        # Check that seed file would be created with correct ground truth
        # (This is tested in the integration with load_or_generate_data)
        
        # Verify avatar_condition is binary
        assert df['avatar_condition'].isin([0, 1]).all()

    def test_decision_log_created(self):
        """Test: Decision log is created and populated correctly."""
        with patch('data.download.discover_real_datasets') as mock_discover:
            mock_discover.return_value = (None, "No real datasets found")
            
            with patch('data.download.get_config') as mock_config:
                mock_config.return_value = self.config
                
                load_or_generate_data()
                
                log_path = self.logs_dir / 'data_path_decision.log'
                assert log_path.exists()
                
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                
                assert len(lines) > 0
                assert any("SYNTHETIC TRIGGERED" in line for line in lines)

    def test_no_synthetic_when_real_available(self):
        """Test: Synthetic is NOT triggered when real data with IRB is available."""
        mock_dataset_info = {'type': 'huggingface', 'dataset_id': 'test_dataset'}
        
        with patch('data.download.discover_real_datasets') as mock_discover:
            mock_discover.return_value = (mock_dataset_info, "Found dataset")
            
            with patch('data.download.verify_irb_consent') as mock_verify:
                mock_verify.return_value = (True, "IRB verified")
                
                with patch('data.download.get_config') as mock_config:
                    mock_config.return_value = self.config
                    
                    with patch('data.download.load_dataset') as mock_load:
                        mock_df = MagicMock()
                        mock_df.to_pandas.return_value = MagicMock(columns=['participant_id', 'avatar_condition', 'pre_self_esteem', 'post_self_esteem', 'comparison_tendency'])
                        mock_load.return_value = mock_df
                        
                        data_source_type, _, _ = load_or_generate_data()
                        
                        assert data_source_type == "real"
                        
                        # Check that synthetic seed file was NOT created
                        seed_path = self.raw_data_dir / 'synthetic_seed.json'
                        assert not seed_path.exists()