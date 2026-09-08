"""
Contract test for SymbolicState schema validation.

Validates that the SymbolicState dataclass produced by src.state_mapper
conforms to the schema defined in specs/001-symbolic-dojo-extend/contracts/symbolic_state.schema.yaml
using the jsonschema library.
"""
import pytest
import sys
from pathlib import Path
import json
import yaml

# Ensure src and project root are importable
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.state_mapper import SymbolicState


class TestSymbolicStateContract:
    """Tests for SymbolicState schema compliance."""

    @pytest.fixture
    def schema(self):
        """Load the SymbolicState schema from the specs directory."""
        schema_path = project_root / "specs" / "001-symbolic-dojo-extend" / "contracts" / "symbolic_state.schema.yaml"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
        with open(schema_path, "r") as f:
            return yaml.safe_load(f)

    def test_symbolic_state_structure(self, schema):
        """Verify SymbolicState instance matches the schema definition."""
        # Create a valid instance according to the current implementation
        state = SymbolicState(
            state_id="test_state_001",
            predicates=["on_table", "graspable"],
            affordances={"block_a": ["move", "stack"], "block_b": ["stack"]},
            connectivity=["state_1", "state_2"],
            replan_support=True
        )

        # Convert to dictionary for validation
        data = state.__dict__

        # Validate against the loaded JSON/YAML schema
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=schema)
        except ImportError:
            pytest.fail("jsonschema library is required but not installed.")
        except Exception as e:
            pytest.fail(f"SymbolicState instance failed schema validation: {e}")

    def test_replan_support_type(self):
        """Ensure replan_support is strictly a boolean."""
        state = SymbolicState(
            state_id="test_state_002",
            predicates=["on_table"],
            affordances={},
            connectivity=[],
            replan_support=False
        )
        assert isinstance(state.replan_support, bool)
        
        state_true = SymbolicState(
            state_id="test_state_003",
            predicates=["on_table"],
            affordances={},
            connectivity=[],
            replan_support=True
        )
        assert isinstance(state_true.replan_support, bool)

    def test_predicates_list_type(self):
        """Ensure predicates is a list of strings."""
        state = SymbolicState(
            state_id="test_state_004",
            predicates=["on_table", "holding"],
            affordances={},
            connectivity=[],
            replan_support=True
        )
        assert isinstance(state.predicates, list)
        assert all(isinstance(p, str) for p in state.predicates)

    def test_affordances_dict_structure(self):
        """Ensure affordances is a dict mapping strings to lists of strings."""
        state = SymbolicState(
            state_id="test_state_005",
            predicates=[],
            affordances={"obj_a": ["grab", "push"], "obj_b": ["grab"]},
            connectivity=[],
            replan_support=True
        )
        assert isinstance(state.affordances, dict)
        for k, v in state.affordances.items():
            assert isinstance(k, str)
            assert isinstance(v, list)
            assert all(isinstance(item, str) for item in v)

    def test_connectivity_list_type(self):
        """Ensure connectivity is a list of strings."""
        state = SymbolicState(
            state_id="test_state_006",
            predicates=[],
            affordances={},
            connectivity=["next_state_a", "next_state_b"],
            replan_support=True
        )
        assert isinstance(state.connectivity, list)
        assert all(isinstance(c, str) for c in state.connectivity)