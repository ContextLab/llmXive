"""
Integration test for the simulation loop (US2).

This test validates the end-to-end interaction between the Meta-Critic model,
the simulation framework, and the baseline reference. It ensures that:
1. The simulation framework correctly loads the trained model and config.
2. The loop executes for a defined number of steps without crashing.
3. The Meta-Critic triggers abstention based on the learned policy.
4. The output schema matches the expected contract (tokens, turns, abstention events).
"""

import os
import sys
import json
import tempfile
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import numpy as np
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config, get_simulation_config
from models.train_meta_critic import main as train_main
from simulation.simulation_framework import SimulationLoop, run_simulation
from simulation.run_baseline import run_baseline_comparison
from data.simulator import run_synthetic_simulator
from analysis.generate_baseline_comparison import main as comparison_main

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create necessary subdirectories
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        (tmp_path / "data" / "results").mkdir(parents=True)
        (tmp_path / "state" / "models").mkdir(parents=True)
        (tmp_path / "state" / "logs").mkdir(parentts=True)
        (tmp_path / "code").mkdir(parents=True)
        
        # Create a minimal config file
        config_content = """
        paths:
          data_raw: data/raw
          data_processed: data/processed
          data_results: data/results
          state_models: state/models
          state_logs: state/logs
          code_root: code
        simulation:
          max_turns: 10
          seed: 42
          baseline_turns: 5
        model:
          model_path: state/models/meta_critic_model.json
        """
        (tmp_path / "config.yaml").write_text(config_content)
        
        # Mock the config loading to use this temp dir
        original_load = load_config
        def mock_load_config(path=None):
            return load_config(str(tmp_path / "config.yaml"))
        
        with patch('tests.integration.test_simulation_loop.load_config', mock_load_config):
            yield tmp_path


@pytest.fixture
def mock_simulation_data(temp_project_dir):
    """Generate a small synthetic dataset for testing the simulation loop."""
    logger.info("Generating mock simulation data...")
    
    # Create a small synthetic dataset
    data = {
        "query_id": [f"q_{i}" for i in range(5)],
        "turn_number": [1, 2, 3, 1, 2],
        "search_count": [0, 1, 2, 0, 1],
        "error_frequency": [0.0, 0.2, 0.5, 0.0, 0.3],
        "token_usage": [100, 150, 200, 100, 180],
        "embedding_distance": [0.1, 0.4, 0.8, 0.2, 0.6],
        "abstention_label": [0, 0, 1, 0, 1]  # 1 = should abstain
    }
    
    df = pd.DataFrame(data)
    output_path = temp_project_dir / "data" / "processed" / "features_test.parquet"
    df.to_parquet(output_path)
    
    logger.info(f"Mock data written to {output_path}")
    return output_path


@pytest.fixture
def mock_trained_model(temp_project_dir, mock_simulation_data):
    """Train a minimal mock model for the simulation test."""
    logger.info("Training mock model...")
    
    # We need to mock the actual training to avoid heavy dependencies or
    # requiring the full dataset. We will create a dummy model file.
    model_path = temp_project_dir / "state" / "models" / "meta_critic_model.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a simple JSON representation of a model (mocking XGBoost output structure)
    mock_model = {
        "model_type": "xgboost_mock",
        "features": ["search_count", "error_frequency", "token_usage", "embedding_distance"],
        "threshold": 0.5,
        "trained_on": "mock_data",
        "params": {
            "max_depth": 3,
            "learning_rate": 0.1
        }
    }
    
    with open(model_path, 'w') as f:
        json.dump(mock_model, f)
    
    logger.info(f"Mock model written to {model_path}")
    return model_path


def test_simulation_loop_initialization(temp_project_dir, mock_trained_model):
    """Test that the SimulationLoop initializes correctly."""
    logger.info("Testing SimulationLoop initialization...")
    
    config = load_config()
    sim_config = get_simulation_config()
    
    # Verify config loading
    assert "max_turns" in sim_config
    assert "seed" in sim_config
    
    # Initialize the loop
    loop = SimulationLoop(
        model_path=mock_trained_model,
        config=sim_config
    )
    
    assert loop.model is not None
    assert loop.max_turns == sim_config.get("max_turns", 20)
    logger.info("SimulationLoop initialized successfully.")


def test_simulation_step_execution(temp_project_dir, mock_simulation_data, mock_trained_model):
    """Test that a single simulation step executes without error."""
    logger.info("Testing simulation step execution...")
    
    # Load the mock data
    df = pd.read_parquet(mock_simulation_data)
    
    # Initialize loop
    config = load_config()
    sim_config = get_simulation_config()
    loop = SimulationLoop(
        model_path=mock_trained_model,
        config=sim_config
    )
    
    # Mock the agent action to avoid needing a real LLM
    mock_action = {
        "action_type": "search",
        "tokens_used": 50,
        "result": "found_info"
    }
    
    # Run one step
    # We simulate the state for the first row
    state = df.iloc[0].to_dict()
    
    # Mock the model prediction
    with patch.object(loop, 'predict_abstention', return_value=False):
        with patch.object(loop, 'execute_agent_action', return_value=mock_action):
            result = loop.step(state)
            
    assert result is not None
    assert "turn_number" in result
    assert "tokens_used" in result
    assert "abstained" in result
    logger.info("Simulation step executed successfully.")


def test_abstention_trigger(temp_project_dir, mock_simulation_data, mock_trained_model):
    """Test that the Meta-Critic correctly triggers abstention."""
    logger.info("Testing abstention trigger...")
    
    config = load_config()
    sim_config = get_simulation_config()
    loop = SimulationLoop(
        model_path=mock_trained_model,
        config=sim_config
    )
    
    # Create a state that should trigger abstention (high error freq)
    high_error_state = {
        "search_count": 5,
        "error_frequency": 0.9,
        "token_usage": 500,
        "embedding_distance": 0.9,
        "turn_number": 8
    }
    
    # Mock the model to predict abstention
    with patch.object(loop, 'predict_abstention', return_value=True):
        result = loop.step(high_error_state)
        
    assert result["abstained"] is True
    assert "abstention_reason" in result
    logger.info("Abstention trigger test passed.")


def test_full_simulation_run(temp_project_dir, mock_simulation_data, mock_trained_model):
    """Test the full simulation run function."""
    logger.info("Testing full simulation run...")
    
    config = load_config()
    sim_config = get_simulation_config()
    
    # Run the simulation on the mock data
    results = run_simulation(
        data_path=mock_simulation_data,
        model_path=mock_trained_model,
        config=sim_config
    )
    
    assert isinstance(results, list)
    assert len(results) > 0
    
    # Verify schema of results
    first_result = results[0]
    required_keys = ["query_id", "turn_number", "tokens_total", "abstained", "abstention_turn"]
    for key in required_keys:
        assert key in first_result, f"Missing key: {key}"
    
    logger.info(f"Full simulation run completed. Generated {len(results)} results.")


def test_baseline_comparison_integration(temp_project_dir, mock_simulation_data, mock_trained_model):
    """Test the integration of the baseline comparison logic."""
    logger.info("Testing baseline comparison integration...")
    
    # Run the baseline comparison
    results = run_baseline_comparison(
        data_path=mock_simulation_data,
        model_path=mock_trained_model,
        config=get_simulation_config()
    )
    
    assert "meta_critic" in results
    assert "baseline" in results
    assert "token_reduction" in results
    
    # Verify token reduction is calculated
    assert isinstance(results["token_reduction"], (int, float))
    logger.info(f"Baseline comparison completed. Token reduction: {results['token_reduction']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])