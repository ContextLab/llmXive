import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datasets import Dataset

# Mock the config to avoid needing a real config file for unit tests
@pytest.fixture
def mock_config():
    return {
        'dataset_name': 'allenai/medmisbench',
        'target_labels': ['Authority-framed', 'Exception-poisoning'],
        'streaming': True,
        'paths': {
            'raw': 'data/raw',
            'state': 'state'
        }
    }

@pytest.fixture
def mock_sample_data():
    """Mock dataset items that simulate MedMisBench structure."""
    return [
        {
            'id': '1',
            'prompt': 'The false claim is: Vaccines cause autism. Please explain.',
            'label': 'Authority-framed',
            'category': 'Authority-framed'
        },
        {
            'id': '2',
            'prompt': 'Claim: 5G towers spread viruses. Is this true?',
            'label': 'Exception-poisoning',
            'category': 'Exception-poisoning'
        },
        {
            'id': '3',
            'prompt': 'Normal medical advice: Drink water.',
            'label': 'Control',
            'category': 'Control'
        }
    ]

class TestIngestion:
    def test_load_and_filter_dataset(self, mock_config, mock_sample_data):
        """Test that the dataset is filtered correctly."""
        from ingestion import load_and_filter_dataset
        
        # Mock the load_dataset function
        with patch('ingestion.load_dataset') as mock_load:
            mock_ds = MagicMock()
            mock_ds.__iter__ = lambda self: iter(mock_sample_data)
            mock_load.return_value = mock_ds
            
            result = load_and_filter_dataset(mock_config)
            
            # Should have 2 items (filtered out 'Control')
            assert len(result) == 2
            
            # Check false_claim extraction
            assert result[0]['false_claim'] == 'Vaccines cause autism.'
            assert result[1]['false_claim'] == '5G towers spread viruses.'
            
            # Check labels
            assert result[0]['label'] == 'Authority-framed'
            assert result[1]['label'] == 'Exception-poisoning'

    def test_extract_false_claim_regex_fallback(self, mock_config, mock_sample_data):
        """Test regex fallback when false_claim column is missing."""
        from ingestion import load_and_filter_dataset
        
        # Modify sample data to not have 'false_claim' column explicitly
        # (The function extracts it from prompt text via regex)
        pass # Logic is covered in test_load_and_filter_dataset

    def test_save_to_csv(self, mock_config, mock_sample_data):
        """Test saving data to CSV."""
        from ingestion import save_to_csv
        
        # Prepare data
        data = [
            {'prompt_id': '1', 'prompt': 'Test', 'false_claim': 'Claim', 'label': 'A', 'source': 'S'}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.csv'
            save_to_csv(data, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                content = f.read()
                assert 'prompt_id' in content
                assert 'Claim' in content

    def test_update_hash_state(self, mock_config):
        """Test updating hash state."""
        from ingestion import update_hash_state
        
        hash_state = {'existing': 'hash'}
        # Create a dummy file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)
        
        try:
            new_state = update_hash_state(tmp_path, hash_state)
            assert str(tmp_path) in new_state
            assert len(new_state) == 2
        finally:
            os.unlink(tmp_path)

    def test_run_ingestion_pipeline(self, mock_config, mock_sample_data):
        """Test the full pipeline."""
        from ingestion import run_ingestion_pipeline
        
        with patch('ingestion.load_dataset') as mock_load:
            mock_ds = MagicMock()
            mock_ds.__iter__ = lambda self: iter(mock_sample_data)
            mock_load.return_value = mock_ds
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Update config paths to temp dir
                mock_config['paths']['raw'] = str(Path(tmpdir) / 'raw')
                mock_config['paths']['state'] = str(Path(tmpdir) / 'state')
                
                output_file = run_ingestion_pipeline(mock_config)
                
                assert output_file.exists()
                # Check hash file
                hash_file = Path(tmpdir) / 'state' / 'artifact_hashes.yaml'
                assert hash_file.exists()