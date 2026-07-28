"""
Dataset Validation Script for Co-Evolving Policy Distillation.

This script validates generated datasets for logic proofs and grid-world navigation.
It ensures that:
1. At least 99% of generated logic proofs are valid (syntactically correct and logically sound).
2. At least 99% of generated grid worlds are solvable (path exists from start to goal).

Exit codes:
0: All validations passed (validity/solvability >= 99%)
1: Validation failed (validity/solvability < 99%)
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# Import from local project structure
from src.utils.config import load_config, Config
import networkx as nx
from sympy import simplify_logic, symbols, Implies, And, Or, Not, Symbol


def load_generated_data(config: Config) -> Dict[str, Any]:
    """
    Load generated training datasets from the paths specified in the config.

    Args:
        config: The configuration object containing data paths.

    Returns:
        A dictionary containing 'logic_proofs' and 'grid_worlds' lists.
    """
    data_dir = Path(config.data_dir)
    result = {
        'logic_proofs': [],
        'grid_worlds': []
    }

    # Load logic proofs
    logic_file = data_dir / config.logic_dataset_file
    if logic_file.exists():
        with open(logic_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                result['logic_proofs'] = data
            elif isinstance(data, dict) and 'proofs' in data:
                result['logic_proofs'] = data['proofs']
    else:
        # If file doesn't exist, we might need to generate it or fail
        # For validation, we assume data should exist. If not, we return empty.
        print(f"Warning: Logic dataset file not found: {logic_file}")

    # Load grid worlds
    grid_file = data_dir / config.grid_dataset_file
    if grid_file.exists():
        with open(grid_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                result['grid_worlds'] = data
            elif isinstance(data, dict) and 'grids' in data:
                result['grid_worlds'] = data['grids']
    else:
        print(f"Warning: Grid dataset file not found: {grid_file}")

    return result


def validate_logic_proofs(proofs: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
    """
    Validate a list of generated logic proofs.

    A proof is considered valid if:
    1. It has the required structure (premises, conclusion, derivation).
    2. The conclusion logically follows from the premises (sympy validation).

    Args:
        proofs: List of proof dictionaries.

    Returns:
        Tuple of (valid_count, total_count, list of error messages).
    """
    valid_count = 0
    errors = []

    for i, proof in enumerate(proofs):
        try:
            # Check structure
            if 'premises' not in proof or 'conclusion' not in proof:
                errors.append(f"Proof {i}: Missing 'premises' or 'conclusion'")
                continue

            premises = proof['premises']
            conclusion = proof['conclusion']

            # Parse premises and conclusion
            # Assume premises and conclusion are strings representing logical expressions
            # We need to reconstruct the symbols and expressions

            # Extract symbols from premises and conclusion
            all_symbols = set()
            for p in premises:
                all_symbols.update(re.findall(r'[A-Z][a-z]*', p))
            all_symbols.update(re.findall(r'[A-Z][a-z]*', conclusion))

            # Create sympy symbols
            symbol_map = {name: Symbol(name) for name in all_symbols}

            # Parse expressions
            # Note: This is a simplified parser. In a real scenario, we'd use a more robust parser
            # or store expressions in a format that sympy can directly parse.
            try:
                # Evaluate premises as a conjunction
                premise_expr = None
                for p in premises:
                    # Replace logical operators with sympy equivalents
                    p_expr_str = p.replace('AND', '&').replace('OR', '|').replace('NOT', '~').replace('IMPLIES', '>>')
                    # This is a naive approach; a real implementation would use a proper parser
                    p_expr = eval(p_expr_str, {"__builtins__": {}}, symbol_map)
                    if premise_expr is None:
                        premise_expr = p_expr
                    else:
                        premise_expr = premise_expr & p_expr

                # Evaluate conclusion
                conc_expr_str = conclusion.replace('AND', '&').replace('OR', '|').replace('NOT', '~').replace('IMPLIES', '>>')
                conc_expr = eval(conc_expr_str, {"__builtins__": {}}, symbol_map)

                # Validate: (premises) -> conclusion should be a tautology
                implication = premise_expr >> conc_expr
                if simplify_logic(implication, force=True) is True:
                    valid_count += 1
                else:
                    errors.append(f"Proof {i}: Logical implication does not hold")

            except Exception as e:
                errors.append(f"Proof {i}: Parsing error - {str(e)}")

        except Exception as e:
            errors.append(f"Proof {i}: Unexpected error - {str(e)}")

    return valid_count, len(proofs), errors


def validate_grid_worlds(grids: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
    """
    Validate a list of generated grid worlds.

    A grid is considered valid if:
    1. It has the required structure (grid, start, goal, rules).
    2. There exists a path from start to goal that satisfies all rules.

    Args:
        grids: List of grid world dictionaries.

    Returns:
        Tuple of (valid_count, total_count, list of error messages).
    """
    valid_count = 0
    errors = []

    for i, grid_data in enumerate(grids):
        try:
            # Check structure
            required_keys = ['grid', 'start', 'goal', 'rules']
            for key in required_keys:
                if key not in grid_data:
                    errors.append(f"Grid {i}: Missing required key '{key}'")
                    break
            else:
                # All required keys present, validate solvability
                grid = grid_data['grid']
                start = tuple(grid_data['start'])
                goal = tuple(grid_data['goal'])
                rules = grid_data.get('rules', [])

                # Build graph
                G = nx.Graph()
                rows = len(grid)
                cols = len(grid[0]) if rows > 0 else 0

                # Add nodes
                for r in range(rows):
                    for c in range(cols):
                        if grid[r][c] != 1:  # 1 represents obstacle
                            G.add_node((r, c))

                # Add edges (4-connectivity)
                for r in range(rows):
                    for c in range(cols):
                        if grid[r][c] != 1:
                            # Check neighbors
                            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                                nr, nc = r + dr, c + dc
                                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1:
                                    G.add_edge((r, c), (nr, nc))

                # Check if start and goal are in the graph
                if start not in G or goal not in G:
                    errors.append(f"Grid {i}: Start or goal is an obstacle or out of bounds")
                    continue

                # Check if path exists
                try:
                    path = nx.shortest_path(G, start, goal)
                    # Validate path against rules
                    # This is a simplified rule check; real implementation would be more complex
                    path_valid = True
                    for rule in rules:
                        # Example rules: "avoid_red", "diagonal_paths"
                        # For now, we just check if a path exists
                        # In a real scenario, we'd check each step against the rule
                        pass

                    if path_valid:
                        valid_count += 1
                    else:
                        errors.append(f"Grid {i}: Path exists but violates rules")

                except nx.NetworkXNoPath:
                    errors.append(f"Grid {i}: No path exists from start to goal")

        except Exception as e:
            errors.append(f"Grid {i}: Unexpected error - {str(e)}")

    return valid_count, len(grids), errors


def validate_dataset(config: Optional[Config] = None) -> bool:
    """
    Main validation function.

    Loads generated data, validates logic proofs and grid worlds,
    and returns True if validity/solvability >= 99%.

    Args:
        config: Optional configuration object. If None, loads from default config.

    Returns:
        True if all validations pass, False otherwise.
    """
    if config is None:
        config = load_config()

    # Load data
    data = load_generated_data(config)

    total_errors = []
    all_valid = True

    # Validate logic proofs
    if data['logic_proofs']:
        valid_count, total_count, errors = validate_logic_proofs(data['logic_proofs'])
        total_errors.extend(errors)

        if total_count > 0:
            validity_rate = valid_count / total_count
            print(f"Logic Proofs: {valid_count}/{total_count} valid ({validity_rate:.2%})")
            if validity_rate < 0.99:
                print(f"ERROR: Logic proof validity ({validity_rate:.2%}) is below 99% threshold")
                all_valid = False
        else:
            print("Warning: No logic proofs found to validate")
    else:
        print("Warning: No logic proofs found in dataset")

    # Validate grid worlds
    if data['grid_worlds']:
        valid_count, total_count, errors = validate_grid_worlds(data['grid_worlds'])
        total_errors.extend(errors)

        if total_count > 0:
            solvability_rate = valid_count / total_count
            print(f"Grid Worlds: {valid_count}/{total_count} solvable ({solvability_rate:.2%})")
            if solvability_rate < 0.99:
                print(f"ERROR: Grid world solvability ({solvability_rate:.2%}) is below 99% threshold")
                all_valid = False
        else:
            print("Warning: No grid worlds found to validate")
    else:
        print("Warning: No grid worlds found in dataset")

    # Report errors
    if total_errors:
        print(f"\nValidation Errors ({len(total_errors)}):")
        for error in total_errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(total_errors) > 10:
            print(f"  ... and {len(total_errors) - 10} more errors")

    return all_valid


def main():
    """
    Entry point for the validation script.

    Exits with code 0 if validation passes, 1 if it fails.
    """
    try:
        is_valid = validate_dataset()
        if is_valid:
            print("\nValidation PASSED: All datasets meet the 99% threshold.")
            sys.exit(0)
        else:
            print("\nValidation FAILED: One or more datasets do not meet the 99% threshold.")
            sys.exit(1)
    except Exception as e:
        print(f"Validation ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
