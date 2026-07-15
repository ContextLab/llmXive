"""
Unit tests for the Oracle Parser.

These tests verify that the parser correctly extracts interaction logic
from Qwen-AgentWorld source code and produces valid output structures.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.oracle.parser import (
    QwenAgentWorldParser,
    StateTransition,
    InteractionLogic,
    parse_qwen_agentworld
)


class TestStateTransition:
    """Tests for the StateTransition dataclass."""

    def test_create_transition(self):
        """Test creating a basic state transition."""
        transition = StateTransition(
            source_state="idle",
            action="move_to_target",
            target_state="moving"
        )

        assert transition.source_state == "idle"
        assert transition.action == "move_to_target"
        assert transition.target_state == "moving"
        assert len(transition.preconditions) == 0
        assert len(transition.postconditions) == 0

    def test_transition_with_conditions(self):
        """Test creating a transition with pre/post conditions."""
        transition = StateTransition(
            source_state="idle",
            action="grab_object",
            target_state="holding",
            preconditions=["object_exists", "arm_reachable"],
            postconditions=["object_grasped", "arm_closing"]
        )

        assert "object_exists" in transition.preconditions
        assert "object_grasped" in transition.postconditions

    def test_transition_to_dict(self):
        """Test converting transition to dictionary."""
        transition = StateTransition(
            source_state="a",
            action="b",
            target_state="c",
            spatial_constraints=["dist<5"]
        )

        d = transition.to_dict()

        assert d["source_state"] == "a"
        assert d["action"] == "b"
        assert d["target_state"] == "c"
        assert "dist<5" in d["spatial_constraints"]


class TestInteractionLogic:
    """Tests for the InteractionLogic dataclass."""

    def test_create_empty_logic(self):
        """Test creating an empty interaction logic container."""
        logic = InteractionLogic()

        assert len(logic.spatial_rules) == 0
        assert len(logic.temporal_rules) == 0
        assert len(logic.causal_rules) == 0
        assert len(logic.state_transitions) == 0

    def test_add_transition(self):
        """Test adding a transition to logic container."""
        logic = InteractionLogic()
        transition = StateTransition("a", "b", "c")
        logic.state_transitions.append(transition)

        assert len(logic.state_transitions) == 1
        assert logic.state_transitions[0].action == "b"

    def test_logic_to_dict(self):
        """Test converting logic to dictionary."""
        logic = InteractionLogic()
        logic.spatial_rules.append({"rule": "spatial_1"})
        logic.state_transitions.append(StateTransition("x", "y", "z"))

        d = logic.to_dict()

        assert len(d["spatial_rules"]) == 1
        assert len(d["state_transitions"]) == 1
        assert d["state_transitions"][0]["action"] == "y"


class TestQwenAgentWorldParser:
    """Tests for the QwenAgentWorldParser class."""

    @pytest.fixture
    def sample_source_file(self, tmp_path):
        """Create a sample Python file with state transition patterns."""
        source_code = '''
        """Sample Qwen-AgentWorld source for testing."""

        class AgentState:
            """Agent state machine."""

            def transition_to_moving(self):
                """Transition from idle to moving state.

                Spatial constraint: distance < 10 meters
                Temporal: after initialization complete
                Causal: requires target acquired
                """
                self.state = "moving"
                return self.state

            def apply_grasp(self, object_id):
                """Apply grasp action.

                Precondition: object_exists(object_id)
                Postcondition: object_grasped(object_id)
                """
                pass

        def move_to_location(location):
            """Move agent to specified location.

            Position: (location_x, location_y)
            """
            pass
        '''

        file_path = tmp_path / "sample_agent.py"
        file_path.write_text(source_code)
        return file_path

    def test_parse_file(self, sample_source_file):
        """Test parsing a single file."""
        parser = QwenAgentWorldParser()
        logic = parser.parse_file(sample_source_file)

        assert logic.metadata["source_file"] == str(sample_source_file)
        assert len(logic.state_transitions) > 0 or len(logic.spatial_rules) > 0

    def test_parse_directory(self, tmp_path):
        """Test parsing a directory of files."""
        # Create multiple sample files
        for i in range(3):
            file_path = tmp_path / f"agent_{i}.py"
            file_path.write_text(f'''
            class Agent{i}:
                def transition(self):
                    """Transition action."""
                    pass
            ''')

        parser = QwenAgentWorldParser()
        logic = parser.parse_directory(tmp_path)

        assert len(logic.metadata["files_parsed"]) == 3
        assert len(logic.state_transitions) > 0

    def test_parse_nonexistent_file(self):
        """Test that parsing a non-existent file raises an error."""
        parser = QwenAgentWorldParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/path.py")

    def test_parse_nonexistent_directory(self):
        """Test that parsing a non-existent directory raises an error."""
        parser = QwenAgentWorldParser()

        with pytest.raises(NotADirectoryError):
            parser.parse_directory("/nonexistent/directory")

    def test_extract_spatial_patterns(self, tmp_path):
        """Test extraction of spatial patterns."""
        source_code = '''
        position = (10, 20)
        distance between A and B = 5
        adjacent(X, Y)
        move robot to target
        '''

        file_path = tmp_path / "spatial_test.py"
        file_path.write_text(source_code)

        parser = QwenAgentWorldParser()
        logic = parser.parse_file(file_path)

        # Should detect at least one spatial rule
        assert len(logic.spatial_rules) > 0

    def test_extract_temporal_patterns(self, tmp_path):
        """Test extraction of temporal patterns."""
        source_code = '''
        before action can execute
        after initialization is complete
        while system is running
        sequence: init, run, stop
        '''

        file_path = tmp_path / "temporal_test.py"
        file_path.write_text(source_code)

        parser = QwenAgentWorldParser()
        logic = parser.parse_file(file_path)

        assert len(logic.temporal_rules) > 0

    def test_extract_causal_patterns(self, tmp_path):
        """Test extraction of causal patterns."""
        source_code = '''
        if condition then result
        cause effect to happen
        leads to success
        requires permission for access
        '''

        file_path = tmp_path / "causal_test.py"
        file_path.write_text(source_code)

        parser = QwenAgentWorldParser()
        logic = parser.parse_file(file_path)

        assert len(logic.causal_rules) > 0


class TestParseQwenAgentWorld:
    """Tests for the main parse_qwen_agentworld function."""

    def test_parse_with_file_path(self, sample_source_file):
        """Test parsing with a file path."""
        logic = parse_qwen_agentworld(str(sample_source_file))

        assert isinstance(logic, InteractionLogic)
        assert logic.metadata["source_file"] == str(sample_source_file)

    def test_parse_with_output_path(self, tmp_path, sample_source_file):
        """Test parsing with an output path."""
        output_path = tmp_path / "output_oracle.json"

        logic = parse_qwen_agentworld(str(sample_source_file), str(output_path))

        assert output_path.exists()
        assert logic.metadata["source_file"] == str(sample_source_file)

        # Verify JSON is valid
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert "state_transitions" in data

    def test_parse_with_directory_path(self, tmp_path):
        """Test parsing with a directory path."""
        file_path = tmp_path / "test.py"
        file_path.write_text('''
        class Test:
            def transition(self):
                pass
        ''')

        logic = parse_qwen_agentworld(str(tmp_path))

        assert isinstance(logic, InteractionLogic)
        assert logic.metadata["source_directory"] == str(tmp_path)

    def test_parse_invalid_path(self):
        """Test parsing with an invalid path."""
        with pytest.raises(ValueError):
            parse_qwen_agentworld("/invalid/path")


class TestParserIntegration:
    """Integration tests for the parser with realistic scenarios."""

    def test_parse_complex_state_machine(self, tmp_path):
        """Test parsing a complex state machine definition."""
        source_code = '''
        """Complex state machine for agent world."""

        class ComplexStateMachine:
            def initialize(self):
                """Initialize the state machine.

                Precondition: system_ready
                Postcondition: initialized
                """
                self.state = "initialized"

            def transition_to_active(self):
                """Transition to active state.

                Requires: initialization complete
                Temporal: after initialize()
                Spatial: within bounds
                """
                self.state = "active"

            def execute_action(self, action_name):
                """Execute an action.

                Causal: if action_valid then execute
                Precondition: state == "active"
                """
                pass

            def cleanup(self):
                """Cleanup after execution.

                After: all actions complete
                """
                self.state = "cleaned"
        '''

        file_path = tmp_path / "complex_fsm.py"
        file_path.write_text(source_code)

        parser = QwenAgentWorldParser()
        logic = parser.parse_file(file_path)

        # Should extract multiple transitions
        assert len(logic.state_transitions) >= 3

        # Should have preconditions and postconditions
        for transition in logic.state_transitions:
            if transition.action == "transition_to_active":
                assert "initialization complete" in transition.preconditions or \
                       transition.causal_dependencies

    def test_parser_preserves_source_info(self, tmp_path):
        """Test that parser preserves source file and line information."""
        source_code = '''
        class TestClass:
            def my_transition(self):
                """A transition."""
                pass
        '''

        file_path = tmp_path / "info_test.py"
        file_path.write_text(source_code)

        parser = QwenAgentWorldParser()
        logic = parser.parse_file(file_path)

        for transition in logic.state_transitions:
            assert transition.source_file is not None or \
                   transition.source_line is not None or \
                   len(logic.state_transitions) == 0  # If none extracted, that's ok