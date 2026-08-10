"""
Unit tests for T002: Conda Environment Initialization.

These tests verify that the environment.yml file is syntactically valid
and contains the required packages defined in the task specification.
"""
import os
import yaml
import pytest
from pathlib import Path

# Path to the environment file relative to the project root
ENV_FILE_PATH = Path(__file__).parent.parent.parent / "environment.yml"

@pytest.fixture
def env_config():
    """Load the environment.yml file."""
    if not ENV_FILE_PATH.exists():
        pytest.skip(f"environment.yml not found at {ENV_FILE_PATH}. "
                    "This test must run after T002 creates the file.")
    
    with open(ENV_FILE_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_env_file_exists():
    """Verify environment.yml exists in the project root."""
    assert ENV_FILE_PATH.exists(), "environment.yml must exist at project root"

def test_env_name(env_config):
    """Verify the environment has the correct name."""
    assert env_config.get('name') == 'yeast-cre-analysis', \
        "Environment name must be 'yeast-cre-analysis'"

def test_required_channels(env_config):
    """Verify required conda channels are present."""
    channels = env_config.get('channels', [])
    required_channels = ['conda-forge', 'bioconda', 'defaults']
    
    for channel in required_channels:
        assert channel in channels, f"Required channel '{channel}' missing from channels list"

def test_required_tools_present(env_config):
    """Verify required bioinformatics tools are in dependencies."""
    deps = env_config.get('dependencies', [])
    # Filter out pip section for this check
    conda_deps = [d for d in deps if isinstance(d, str)]
    
    required_tools = {
        'fastp': 'Adapter trimming',
        'bowtie2': 'Alignment',
        'macs3': 'Peak calling (MACS2)',
        'r-base': 'R environment',
        'python': 'Python environment'
    }
    
    for tool, description in required_tools.items():
        # Check if tool is in conda deps
        found = any(tool in d for d in conda_deps)
        assert found, f"Required tool '{tool}' ({description}) not found in dependencies"

def test_python_version(env_config):
    """Verify Python version is pinned to a compatible version."""
    deps = env_config.get('dependencies', [])
    python_dep = next((d for d in deps if isinstance(d, str) and d.startswith('python')), None)
    
    assert python_dep is not None, "Python version must be specified"
    assert '3.10' in python_dep or '3.9' in python_dep or '3.11' in python_dep, \
        f"Python version {python_dep} is not within supported range (3.9-3.11)"

def test_r_packages_present(env_config):
    """Verify required R packages are present (either in conda or pip)."""
    deps = env_config.get('dependencies', [])
    
    # Check both conda and pip sections
    all_deps = []
    for d in deps:
        if isinstance(d, str):
            all_deps.append(d)
        elif isinstance(d, dict) and 'pip' in d:
            all_deps.extend(d['pip'])
    
    required_r_packages = ['ggplot2', 'dplyr', 'lme4', 'glmmTMB']
    
    for pkg in required_r_packages:
        found = any(pkg in d for d in all_deps)
        assert found, f"Required R package '{pkg}' not found in dependencies"

def test_yaml_syntax_valid(env_config):
    """Verify the YAML file is syntactically valid."""
    # If we got here, yaml.safe_load succeeded, so this is implicitly true
    # but we assert the structure is correct
    assert 'name' in env_config, "Missing 'name' key"
    assert 'channels' in env_config, "Missing 'channels' key"
    assert 'dependencies' in env_config, "Missing 'dependencies' key"
    assert isinstance(env_config['dependencies'], list), "Dependencies must be a list"