"""
Tests for scripts/generate_test_set.py

These tests verify that the test set generation script:
1. Runs without errors (with mocked physics)
2. Produces the expected output files
3. Correctly verifies zero overlap with baseline
4. Handles configuration overrides properly
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))
sys.path.insert(0, str(project_root / "scripts"))

from config import Config, TopologyConfig, SolverConfig, ExperimentConfig
from utils import set_deterministic_seed

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration for testing."""
    config = Config(
        topology=TopologyConfig(
            min_hinge_count=3,
            max_hinge_count=10,
            material_stiffness_range=(0.1, 1.0)
        ),
        solver=SolverConfig(
            timeout_limits=300,
            max_iterations=1000
        ),
        experiment=ExperimentConfig(
            seed=42,
            trial_count=5,  # Small number for testing
            output_dir=str(temp_dir)
        )
    )
    return config

@pytest.fixture
def mock_baseline_metadata(temp_dir):
    """Create a mock baseline metadata file."""
    baseline_path = temp_dir / "gam_baseline_metadata.json"
    baseline_data = {
        "topology_ids": ["baseline_001", "baseline_002", "baseline_003"],
        "object_types": ["rigid_body", "hinge_chain"]
    }
    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f)
    return baseline_path

@pytest.fixture
def mock_generated_physics_states(temp_dir):
    """Create a mock generated physics states file."""
    states_path = temp_dir / "physics_states.json"
    states_data = {
        "topology_ids": ["generated_001", "generated_002"],
        "trials": [
            {
                "trial_id": 1,
                "topology_id": "generated_001",
                "states": [{"t": 0, "vertices": [[0, 0, 0]]}]
            }
        ]
    }
    with open(states_path, 'w') as f:
        json.dump(states_data, f)
    return states_path

def test_generate_test_set_script_imports():
    """Test that the script can be imported without errors."""
    from scripts.generate_test_set import parse_args, main
    assert parse_args is not None
    assert main is not None

@patch('scripts.generate_test_set.setup_logging')
@patch('scripts.generate_test_set.load_config')
@patch('scripts.generate_test_set.set_deterministic_seed')
@patch('scripts.generate_test_set.TopologyShiftGenerator')
@patch('scripts.generate_test_set.generation_main')
@patch('scripts.generate_test_set.verify_zero_overlap')
@patch('scripts.generate_test_set.generate_test_set_metadata')
def test_main_execution_flow(
    mock_metadata,
    mock_verify,
    mock_gen_main,
    mock_generator,
    mock_seed,
    mock_load_config,
    mock_setup_logging,
    mock_config,
    mock_baseline_metadata,
    temp_dir
):
    """Test the main execution flow of the generation script."""
    # Setup mocks
    mock_logger = MagicMock()
    mock_setup_logging.return_value = mock_logger
    mock_load_config.return_value = mock_config
    
    mock_generator_instance = MagicMock()
    mock_generator.return_value = mock_generator_instance
    
    mock_verify.return_value = {
        "overlap_detected": False,
        "generated_topology_ids": ["generated_001", "generated_002"]
    }
    
    # Create necessary directories
    (temp_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (temp_dir / "data" / "generated").mkdir(parents=True, exist_ok=True)
    (temp_dir / "data" / "results").mkdir(parents=True, exist_ok=True)
    
    # Mock the baseline metadata file to exist
    baseline_path = temp_dir / "data" / "raw" / "gam_baseline_metadata.json"
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(baseline_path, 'w') as f:
        json.dump({"topology_ids": ["baseline_001"], "object_types": ["test"]}, f)
    
    # Mock generated physics states
    states_path = temp_dir / "data" / "generated" / "physics_states.json"
    with open(states_path, 'w') as f:
        json.dump({"topology_ids": ["gen_001"], "trials": []}, f)
    
    # Run main
    from scripts.generate_test_set import main
    with patch.object(sys, 'argv', ['generate_test_set.py']):
        main()
    
    # Verify calls
    mock_setup_logging.assert_called_once()
    mock_load_config.assert_called_once()
    mock_seed.assert_called_once()
    mock_generator.assert_called_once()
    mock_gen_main.assert_called_once()
    mock_verify.assert_called_once()
    mock_metadata.assert_called_once()
    mock_logger.info.assert_called()

@patch('scripts.generate_test_set.verify_zero_overlap')
def test_zero_overlap_failure(mock_verify, mock_config, mock_baseline_metadata, temp_dir):
    """Test that the script exits when zero overlap verification fails."""
    mock_verify.return_value = {
        "overlap_detected": True,
        "overlap_ids": ["baseline_001"],
        "generated_topology_ids": ["baseline_001", "generated_002"]
    }
    
    # Setup directories and files
    (temp_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (temp_dir / "data" / "generated").mkdir(parents=True, exist_ok=True)
    baseline_path = temp_dir / "data" / "raw" / "gam_baseline_metadata.json"
    with open(baseline_path, 'w') as f:
        json.dump({"topology_ids": ["baseline_001"], "object_types": ["test"]}, f)
    
    states_path = temp_dir / "data" / "generated" / "physics_states.json"
    with open(states_path, 'w') as f:
        json.dump({"topology_ids": ["baseline_001"], "trials": []}, f)
    
    from scripts.generate_test_set import main
    
    with pytest.raises(SystemExit) as exc_info:
        with patch.object(sys, 'argv', ['generate_test_set.py']):
            main()
    
    assert exc_info.value.code == 1

def test_seed_override(mock_config, temp_dir):
    """Test that seed can be overridden via command line."""
    from scripts.generate_test_set import parse_args
    
    # Simulate command line arguments
    with patch.object(sys, 'argv', ['generate_test_set.py', '--seed', '12345']):
        args = parse_args()
        assert args.seed == 12345
    
    # Default seed
    with patch.object(sys, 'argv', ['generate_test_set.py']):
        args = parse_args()
        assert args.seed is None

@patch('scripts.generate_test_set.load_config')
def test_missing_config_file(mock_load_config, temp_dir):
    """Test that the script exits when config file is missing."""
    mock_load_config.side_effect = FileNotFoundError("Config not found")
    
    from scripts.generate_test_set import main
    
    with patch.object(sys, 'argv', ['generate_test_set.py', '--config', '/nonexistent.yaml']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1

@patch('scripts.generate_test_set.load_config')
def test_missing_baseline_metadata(mock_load_config, temp_dir):
    """Test that the script exits when baseline metadata is missing."""
    mock_config = mock_config
    
    # Setup directories
    (temp_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
    
    from scripts.generate_test_set import main
    
    with patch.object(sys, 'argv', ['generate_test_set.py']):
        with patch('scripts.generate_test_set.load_config', return_value=mock_config):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1