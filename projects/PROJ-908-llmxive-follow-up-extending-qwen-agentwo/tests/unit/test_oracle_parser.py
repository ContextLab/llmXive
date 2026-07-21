"""
Contract test for code/oracle/parser.py.
Verifies schema alignment for StateTransition and InteractionLogic dataclasses.
"""
import json
import pytest
from dataclasses import asdict

# Import the parser module components
try:
    from code.oracle.parser import StateTransition, InteractionLogic, QwenAgentWorldParser
except ImportError:
    pytest.skip("Oracle parser module not yet implemented", allow_module_level=True)

@pytest.mark.unit
def test_state_transition_schema():
    """Verify StateTransition dataclass has expected fields."""
    # Create an instance to test serialization
    state = StateTransition(
        state_id="s1",
        action="move_north",
        pre_conditions=["at_south"],
        post_conditions=["at_north"],
        probability=1.0
    )
    
    # Convert to dict (schema check)
    state_dict = asdict(state)
    
    required_fields = {"state_id", "action", "pre_conditions", "post_conditions", "probability"}
    assert set(state_dict.keys()) == required_fields, f"Schema mismatch: {set(state_dict.keys())}"
    
    # Verify types
    assert isinstance(state_dict["state_id"], str)
    assert isinstance(state_dict["action"], str)
    assert isinstance(state_dict["pre_conditions"], list)
    assert isinstance(state_dict["post_conditions"], list)
    assert isinstance(state_dict["probability"], float)

@pytest.mark.unit
def test_interaction_logic_schema():
    """Verify InteractionLogic dataclass has expected fields."""
    logic = InteractionLogic(
        rule_id="r1",
        description="If at south, can move north",
        conditions=["at_south"],
        effect="at_north",
        source_file="agent.py"
    )
    
    logic_dict = asdict(logic)
    
    required_fields = {"rule_id", "description", "conditions", "effect", "source_file"}
    assert set(logic_dict.keys()) == required_fields, f"Schema mismatch: {set(logic_dict.keys())}"

@pytest.mark.unit
def test_parser_initialization():
    """Verify parser can be initialized."""
    parser = QwenAgentWorldParser()
    assert parser is not None
    assert hasattr(parser, "parse")
    
@pytest.mark.unit
def test_parser_parse_signature():
    """Verify parse method signature."""
    parser = QwenAgentWorldParser()
    # Check that parse method exists and accepts expected arguments
    import inspect
    sig = inspect.signature(parser.parse)
    params = list(sig.parameters.keys())
    # We expect at least 'source_code' or similar
    assert len(params) >= 1, "Parser.parse should accept arguments"