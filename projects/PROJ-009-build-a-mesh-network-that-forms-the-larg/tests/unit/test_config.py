"""
Unit tests for the configuration manager (T004).
"""

import pytest
import yaml
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from orchestrator.config import ConfigManager, ConfigError, load_config


class TestConfigManager:
    """Test suite for ConfigManager class."""

    @pytest.fixture
    def valid_config_dict(self):
        """Create a valid configuration dictionary."""
        return {
            'nodes': [
                {'id': 'node_001', 'host': '192.168.1.101'},
                {'id': 'node_002', 'host': '192.168.1.102'}
            ],
            'granularity': {
                'fine': 1000,
                'medium': 10000,
                'coarse': 100000
            },
            'ci_timeout': {'seconds': 21600},
            'pipeline_timeout': {'seconds': 18000},
            'node_count_range': {'min': 3, 'max': 10, 'step': 1},
            'paths': {
                'raw_data': 'code/data/raw',
                'processed_data': 'code/data/processed',
                'figures': 'figures'
            }
        }

    @pytest.fixture
    def temp_config_file(self, valid_config_dict):
        """Create a temporary YAML config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_config_dict, f)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid configuration file."""
        config = ConfigManager(temp_config_file)
        assert config.get_nodes() is not None
        assert len(config.get_nodes()) == 2
        assert config.get_granularity_settings()['fine'] == 1000
        assert config.get_ci_timeout() == 21600

    def test_get_nodes(self, temp_config_file):
        """Test retrieving node list."""
        config = ConfigManager(temp_config_file)
        nodes = config.get_nodes()
        
        assert len(nodes) == 2
        assert nodes[0]['id'] == 'node_001'
        assert nodes[0]['host'] == '192.168.1.101'
        assert nodes[1]['id'] == 'node_002'
        assert nodes[1]['host'] == '192.168.1.102'

    def test_get_granularity_settings(self, temp_config_file):
        """Test retrieving granularity settings."""
        config = ConfigManager(temp_config_file)
        settings = config.get_granularity_settings()
        
        assert settings['fine'] == 1000
        assert settings['medium'] == 10000
        assert settings['coarse'] == 100000

    def test_get_ci_timeout(self, temp_config_file):
        """Test retrieving CI timeout."""
        config = ConfigManager(temp_config_file)
        assert config.get_ci_timeout() == 21600

    def test_get_pipeline_timeout(self, temp_config_file):
        """Test retrieving pipeline timeout."""
        config = ConfigManager(temp_config_file)
        assert config.get_pipeline_timeout() == 18000

    def test_get_node_count_range(self, temp_config_file):
        """Test retrieving node count range."""
        config = ConfigManager(temp_config_file)
        node_range = config.get_node_count_range()
        
        assert node_range['min'] == 3
        assert node_range['max'] == 10
        assert node_range['step'] == 1

    def test_get_raw_data_path(self, temp_config_file):
        """Test retrieving raw data path."""
        config = ConfigManager(temp_config_file)
        path = config.get_raw_data_path()
        assert str(path) == 'code/data/raw'

    def test_get_processed_data_path(self, temp_config_file):
        """Test retrieving processed data path."""
        config = ConfigManager(temp_config_file)
        path = config.get_processed_data_path()
        assert str(path) == 'code/data/processed'

    def test_get_figures_path(self, temp_config_file):
        """Test retrieving figures path."""
        config = ConfigManager(temp_config_file)
        path = config.get_figures_path()
        assert str(path) == 'figures'

    def test_missing_config_file(self):
        """Test that missing config file raises ConfigError."""
        with pytest.raises(ConfigError, match="Configuration file not found"):
            ConfigManager("nonexistent/config.yaml")

    def test_invalid_yaml(self):
        """Test that invalid YAML raises ConfigError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="Failed to parse YAML"):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_nodes(self):
        """Test that missing nodes section raises ConfigError."""
        config_dict = {
            'granularity': {'fine': 1000, 'medium': 10000, 'coarse': 100000},
            'ci_timeout': {'seconds': 21600},
            'pipeline_timeout': {'seconds': 18000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="No nodes configured"):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)

    def test_node_missing_id(self):
        """Test that node without id raises ConfigError."""
        config_dict = {
            'nodes': [{'host': '192.168.1.101'}],
            'granularity': {'fine': 1000, 'medium': 10000, 'coarse': 100000},
            'ci_timeout': {'seconds': 21600},
            'pipeline_timeout': {'seconds': 18000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="missing required 'id'"):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)

    def test_node_missing_host(self):
        """Test that node without host raises ConfigError."""
        config_dict = {
            'nodes': [{'id': 'node_001'}],
            'granularity': {'fine': 1000, 'medium': 10000, 'coarse': 100000},
            'ci_timeout': {'seconds': 21600},
            'pipeline_timeout': {'seconds': 18000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="missing required"):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_granularity(self):
        """Test that missing granularity settings raise ConfigError."""
        config_dict = {
            'nodes': [{'id': 'node_001', 'host': '192.168.1.101'}],
            'ci_timeout': {'seconds': 21600},
            'pipeline_timeout': {'seconds': 18000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="Missing required granularity setting"):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)

    def test_invalid_granularity_value(self):
        """Test that invalid granularity value raises ConfigError."""
        config_dict = {
            'nodes': [{'id': 'node_001', 'host': '192.168.1.101'}],
            'granularity': {'fine': -1000, 'medium': 10000, 'coarse': 100000},
            'ci_timeout': {'seconds': 21600},
            'pipeline_timeout': {'seconds': 18000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="must be a positive integer"):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_ci_timeout(self):
        """Test that missing CI timeout raises ConfigError."""
        config_dict = {
            'nodes': [{'id': 'node_001', 'host': '192.168.1.101'}],
            'granularity': {'fine': 1000, 'medium': 10000, 'coarse': 100000},
            'pipeline_timeout': {'seconds': 18000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="Missing 'ci_timeout.seconds'"):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)

    def test_invalid_ci_timeout(self):
        """Test that invalid CI timeout raises ConfigError."""
        config_dict = {
            'nodes': [{'id': 'node_001', 'host': '192.168.1.101'}],
            'granularity': {'fine': 1000, 'medium': 10000, 'coarse': 100000},
            'ci_timeout': {'seconds': -100},
            'pipeline_timeout': {'seconds': 18000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="must be a positive number"):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_pipeline_timeout(self):
        """Test that missing pipeline timeout raises ConfigError."""
        config_dict = {
            'nodes': [{'id': 'node_001', 'host': '192.168.1.101'}],
            'granularity': {'fine': 1000, 'medium': 10000, 'coarse': 100000},
            'ci_timeout': {'seconds': 21600}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="Missing 'pipeline_timeout.seconds'"):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_config_function(self, temp_config_file):
        """Test the load_config convenience function."""
        config = load_config(temp_config_file)
        assert isinstance(config, ConfigManager)
        assert len(config.get_nodes()) == 2
