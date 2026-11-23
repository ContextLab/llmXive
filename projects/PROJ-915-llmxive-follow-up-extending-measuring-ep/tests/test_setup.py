import os
import pytest
from pathlib import Path

def test_project_structure_exists():
    """
    Verify that the required project directories exist.
    This validates T001 and T004.
    """
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/interim",
        "data/results",
        "code",
        "tests",
        "figures",
        "state",
        "docs"
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"{dir_path} is not a directory."

def test_linting_config_exists():
    """
    Verify that linting configuration files exist.
    This validates T003.
    """
    project_root = Path(__file__).parent.parent
    
    # Check for pyproject.toml with black/ruff config
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml does not exist."
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml."
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml."

def test_error_handling_module_imports():
    """
    Verify that error_handling module can be imported and has required names.
    This validates T008.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from error_handling import (
        InferenceTimeoutError,
        DatasetDownloadError,
        RetryExhaustedError,
        retry_with_backoff,
        timeout_context,
        enforce_inference_timeout,
        safe_download_with_retry,
        compute_sha256,
        update_hash_state
    )
    
    assert InferenceTimeoutError is not None
    assert DatasetDownloadError is not None
    assert RetryExhaustedError is not None
    assert callable(retry_with_backoff)
    assert callable(timeout_context)
    assert callable(enforce_inference_timeout)
    assert callable(safe_download_with_retry)
    assert callable(compute_sha256)
    assert callable(update_hash_state)

def test_secrets_manager_imports():
    """
    Verify that secrets_manager module can be imported.
    This validates T009.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from secrets_manager import (
        load_env_file,
        get_secret,
        validate_secrets,
        get_hf_token,
        get_prolific_api_key,
        SecretsManager,
        init_secrets
    )
    
    assert SecretsManager is not None
    assert callable(load_env_file)
    assert callable(get_secret)
    assert callable(validate_secrets)
    assert callable(get_hf_token)
    assert callable(get_prolific_api_key)
    assert callable(init_secrets)