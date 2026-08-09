import os
from pathlib import Path
import pytest

PROJECT_NAME = "PROJ-328-predicting-the-impact-of-composition-on-"
BASE_PATH = Path("projects") / PROJECT_NAME

def test_project_root_exists():
    """Verify the project root directory exists."""
    assert BASE_PATH.exists(), f"Project root {BASE_PATH} does not exist"
    assert BASE_PATH.is_dir(), f"{BASE_PATH} is not a directory"

def test_data_directory_exists():
    """Verify the data directory structure exists."""
    data_dir = BASE_PATH / "data"
    assert data_dir.exists(), f"Data directory {data_dir} does not exist"
    assert data_dir.is_dir(), f"{data_dir} is not a directory"

def test_data_raw_directory_exists():
    """Verify the raw data subdirectory exists."""
    raw_dir = BASE_PATH / "data" / "raw"
    assert raw_dir.exists(), f"Raw data directory {raw_dir} does not exist"
    assert raw_dir.is_dir(), f"{raw_dir} is not a directory"

def test_data_processed_directory_exists():
    """Verify the processed data subdirectory exists."""
    processed_dir = BASE_PATH / "data" / "processed"
    assert processed_dir.exists(), f"Processed data directory {processed_dir} does not exist"
    assert processed_dir.is_dir(), f"{processed_dir} is not a directory"

def test_data_outputs_directory_exists():
    """Verify the outputs data subdirectory exists."""
    outputs_dir = BASE_PATH / "data" / "outputs"
    assert outputs_dir.exists(), f"Outputs data directory {outputs_dir} does not exist"
    assert outputs_dir.is_dir(), f"{outputs_dir} is not a directory"

def test_data_config_directory_exists():
    """Verify the config data subdirectory exists."""
    config_dir = BASE_PATH / "data" / "config"
    assert config_dir.exists(), f"Config data directory {config_dir} does not exist"
    assert config_dir.is_dir(), f"{config_dir} is not a directory"

def test_code_directory_exists():
    """Verify the code directory exists."""
    code_dir = BASE_PATH / "code"
    assert code_dir.exists(), f"Code directory {code_dir} does not exist"
    assert code_dir.is_dir(), f"{code_dir} is not a directory"

def test_code_ingestion_directory_exists():
    """Verify the ingestion code subdirectory exists."""
    ingestion_dir = BASE_PATH / "code" / "ingestion"
    assert ingestion_dir.exists(), f"Ingestion code directory {ingestion_dir} does not exist"
    assert ingestion_dir.is_dir(), f"{ingestion_dir} is not a directory"

def test_code_features_directory_exists():
    """Verify the features code subdirectory exists."""
    features_dir = BASE_PATH / "code" / "features"
    assert features_dir.exists(), f"Features code directory {features_dir} does not exist"
    assert features_dir.is_dir(), f"{features_dir} is not a directory"

def test_code_models_directory_exists():
    """Verify the models code subdirectory exists."""
    models_code_dir = BASE_PATH / "code" / "models"
    assert models_code_dir.exists(), f"Models code directory {models_code_dir} does not exist"
    assert models_code_dir.is_dir(), f"{models_code_dir} is not a directory"

def test_code_evaluation_directory_exists():
    """Verify the evaluation code subdirectory exists."""
    eval_dir = BASE_PATH / "code" / "evaluation"
    assert eval_dir.exists(), f"Evaluation code directory {eval_dir} does not exist"
    assert eval_dir.is_dir(), f"{eval_dir} is not a directory"

def test_code_visualization_directory_exists():
    """Verify the visualization code subdirectory exists."""
    viz_dir = BASE_PATH / "code" / "visualization"
    assert viz_dir.exists(), f"Visualization code directory {viz_dir} does not exist"
    assert viz_dir.is_dir(), f"{viz_dir} is not a directory"

def test_code_utils_directory_exists():
    """Verify the utils code subdirectory exists."""
    utils_dir = BASE_PATH / "code" / "utils"
    assert utils_dir.exists(), f"Utils code directory {utils_dir} does not exist"
    assert utils_dir.is_dir(), f"{utils_dir} is not a directory"

def test_tests_directory_exists():
    """Verify the tests directory exists."""
    tests_dir = BASE_PATH / "tests"
    assert tests_dir.exists(), f"Tests directory {tests_dir} does not exist"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"

def test_tests_contract_directory_exists():
    """Verify the contract tests subdirectory exists."""
    contract_dir = BASE_PATH / "tests" / "contract"
    assert contract_dir.exists(), f"Contract tests directory {contract_dir} does not exist"
    assert contract_dir.is_dir(), f"{contract_dir} is not a directory"

def test_tests_integration_directory_exists():
    """Verify the integration tests subdirectory exists."""
    integration_dir = BASE_PATH / "tests" / "integration"
    assert integration_dir.exists(), f"Integration tests directory {integration_dir} does not exist"
    assert integration_dir.is_dir(), f"{integration_dir} is not a directory"

def test_tests_unit_directory_exists():
    """Verify the unit tests subdirectory exists."""
    unit_dir = BASE_PATH / "tests" / "unit"
    assert unit_dir.exists(), f"Unit tests directory {unit_dir} does not exist"
    assert unit_dir.is_dir(), f"{unit_dir} is not a directory"

def test_models_directory_exists():
    """Verify the models output directory exists."""
    models_dir = BASE_PATH / "models"
    assert models_dir.exists(), f"Models directory {models_dir} does not exist"
    assert models_dir.is_dir(), f"{models_dir} is not a directory"

def test_all_required_directories_exist():
    """Verify all required directories exist."""
    required_dirs = [
        BASE_PATH / "data",
        BASE_PATH / "data" / "raw",
        BASE_PATH / "data" / "processed",
        BASE_PATH / "data" / "outputs",
        BASE_PATH / "data" / "config",
        BASE_PATH / "code",
        BASE_PATH / "code" / "ingestion",
        BASE_PATH / "code" / "features",
        BASE_PATH / "code" / "models",
        BASE_PATH / "code" / "evaluation",
        BASE_PATH / "code" / "visualization",
        BASE_PATH / "code" / "utils",
        BASE_PATH / "tests",
        BASE_PATH / "tests" / "contract",
        BASE_PATH / "tests" / "integration",
        BASE_PATH / "tests" / "unit",
        BASE_PATH / "models",
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not dir_path.exists() or not dir_path.is_dir():
            missing.append(str(dir_path))
    
    if missing:
        pytest.fail(f"The following required directories are missing:\n  - " + "\n  - ".join(missing))