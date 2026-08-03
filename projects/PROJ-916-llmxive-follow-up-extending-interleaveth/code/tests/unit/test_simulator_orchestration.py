"""
Unit tests for the simulator orchestration logic (T014).
"""
import pytest
import json
from unittest.mock import patch, MagicMock

from src.simulator.simulator import run_simulation, SimulationResult
from src.config import reset_config, Config
from src.simulator.parser import SceneDescription, ParsedObject, ParsedRelationship
from src.simulator.noise_injector import NoiseInjectionResult

@pytest.fixture(autouse=True)
def reset_config_state():
    """Ensure config is reset before each test."""
    reset_config()
    yield
    reset_config()

def create_mock_base_description():
    """Helper to create a valid base SceneDescription."""
    return SceneDescription(
        objects=[
            ParsedObject(id="obj1", label="cat", attributes=["fluffy"]),
            ParsedObject(id="obj2", label="mat", attributes=["red"])
        ],
        relationships=[
            ParsedRelationship(subject="obj1", predicate="on", object="obj2")
        ]
    )

def create_mock_noise_result(base_desc):
    """Helper to create a mock noise result that removes one object."""
    modified = create_mock_base_description()
    # Remove one object to simulate noise
    modified.objects = [modified.objects[0]] 
    return NoiseInjectionResult(
        modified_description=modified,
        removed_objects_count=1,
        swapped_relationships_count=0
    )

@patch('src.simulator.simulator.parse_caption_to_scene_description')
def test_simulator_perfect_mode(mock_parse, reset_config_state):
    """Test that Perfect mode returns the parsed description without noise."""
    # Setup
    mock_desc = create_mock_base_description()
    mock_parse.return_value = mock_desc
    
    # Configure global config to Perfect
    reset_config()
    # We rely on the default or explicit setting in get_config logic if needed,
    # but run_simulation accepts mode arg which overrides config.
    
    # Execute
    result = run_simulation("A cat on a mat", mode="Perfect")
    
    # Assert
    assert result.mode == "Perfect"
    assert result.prompt == "A cat on a mat"
    assert result.noise_result is None
    assert result.error_rate == 0.0
    assert len(result.scene_description.objects) == 2
    mock_parse.assert_called_once_with("A cat on a mat")

@patch('src.simulator.simulator.parse_caption_to_scene_description')
@patch('src.simulator.simulator.inject_noise')
def test_simulator_noisy_mode(mock_inject, mock_parse, reset_config_state):
    """Test that Noisy mode applies noise and calculates error rate."""
    # Setup
    base_desc = create_mock_base_description()
    mock_parse.return_value = base_desc
    
    noise_res = create_mock_noise_result(base_desc)
    mock_inject.return_value = noise_res
    
    # Execute
    result = run_simulation("A cat on a mat", mode="Noisy")
    
    # Assert
    assert result.mode == "Noisy"
    assert result.noise_result is not None
    assert result.noise_result.removed_objects_count == 1
    # Error rate calculation: 1 removed object out of 3 total elements (2 objects + 1 rel) = 0.333
    # Note: The implementation calculates based on total elements in base vs removed/swapped
    # Total elements in base = 2 objects + 1 rel = 3. Removed = 1. Swapped = 0. Rate = 1/3.
    assert abs(result.error_rate - (1/3)) < 0.001
    
    # Verify inject_noise was called with the base description
    mock_inject.assert_called_once_with(base_desc)

@patch('src.simulator.simulator.parse_caption_to_scene_description')
def test_simulator_invalid_mode(mock_parse, reset_config_state):
    """Test that an invalid mode raises ValueError."""
    mock_parse.return_value = create_mock_base_description()
    
    with pytest.raises(ValueError, match="Invalid simulator mode"):
        run_simulation("A cat on a mat", mode="InvalidMode")

@patch('src.simulator.simulator.parse_caption_to_scene_description')
def test_simulator_config_fallback(mock_parse, reset_config_state):
    """Test that the simulator falls back to config.simulator_mode if mode arg is None."""
    mock_parse.return_value = create_mock_base_description()
    
    # Force config to be Noisy
    with patch('src.simulator.simulator.get_config') as mock_get_config:
        mock_config = MagicMock(spec=Config)
        mock_config.simulator_mode = "Noisy"
        mock_get_config.return_value = mock_config
        
        with patch('src.simulator.simulator.inject_noise') as mock_inject:
            mock_inject.return_value = create_mock_noise_result(create_mock_base_description())
            
            # Call without explicit mode
            result = run_simulation("A cat on a mat")
            
            assert result.mode == "Noisy"
            mock_get_config.assert_called_once()

def test_simulation_result_serialization():
    """Test that SimulationResult can be serialized to JSON."""
    base_desc = create_mock_base_description()
    noise_res = create_mock_noise_result(base_desc)
    
    result = SimulationResult(
        prompt="Test",
        mode="Noisy",
        scene_description=base_desc,
        scene_graph=base_desc.to_scene_graph(),
        noise_result=noise_res,
        error_rate=0.33
    )
    
    data = result.to_dict()
    assert "prompt" in data
    assert "scene_description" in data
    assert data["mode"] == "Noisy"
    
    # Verify it's valid JSON
    json_str = json.dumps(data)
    assert json_str is not None