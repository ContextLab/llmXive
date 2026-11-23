"""
Unit tests for baseline_runner.py
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from baseline_runner import BaselineAgentState, BaselineAgent, run_baseline_agent
from config_loader import set_seeds

class TestBaselineAgentState:
    def test_initialization(self):
        state = BaselineAgentState(seed=42)
        assert state.seed == 42
        assert state.step_count == 0
        assert len(state.context_history) == 0
        assert state.mental_map == "Initial state: Unknown"
        assert state.last_action == "wait"
        assert state.is_timed_out is False

    def test_update_context(self):
        state = BaselineAgentState(seed=42)
        event_entry = {"event": "move", "step": 0}
        
        state.update_context("frame.png", event_entry)
        
        assert len(state.context_history) == 1
        assert state.context_history[0]["step"] == 0
        assert state.context_history[0]["event"] == event_entry

    def test_context_window_limit(self):
        state = BaselineAgentState(seed=42)
        
        # Add more entries than context window size
        for i in range(60):
            state.update_context(f"frame_{i}.png", {"step": i})
        
        # Should be limited to CONTEXT_WINDOW_SIZE (50)
        assert len(state.context_history) == 50
        # Oldest entries should be removed
        assert state.context_history[0]["step"] == 10
        assert state.context_history[-1]["step"] == 59

    def test_increment_step_and_timeout(self):
        state = BaselineAgentState(seed=42)
        
        # Increment to just below limit
        for _ in range(500):
            state.increment_step()
        
        assert state.step_count == 500
        assert state.is_timed_out is False
        
        # One more increment should trigger timeout
        state.increment_step()
        assert state.step_count == 501
        assert state.is_timed_out is True

class TestBaselineAgent:
    @patch('baseline_runner.HAS_VISION', True)
    @patch('baseline_runner.AutoProcessor')
    @patch('baseline_runner.AutoModelForCausalLM')
    def test_agent_initialization(self, mock_model, mock_processor):
        # Mock the model and processor
        mock_model.return_value.eval.return_value = MagicMock()
        mock_processor.return_value = MagicMock()
        
        agent = BaselineAgent(model_id="test/model")
        assert agent.model_id == "test/model"
        assert agent.processor is not None
        assert agent.model is not None

    @patch('baseline_runner.HAS_VISION', True)
    @patch('baseline_runner.AutoProcessor')
    @patch('baseline_runner.AutoModelForCausalLM')
    def test_parse_valid_response(self, mock_model, mock_processor):
        agent = BaselineAgent(model_id="test/model")
        
        response = """
        Here is my analysis:
        {"action": "move_up", "mental_map": "I am at position (2,3)"}
        """
        
        result = agent._parse_response(response)
        assert result is not None
        assert result["action"] == "move_up"
        assert result["mental_map"] == "I am at position (2,3)"

    @patch('baseline_runner.HAS_VISION', True)
    @patch('baseline_runner.AutoProcessor')
    @patch('baseline_runner.AutoModelForCausalLM')
    def test_parse_invalid_response(self, mock_model, mock_processor):
        agent = BaselineAgent(model_id="test/model")
        
        response = "This is not valid JSON"
        
        result = agent._parse_response(response)
        assert result is None

    @patch('baseline_runner.HAS_VISION', True)
    @patch('baseline_runner.AutoProcessor')
    @patch('baseline_runner.AutoModelForCausalLM')
    def test_parse_malformed_json(self, mock_model, mock_processor):
        agent = BaselineAgent(model_id="test/model")
        
        response = '{"action": "move_up", missing_quote: "mental_map"}'
        
        result = agent._parse_response(response)
        assert result is None

class TestRunBaselineAgent:
    def test_missing_event_log(self, tmp_path):
        # Create a temporary directory structure
        visual_dir = tmp_path / "visual"
        output_dir = tmp_path / "output"
        visual_dir.mkdir()
        output_dir.mkdir()
        
        # Try to run with missing event log
        result = run_baseline_agent(seed=1, visual_data_dir=str(visual_dir), output_dir=str(output_dir))
        
        assert "error" in result
        assert result["error"] == "Event log not found"
        assert result["seed"] == 1

    def test_successful_run_structure(self, tmp_path):
        # Create a temporary directory structure
        visual_dir = tmp_path / "visual"
        output_dir = tmp_path / "output"
        visual_dir.mkdir()
        output_dir.mkdir()
        
        # Create a minimal event log
        event_log = {
            "events": [
                {"step": 0, "event": "start"},
                {"step": 1, "event": "move"}
            ]
        }
        
        event_log_path = visual_dir / "seeds_1.json"
        with open(event_log_path, 'w') as f:
            json.dump(event_log, f)
        
        # Create dummy visual frames
        for i in range(2):
            frame_path = visual_dir / f"seeds_1_frame_{i}.png"
            frame_path.write_bytes(b"dummy_image_data")
        
        # Mock the BaselineAgent to avoid actual model loading
        with patch('baseline_runner.BaselineAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.step.return_value = {
                "action": "move_up",
                "mental_map": "Test mental map"
            }
            mock_agent_class.return_value = mock_agent
            
            result = run_baseline_agent(seed=1, visual_data_dir=str(visual_dir), output_dir=str(output_dir))
            
            # Verify output file was created
            output_path = output_dir / "baseline_seeds_1.json"
            assert output_path.exists()
            
            # Verify result structure
            assert result["seed"] == 1
            assert "run_duration_seconds" in result
            assert "total_steps" in result
            assert "results" in result
            assert len(result["results"]) == 2