import pytest
from click.testing import CliRunner
from src.cli.run_analysis import cli, run_phase, REGIONAL_DOMAIN, validate_phase_bounds
import os
import tempfile
import yaml

def test_cli_invocation():
    """Test that the CLI can be invoked without errors."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert '--phases' in result.output
    assert '--config' in result.output

def test_run_phase_valid():
    """Test that a valid phase runs without raising exceptions."""
    # Create a minimal mock config
    config = {
        'data_path': '/tmp/data',
        'output_path': '/tmp/output',
        'region': REGIONAL_DOMAIN
    }
    
    # Phase 0 (Validate Structure) should not raise
    try:
        run_phase(0, config)
    except Exception as e:
        pytest.fail(f"run_phase(0) raised unexpected exception: {e}")

def test_regional_domain_constraint():
    """Verify that the REGIONAL_DOMAIN constant matches the spec (20N-60N, 100E-60W)."""
    assert REGIONAL_DOMAIN['lat_min'] == 20.0
    assert REGIONAL_DOMAIN['lat_max'] == 60.0
    assert REGIONAL_DOMAIN['lon_min'] == 100.0
    assert REGIONAL_DOMAIN['lon_max'] == -60.0

def test_cli_run_command():
    """Test running the CLI with a single phase."""
    runner = CliRunner()
    # Use a temp file for config to avoid file not found errors
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'data_path': '/tmp/data',
            'output_path': '/tmp/output',
            'region': REGIONAL_DOMAIN
        }, f)
        config_path = f.name
    
    try:
        result = runner.invoke(cli, ['--phases', '0', '--config', config_path])
        assert result.exit_code == 0
    finally:
        os.unlink(config_path)

def test_cli_run_command_range():
    """Test running the CLI with a phase range."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'data_path': '/tmp/data',
            'output_path': '/tmp/output',
            'region': REGIONAL_DOMAIN
        }, f)
        config_path = f.name
    
    try:
        # Test range 0-1
        result = runner.invoke(cli, ['--phases', '0-1', '--config', config_path])
        assert result.exit_code == 0
    finally:
        os.unlink(config_path)

def test_cli_validate_phase_bounds():
    """Test validation of phase bounds."""
    # Valid
    assert validate_phase_bounds([0, 5, 9]) is True
    
    # Invalid
    with pytest.raises(ValueError):
        validate_phase_bounds([10])
    
    with pytest.raises(ValueError):
        validate_phase_bounds([-1])

def test_cli_invalid_phase_format():
    """Test CLI handling of invalid phase format."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'data_path': '/tmp/data',
            'output_path': '/tmp/output',
            'region': REGIONAL_DOMAIN
        }, f)
        config_path = f.name
    
    try:
        result = runner.invoke(cli, ['--phases', 'invalid', '--config', config_path])
        assert result.exit_code != 0
        assert "Invalid phase format" in result.output
    finally:
        os.unlink(config_path)