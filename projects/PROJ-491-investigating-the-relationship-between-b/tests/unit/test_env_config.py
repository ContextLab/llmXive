"""
Unit tests for OpenNeuro environment configuration management.
"""

import os
import tempfile
from pathlib import Path
import pytest

from code.env_config import OpenNeuroConfig, get_openneuro_config


class TestOpenNeuroConfig:
    """Test cases for OpenNeuroConfig class."""

    def test_initialization_without_credentials(self):
        """Test initialization when no credentials are set."""
        # Clear environment variables for this test
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('')
            
            config = OpenNeuroConfig(env_file)
            
            assert config.username is None
            assert config.password is None
            assert config.api_key is None
            assert not config.is_configured()

    def test_initialization_with_credentials(self):
        """Test initialization with credentials in .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                'OPENNEURO_USERNAME=testuser\n'
                'OPENNEURO_PASSWORD=testpass\n'
                'OPENNEURO_API_KEY=testkey\n'
            )
            
            config = OpenNeuroConfig(env_file)
            
            assert config.username == 'testuser'
            assert config.password == 'testpass'
            assert config.api_key == 'testkey'
            assert config.is_configured()

    def test_validate_credentials_partial(self):
        """Test validation when only some credentials are set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('OPENNEURO_USERNAME=testuser\n')
            
            config = OpenNeuroConfig(env_file)
            
            validation = config.validate_credentials()
            assert validation['username'] is True
            assert validation['password'] is False
            assert validation['api_key'] is False

    def test_validate_credentials_full(self):
        """Test validation when all credentials are set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                'OPENNEURO_USERNAME=testuser\n'
                'OPENNEURO_PASSWORD=testpass\n'
                'OPENNEURO_API_KEY=testkey\n'
            )
            
            config = OpenNeuroConfig(env_file)
            
            validation = config.validate_credentials()
            assert all(validation.values())

    def test_get_credentials(self):
        """Test retrieving all credentials as a dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                'OPENNEURO_USERNAME=testuser\n'
                'OPENNEURO_PASSWORD=testpass\n'
                'OPENNEURO_API_KEY=testkey\n'
            )
            
            config = OpenNeuroConfig(env_file)
            creds = config.get_credentials()
            
            assert creds['openneuro_username'] == 'testuser'
            assert creds['openneuro_password'] == 'testpass'
            assert creds['openneuro_api_key'] == 'testkey'

    def test_repr_masks_credentials(self):
        """Test that string representation masks sensitive values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                'OPENNEURO_USERNAME=testuser\n'
                'OPENNEURO_PASSWORD=testpass\n'
                'OPENNEURO_API_KEY=testkey\n'
            )
            
            config = OpenNeuroConfig(env_file)
            repr_str = repr(config)
            
            assert 'testuser' not in repr_str
            assert 'testpass' not in repr_str
            assert 'testkey' not in repr_str
            assert '***' in repr_str

    def test_factory_function(self):
        """Test the factory function get_openneuro_config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('OPENNEURO_USERNAME=factorytest\n')
            
            config = get_openneuro_config(env_file)
            
            assert isinstance(config, OpenNeuroConfig)
            assert config.username == 'factorytest'


class TestEnvFileLoading:
    """Test cases for .env file loading behavior."""

    def test_nonexistent_env_file(self):
        """Test behavior when .env file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / 'nonexistent.env'
            
            # Should not raise an error, just load empty config
            config = OpenNeuroConfig(env_file)
            assert not config.is_configured()

    def test_empty_env_file(self):
        """Test behavior with an empty .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('')
            
            config = OpenNeuroConfig(env_file)
            assert not config.is_configured()

    def test_comments_in_env_file(self):
        """Test that comments in .env file are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            env_file.write_text(
                '# This is a comment\n'
                'OPENNEURO_USERNAME=testuser\n'
                '# Another comment\n'
                'OPENNEURO_PASSWORD=testpass\n'
            )
            
            config = OpenNeuroConfig(env_file)
            assert config.username == 'testuser'
            assert config.password == 'testpass'
            assert config.api_key is None