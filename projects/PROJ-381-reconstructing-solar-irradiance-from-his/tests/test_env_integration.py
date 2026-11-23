"""
Integration tests for environment variable management.

These tests ensure that the environment setup works end-to-end
when used by other modules in the project.
"""

import os
import pytest
from pathlib import Path
import tempfile
import shutil

from code import env_manager

@pytest.fixture
def setup_env_integration():
    """Setup a temporary project environment."""
    temp_dir = tempfile.mkdtemp()
    
    # Create structure
    code_dir = Path(temp_dir) / "code"
    code_dir.mkdir()
    data_dir = Path(temp_dir) / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (code_dir / "models").mkdir()
    (code_dir / "analysis").mkdir()
    (code_dir / "models" / "artifacts").mkdir()
    (data_dir / "figures").mkdir()
    
    # Create .env
    env_content = f"""
    DATA_ROOT_PATH={data_dir}
    DATA_RAW_PATH={data_dir / 'raw'}
    DATA_PROCESSED_PATH={data_dir / 'processed'}
    MODEL_ARTIFACTS_PATH={code_dir / 'models' / 'artifacts'}
    DATA_FIGURES_PATH={data_dir / 'figures'}
    """
    (code_dir / ".env").write_text(env_content)
    (code_dir / "__init__.py").write_text("")
    
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_setup_environment_integration(setup_env_integration):
    """Test the full setup_environment flow."""
    original_cwd = os.getcwd()
    try:
        os.chdir(setup_env_integration)
        env_manager._PROJECT_ROOT = None
        
        config = env_manager.setup_environment()
        
        # Check that config contains expected keys
        assert "project_root" in config
        assert "data_root" in config
        assert "data_raw" in config
        assert "data_processed" in config
        assert "model_artifacts" in config
        assert "data_figures" in config
        assert "silso_url" in config
        assert "sorce_url" in config
        assert "paths_valid" in config
        
        # Check that paths are correct
        assert config["data_root"] == Path(setup_env_integration) / "data"
        assert config["data_raw"] == Path(setup_env_integration) / "data" / "raw"
        assert config["paths_valid"]["data_root"] is True
    finally:
        os.chdir(original_cwd)
