"""
Symbolic Parser Module for llmXive BES Pipeline.

Converts puzzle constraints from the dataset format into a formal language
parseable by the symbolic planner (code/symbolic/planner.py).

Handles:
- Parsing JSON puzzle instances
- Detecting malformed structures (raising PARSE_FAILURE)
- Detecting logical contradictions in constraints (raising CONTRADICTION_DETECTED)
- Generating a formal representation string for the planner
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Import custom exceptions from the project's exception module
from code.exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, raise_parse_failure, raise_contradiction


class FormalConstraint:
    """Represents a single parsed constraint in the formal language."""
    def __init__(self, constraint_type: str, variables: List[str], value: Any, raw_desc: str):
        self.constraint_type = constraint_type
        self.variables = variables
        self.value = value
        self.raw_desc = raw_desc

    def __repr__(self):
        return f"FormalConstraint({self.constraint_type}, {self.variables}, {self.value})"


class PuzzleParser:
    """
    Parses puzzle instances into a formal language representation.

    Supported formal language constructs (internal representation):
    - EQUALS(var, value)
    - NOT_EQUALS(var, value)
    - IN_SET(var, [val1, val2, ...])
    - UNIQUE(var_list)
    - ADJACENT(var1, var2)
    - SUM_EQUALS(var_list, value)
    """

    def __init__(self):
        self.errors = []
        self.warnings = []

    def parse_puzzle_instance(self, instance: Dict[str, Any]) -> Tuple[List[FormalConstraint], Dict[str, Any]]:
        """
        Parses a dictionary representation of a puzzle instance into formal constraints.

        Args:
            instance: A dictionary representing a puzzle instance (from data/raw/).

        Returns:
            A tuple of (list of FormalConstraint objects, metadata dict).

        Raises:
            PARSE_FAILURE: If the structure is malformed or missing required keys.
            CONTRADICTION_DETECTED: If constraints logically contradict each other.
        """
        if not isinstance(instance, dict):
            raise_parse_failure("Input instance must be a dictionary.")

        # Validate required keys
        required_keys = ['id', 'constraints', 'variables']
        for key in required_keys:
            if key not in instance:
                raise_parse_failure(f"Missing required key in puzzle instance: '{key}'")

        puzzle_id = instance['id']
        variables = instance['variables']
        raw_constraints = instance['constraints']

        if not isinstance(variables, list):
            raise_parse_failure("'variables' must be a list of variable names.")

        if not isinstance(raw_constraints, list):
            raise_parse_failure("'constraints' must be a list of constraint objects.")

        formal_constraints = []
        parsed_vars = set()

        # Parse variables to ensure uniqueness
        for var in variables:
            if not isinstance(var, str):
                raise_parse_failure(f"Variable name must be a string, got: {type(var)}")
            parsed_vars.add(var)

        # Parse constraints
        for idx, raw_constraint in enumerate(raw_constraints):
            if not isinstance(raw_constraint, dict):
                raise_parse_failure(f"Constraint at index {idx} is not a dictionary.")

            constraint_type = raw_constraint.get('type')
            if not constraint_type:
                raise_parse_failure(f"Constraint at index {idx} missing 'type' field.")

            # Map high-level types to internal formal types
            formal_type = self._map_constraint_type(constraint_type)
            if not formal_type:
                raise_parse_failure(f"Unknown constraint type '{constraint_type}' at index {idx}.")

            # Extract variables and values based on type
            parsed_vars_in_constraint, value = self._extract_constraint_data(
                formal_type, raw_constraint, parsed_vars, idx
            )

            # Check for contradictions immediately
            self._check_contradictions(formal_constraints, FormalConstraint(
                formal_type, parsed_vars_in_constraint, value, str(raw_constraint)
            ), idx)

            formal_constraints.append(FormalConstraint(
                formal_type, parsed_vars_in_constraint, value, str(raw_constraint)
            ))

        return formal_constraints, {'id': puzzle_id, 'variable_count': len(parsed_vars)}

    def _map_constraint_type(self, type_str: str) -> Optional[str]:
        """Maps dataset constraint types to internal formal language types."""
        type_map = {
            'equals': 'EQUALS',
            'not_equals': 'NOT_EQUALS',
            'in_set': 'IN_SET',
            'unique': 'UNIQUE',
            'adjacent': 'ADJACENT',
            'sum_equals': 'SUM_EQUALS',
            'range': 'RANGE'
        }
        return type_map.get(type_str.lower())

    def _extract_constraint_data(self, formal_type: str, raw: Dict, valid_vars: set, idx: int) -> Tuple[List[str], Any]:
        """Extracts variables and values from a raw constraint dict."""
        vars_list = []
        value = None

        if formal_type == 'EQUALS' or formal_type == 'NOT_EQUALS':
            vars_list = [raw.get('variable')]
            value = raw.get('value')
            if not vars_list[0] or vars_list[0] not in valid_vars:
                raise_parse_failure(f"Invalid variable '{vars_list[0]}' in constraint at index {idx}.")
            if value is None:
                raise_parse_failure(f"Missing 'value' in constraint at index {idx}.")

        elif formal_type == 'IN_SET':
            vars_list = [raw.get('variable')]
            value = raw.get('possible_values', [])
            if not isinstance(value, list):
                raise_parse_failure(f"'possible_values' must be a list in constraint at index {idx}.")
            if not vars_list[0] or vars_list[0] not in valid_vars:
                raise_parse_failure(f"Invalid variable '{vars_list[0]}' in constraint at index {idx}.")

        elif formal_type == 'UNIQUE':
            vars_list = raw.get('variables', [])
            if not isinstance(vars_list, list) or len(vars_list) < 2:
                raise_parse_failure(f"'variables' must be a list of at least 2 items in constraint at index {idx}.")
            for v in vars_list:
                if v not in valid_vars:
                    raise_parse_failure(f"Invalid variable '{v}' in constraint at index {idx}.")

        elif formal_type == 'ADJACENT':
            vars_list = raw.get('variables', [])
            if len(vars_list) != 2:
                raise_parse_failure(f"ADJACENT constraint requires exactly 2 variables at index {idx}.")
            for v in vars_list:
                if v not in valid_vars:
                    raise_parse_failure(f"Invalid variable '{v}' in constraint at index {idx}.")

        elif formal_type == 'SUM_EQUALS':
            vars_list = raw.get('variables', [])
            value = raw.get('target_sum')
            if not isinstance(vars_list, list):
                raise_parse_failure(f"'variables' must be a list in constraint at index {idx}.")
            if value is None:
                raise_parse_failure(f"Missing 'target_sum' in constraint at index {idx}.")
            for v in vars_list:
                if v not in valid_vars:
                    raise_parse_failure(f"Invalid variable '{v}' in constraint at index {idx}.")

        elif formal_type == 'RANGE':
            vars_list = [raw.get('variable')]
            value = (raw.get('min'), raw.get('max'))
            if not vars_list[0] or vars_list[0] not in valid_vars:
                raise_parse_failure(f"Invalid variable '{vars_list[0]}' in constraint at index {idx}.")
            if value[0] is None or value[1] is None:
                raise_parse_failure(f"Missing 'min' or 'max' in RANGE constraint at index {idx}.")

        return vars_list, value

    def _check_contradictions(self, existing: List[FormalConstraint], new: FormalConstraint, idx: int):
        """
        Checks if the new constraint contradicts any existing constraints.
        Raises CONTRADICTION_DETECTED if a contradiction is found.
        """
        # Simple contradiction checks for EQUALS vs NOT_EQUALS
        for existing_c in existing:
            # Check for direct variable conflict
            if existing_c.constraint_type == 'EQUALS' and new.constraint_type == 'NOT_EQUALS':
                if set(existing_c.variables) == set(new.variables):
                    if existing_c.value == new.value:
                        raise_contradiction(
                            f"Contradiction at constraint {idx}: Variable {existing_c.variables} cannot be "
                            f"equal to {existing_c.value} and NOT equal to {new.value} simultaneously."
                        )

            if existing_c.constraint_type == 'NOT_EQUALS' and new.constraint_type == 'EQUALS':
                if set(existing_c.variables) == set(new.variables):
                    if existing_c.value == new.value:
                        raise_contradiction(
                            f"Contradiction at constraint {idx}: Variable {existing_c.variables} cannot be "
                            f"NOT equal to {existing_c.value} and equal to {new.value} simultaneously."
                        )

            # Check for unique constraint conflicts
            if existing_c.constraint_type == 'UNIQUE' and new.constraint_type == 'EQUALS':
                if len(existing_c.variables) > 1 and new.variables[0] in existing_c.variables:
                    # If we have a unique constraint on [A, B] and later an EQUALS(A, 1),
                    # and another EQUALS(B, 1) appears later, that would be a contradiction.
                    # We can't fully check this here without looking ahead, but we can flag
                    # if a UNIQUE constraint is violated by an existing EQUALS on the same value.
                    pass # Defer full check to planner or more complex analysis

    def to_formal_string(self, constraints: List[FormalConstraint]) -> str:
        """
        Converts a list of FormalConstraint objects into a string representation
        suitable for the symbolic planner.
        """
        lines = []
        for c in constraints:
            if c.constraint_type == 'EQUALS':
                lines.append(f"EQUALS({c.variables[0]}, {c.value})")
            elif c.constraint_type == 'NOT_EQUALS':
                lines.append(f"NOT_EQUALS({c.variables[0]}, {c.value})")
            elif c.constraint_type == 'IN_SET':
                lines.append(f"IN_SET({c.variables[0]}, {c.value})")
            elif c.constraint_type == 'UNIQUE':
                lines.append(f"UNIQUE({', '.join(c.variables)})")
            elif c.constraint_type == 'ADJACENT':
                lines.append(f"ADJACENT({c.variables[0]}, {c.variables[1]})")
            elif c.constraint_type == 'SUM_EQUALS':
                lines.append(f"SUM_EQUALS({', '.join(c.variables)}, {c.value})")
            elif c.constraint_type == 'RANGE':
                lines.append(f"RANGE({c.variables[0]}, {c.value[0]}, {c.value[1]})")
            else:
                lines.append(f"# UNKNOWN_TYPE: {c.raw_desc}")

        return "\n".join(lines)


def parse_dataset_file(input_path: str, output_path: str) -> None:
    """
    Reads a JSON file of puzzle instances, parses them, and writes the formal
    representation to an output file.

    Args:
        input_path: Path to the input JSON file (e.g., data/raw/puzzles.json).
        output_path: Path to write the formal representation (e.g., data/processed/puzzles_formal.txt).
    """
    parser = PuzzleParser()

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise_parse_failure(f"Input file not found: {input_path}")
    except json.JSONDecodeError as e:
        raise_parse_failure(f"Invalid JSON in input file: {e}")

    if not isinstance(data, list):
        data = [data]

    formal_output_lines = []
    metadata = []

    for idx, instance in enumerate(data):
        try:
            constraints, info = parser.parse_puzzle_instance(instance)
            formal_str = parser.to_formal_string(constraints)
            formal_output_lines.append(f"--- PUZZLE_ID: {info['id']} ---")
            formal_output_lines.append(formal_str)
            formal_output_lines.append("")
            metadata.append({
                'id': info['id'],
                'variable_count': info['variable_count'],
                'constraint_count': len(constraints),
                'status': 'PARSED'
            })
        except (PARSE_FAILURE, CONTRADICTION_DETECTED) as e:
            metadata.append({
                'id': instance.get('id', f'UNKNOWN_{idx}'),
                'status': 'FAILED',
                'error': str(e)
            })
            formal_output_lines.append(f"--- PUZZLE_ID: {instance.get('id', f'UNKNOWN_{idx}')} ---")
            formal_output_lines.append(f"# PARSE_ERROR: {e}")
            formal_output_lines.append("")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(formal_output_lines))

    # Write metadata log
    meta_path = output_path.replace('.txt', '_meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)


def main():
    """Main entry point for the parser script."""
    import sys
    from code.config import load_config

    config = load_config()
    input_path = config.get('dataset_path', 'data/raw/puzzles.json')
    output_path = config.get('formal_output_path', 'data/processed/puzzles_formal.txt')

    print(f"Parsing dataset from: {input_path}")
    try:
        parse_dataset_file(input_path, output_path)
        print(f"Formal representation written to: {output_path}")
    except Exception as e:
        print(f"Fatal error during parsing: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()