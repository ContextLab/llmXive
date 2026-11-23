"""
Integration tests for the configuration manager (T004).
Tests the full configuration loading flow with realistic scenarios.
"""

import pytest
import yaml
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from orchestrator.config import ConfigManager, ConfigError


class TestConfigIntegration:
    """Integration tests for ConfigManager with realistic configurations."""

    @pytest.fixture
    def full_project_config(self):
        """Create a full project configuration similar to the actual one."""
        return {
            'nodes': [
                {'id': 'node_001', 'host': '192.168.1.101', 'cpu_cores': 4, 'ram_gb': 8, 'role': 'worker'},
                {'id': 'node_002', 'host': '192.168.1.102', 'cpu_cores': 8, 'ram_gb': 16, 'role': 'worker'},
                {'id': 'node_003', 'host': '192.168.1.103', 'cpu_cores': 4, 'ram_gb': 8, 'role': 'worker'},
                {'id': 'orchestrator', 'host': '192.168.1.100', 'cpu_cores': 8, 'ram_gb': 32, 'role': 'master'}
            ],
            'granularity': {
                'fine': 1000,
                'medium': 10000,
                'coarse': 100000
            },
            'ci_timeout': {'seconds': 21600},
            'pipeline_timeout': {'seconds': 18000},
            'node_count_range': {'min': 3, 'max': 10, 'step': 1},
            'ssh': {
                'timeout': 30,
                'retry_attempts': 3,
                'retry_delay': 5,
                'port': 22,
                'username': 'runner'
            },
            'network_impairments': {
                'enabled': True,
                'default_latency_ms': 10,
                'default_packet_loss_pct': 0.1,
                'max_packet_loss_threshold': 20
            },
            'simulation': {
                'calibration_tolerance': 0.05,
                'max_iterations': 1000,
                'random_seed': 42
            },
            'experiment': {
                'name': 'mesh_supercomputer_baseline',
                'version': '1.0.0',
                'description': 'Baseline experiment'
            },
            'paths': {
                'raw_data': 'code/data/raw',
                'processed_data': 'code/data/processed',
                'figures': 'figures',
                'logs': 'code/logs'
            }
        }

    @pytest.fixture
    def temp_full_config_file(self, full_project_config):
        """Create a temporary file with full configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(full_project_config, f)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_full_config_load(self, temp_full_config_file):
        """Test loading a complete project configuration."""
        config = ConfigManager(temp_full_config_file)
        
        # Verify all sections load correctly
        nodes = config.get_nodes()
        assert len(nodes) == 4
        
        granularity = config.get_granularity_settings()
        assert granularity['fine'] == 1000
        assert granularity['medium'] == 10000
        assert granularity['coarse'] == 100000
        
        assert config.get_ci_timeout() == 21600
        assert config.get_pipeline_timeout() == 18000
        
        node_range = config.get_node_count_range()
        assert node_range['min'] == 3
        assert node_range['max'] == 10
        assert node_range['step'] == 1

    def test_ssh_config_access(self, temp_full_config_file):
        """Test accessing SSH configuration."""
        config = ConfigManager(temp_full_config_file)
        ssh_config = config.get_ssh_config()
        
        assert ssh_config['timeout'] == 30
        assert ssh_config['retry_attempts'] == 3
        assert ssh_config['port'] == 22
        assert ssh_config['username'] == 'runner'

    def test_network_impairment_config(self, temp_full_config_file):
        """Test accessing network impairment configuration."""
        config = ConfigManager(temp_full_config_file)
        net_config = config.get_network_impairment_config()
        
        assert net_config['enabled'] is True
        assert net_config['default_latency_ms'] == 10
        assert net_config['max_packet_loss_threshold'] == 20

    def test_simulation_config(self, temp_full_config_file):
        """Test accessing simulation configuration."""
        config = ConfigManager(temp_full_config_file)
        sim_config = config.get_simulation_config()
        
        assert sim_config['calibration_tolerance'] == 0.05
        assert sim_config['max_iterations'] == 1000
        assert sim_config['random_seed'] == 42

    def test_experiment_metadata(self, temp_full_config_file):
        """Test accessing experiment metadata."""
        config = ConfigManager(temp_full_config_file)
        exp_config = config.get_experiment_config()
        
        assert exp_config['name'] == 'mesh_supercomputer_baseline'
        assert exp_config['version'] == '1.0.0'

    def test_all_paths_configured(self, temp_full_config_file):
        """Test that all data paths are properly configured."""
        config = ConfigManager(temp_full_config_file)
        
        assert str(config.get_raw_data_path()) == 'code/data/raw'
        assert str(config.get_processed_data_path()) == 'code/data/processed'
        assert str(config.get_figures_path()) == 'figures'

    def test_node_attributes(self, temp_full_config_file):
        """Test that nodes have all expected attributes."""
        config = ConfigManager(temp_full_config_file)
        nodes = config.get_nodes()
        
        for node in nodes:
            assert 'id' in node
            assert 'host' in node
            assert 'cpu_cores' in node
            assert 'ram_gb' in node
            assert 'role' in node

    def test_multiple_config_instances(self):
        """Test that multiple config instances can be created independently."""
        config1_dict = {
            'nodes': [{'id': 'node_1', 'host': '192.168.1.1'}],
            'granularity': {'fine': 100, 'medium': 1000, 'coarse': 10000},
            'ci_timeout': {'seconds': 1000},
            'pipeline_timeout': {'seconds': 500}
        }
        
        config2_dict = {
            'nodes': [{'id': 'node_2', 'host': '192.168.1.2'}],
            'granularity': {'fine': 200, 'medium': 2000, 'coarse': 20000},
            'ci_timeout': {'seconds': 2000},
            'pipeline_timeout': {'seconds': 1000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f1:
            yaml.dump(config1_dict, f1)
            path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f2:
            yaml.dump(config2_dict, f2)
            path2 = f2.name
        
        try:
            config1 = ConfigManager(path1)
            config2 = ConfigManager(path2)
            
            # Verify they are independent
            assert config1.get_granularity_settings()['fine'] == 100
            assert config2.get_granularity_settings()['fine'] == 200
            assert config1.get_ci_timeout() == 1000
            assert config2.get_ci_timeout() == 2000
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_config_with_minimal_nodes(self):
        """Test configuration with minimal node setup."""
        config_dict = {
            'nodes': [{'id': 'single_node', 'host': 'localhost'}],
            'granularity': {'fine': 100, 'medium': 1000, 'coarse': 10000},
            'ci_timeout': {'seconds': 3600},
            'pipeline_timeout': {'seconds': 1800}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            config = ConfigManager(temp_path)
            nodes = config.get_nodes()
            assert len(nodes) == 1
            assert nodes[0]['id'] == 'single_node'
        finally:
            os.unlink(temp_path)