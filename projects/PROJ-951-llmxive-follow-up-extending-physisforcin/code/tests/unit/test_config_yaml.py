import os
import tempfile
import pytest
import yaml
from pathlib import Path
from src.training.config import (
    Config,
    load_config,
    save_config,
    validate_config_schema,
    create_default_config
)


class TestConfigYAML:
    """Tests for config.yaml schema validation and loading."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config.yaml file with valid schema."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'project': {
                    'name': 'test-project',
                    'version': '1.0.0',
                    'root_dir': '/tmp/test',
                    'data_root': 'data'
                },
                'environment': {
                    'force_cpu': True,
                    'seed': 42,
                    'max_memory_mb': 6144
                },
                'data': {
                    'raw_dir': 'data/raw',
                    'curated_dir': 'data/curated',
                    'eval_dir': 'data/eval',
                    'validation_dir': 'data/validation',
                    'control_dir': 'data/control',
                    'prompts_file': 'data/prompts.jsonl'
                },
                'generation': {
                    'model_id': 'Wan-AI/Wan2.1-Turbo',
                    'max_frames': 16,
                    'resolution': '256x256',
                    'offload_enabled': False,
                    'offload_target': 'kaggle'
                },
                'filtering': {
                    'schema_file': 'src/filtering/schema.py',
                    'engine': 'pybullet',
                    'headless': True,
                    'time_step': 0.016,
                    'filter_discard_percent': None  # Explicitly null as per spec
                },
                'training': {
                    'model_type': 'unet_diffusion',
                    'base_channels': 64,
                    'down_blocks': 4,
                    'up_blocks': 4,
                    'attention_heads': 8,
                    'batch_size': 4,
                    'learning_rate': 0.0001,
                    'num_epochs': 10,
                    'timeout_hours': 4,
                    'abort_on_nan': True
                },
                'evaluation': {
                    'r_bench_enabled': True,
                    'pai_bench_enabled': True,
                    'significance_level': 0.05,
                    'eval_sample_size': 30,
                    'orthogonality_threshold': 0.95
                },
                'logging': {
                    'level': 'INFO',
                    'format': 'json',
                    'log_dir': 'logs',
                    'metrics_file': 'metrics.jsonl',
                    'discard_rate_log': 'logs/discard_rate.log',
                    'orthogonality_log': 'logs/orthogonality_gate.log',
                    'baseline_log': 'logs/baseline_verification.log',
                    'dataset_validation_log': 'logs/dataset_validation.log'
                },
                'augmentation': {
                    'enabled': True,
                    'min_curated_size': 30,
                    'temporal_jitter_percent': 10,
                    'geometric_flip': True
                }
            }
            yaml.dump(config_data, f)
            f.flush()
            yield f.name
            os.unlink(f.name)

    def test_load_config_valid_file(self, temp_config_file):
        """Test that a valid config.yaml can be loaded."""
        config = load_config(temp_config_file)
        assert config is not None
        assert config['project']['name'] == 'test-project'
        assert config['filtering']['filter_discard_percent'] is None

    def test_filter_discard_percent_null(self, temp_config_file):
        """Test that filter_discard_percent is explicitly null in the loaded config."""
        config = load_config(temp_config_file)
        assert 'filter_discard_percent' in config['filtering']
        assert config['filtering']['filter_discard_percent'] is None

    def test_validate_config_schema(self, temp_config_file):
        """Test schema validation against the loaded config."""
        config = load_config(temp_config_file)
        is_valid, errors = validate_config_schema(config)
        assert is_valid
        assert len(errors) == 0

    def test_missing_required_key(self, temp_config_file):
        """Test validation fails when a required key is missing."""
        with open(temp_config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Remove a required key
        del data['filtering']['filter_discard_percent']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(data, f)
            f.flush()
            temp_missing = f.name
        
        try:
            config = load_config(temp_missing)
            is_valid, errors = validate_config_schema(config)
            assert not is_valid
            assert any('filter_discard_percent' in str(e) for e in errors)
        finally:
            os.unlink(temp_missing)

    def test_invalid_discard_percent_type(self, temp_config_file):
        """Test validation fails when discard_percent is not a number or null."""
        with open(temp_config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        data['filtering']['filter_discard_percent'] = "invalid"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(data, f)
            f.flush()
            temp_invalid = f.name
        
        try:
            config = load_config(temp_invalid)
            is_valid, errors = validate_config_schema(config)
            assert not is_valid
            assert any('filter_discard_percent' in str(e) for e in errors)
        finally:
            os.unlink(temp_invalid)

    def test_save_and_reload_config(self, temp_config_file):
        """Test that a config can be saved and reloaded correctly."""
        config = load_config(temp_config_file)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_out = f.name
        
        try:
            save_config(config, temp_out)
            reloaded = load_config(temp_out)
            
            assert reloaded['project']['name'] == config['project']['name']
            assert reloaded['filtering']['filter_discard_percent'] == config['filtering']['filter_discard_percent']
        finally:
            os.unlink(temp_out)

    def test_default_config_structure(self):
        """Test that create_default_config produces a valid schema."""
        default_cfg = create_default_config()
        is_valid, errors = validate_config_schema(default_cfg)
        assert is_valid
        assert len(errors) == 0
        assert default_cfg['filtering']['filter_discard_percent'] is None