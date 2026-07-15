"""
Oracle Parser for Qwen-AgentWorld.

Parses Qwen-AgentWorld source code to extract interaction logic including:
- Spatial relationships
- Temporal sequences
- Causal dependencies

This module implements the Ground Truth Oracle construction for independent
verification of agent behavior against the original environment simulator.
"""

import ast
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from utils.loaders import load_oracle_source_code
from utils.checksums import compute_string_sha256

logger = logging.getLogger(__name__)


@dataclass
class StateTransition:
    """Represents a single state transition in the oracle."""
    source_state: str
    action: str
    target_state: str
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    spatial_constraints: List[str] = field(default_factory=list)
    temporal_order: Optional[str] = None
    causal_dependencies: List[str] = field(default_factory=list)
    confidence: float = 1.0
    source_file: Optional[str] = None
    source_line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InteractionLogic:
    """Container for extracted interaction logic."""
    spatial_rules: List[Dict[str, Any]] = field(default_factory=list)
    temporal_rules: List[Dict[str, Any]] = field(default_factory=list)
    causal_rules: List[Dict[str, Any]] = field(default_factory=list)
    state_transitions: List[StateTransition] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spatial_rules": self.spatial_rules,
            "temporal_rules": self.temporal_rules,
            "causal_rules": self.causal_rules,
            "state_transitions": [st.to_dict() for st in self.state_transitions],
            "metadata": self.metadata
        }


class QwenAgentWorldParser:
    """
    Parser for Qwen-AgentWorld source code to extract interaction logic.

    This parser uses AST analysis and pattern matching to identify:
    - State transition definitions
    - Action preconditions and postconditions
    - Spatial constraints (position, distance, adjacency)
    - Temporal ordering (before, after, during)
    - Causal dependencies (cause-effect relationships)
    """

    def __init__(self, source_path: Optional[Union[str, Path]] = None):
        self.source_path = Path(source_path) if source_path else None
        self.transitions: List[StateTransition] = []
        self.spatial_patterns = [
            r"position\s*=\s*\(?\s*['\"]?(\w+)['\"]?\s*,?\s*['\"]?(\w+)['\"]?\s*\)?",
            r"distance\s*(?:between|from)\s+(\w+)\s+and\s+(\w+)\s*[:=]\s*(\d+)",
            r"adjacent\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)",
            r"in\s+(\w+)\s+of\s+(\w+)",
            r"at\s+(\w+)\s+location",
            r"move\s+(\w+)\s+to\s+(\w+)"
        ]
        self.temporal_patterns = [
            r"before\s+(\w+)\s+can\s+(\w+)",
            r"after\s+(\w+)\s+is\s+(\w+)",
            r"while\s+(\w+)\s+is\s+(\w+)",
            r"when\s+(\w+)\s+occurs",
            r"step\s+(\d+)\s+must\s+precede\s+step\s+(\d+)",
            r"sequence\s*:\s*(.+)"
        ]
        self.causal_patterns = [
            r"if\s+(\w+)\s+then\s+(\w+)",
            r"cause\s+(\w+)\s+to\s+(\w+)",
            r"leads\s+to\s+(\w+)",
            r"results\s+in\s+(\w+)",
            r"requires\s+(\w+)\s+for\s+(\w+)",
            r"enables\s+(\w+)\s+to\s+(\w+)"
        ]

    def parse_file(self, file_path: Union[str, Path]) -> InteractionLogic:
        """Parse a single Python file and extract interaction logic."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        logger.info(f"Parsing file: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            raise

        logic = InteractionLogic()
        logic.metadata["source_file"] = str(file_path)
        logic.metadata["checksum"] = compute_string_sha256(source_code)

        # Extract state transitions from class definitions and methods
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._extract_class_logic(node, source_code, logic)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                self._extract_function_logic(node, source_code, logic)
            elif isinstance(node, ast.Assign):
                self._extract_assignment_logic(node, source_code, logic)

        # Apply pattern-based extraction as fallback
        self._apply_pattern_extraction(source_code, logic)

        logger.info(f"Extracted {len(logic.state_transitions)} state transitions from {file_path}")
        return logic

    def _extract_class_logic(self, node: ast.ClassDef, source_code: str, logic: InteractionLogic):
        """Extract logic from class definitions (often state machines)."""
        class_name = node.name
        logger.debug(f"Analyzing class: {class_name}")

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name
                # Look for state transition patterns in method names
                if any(keyword in method_name for keyword in ['transition', 'move', 'change', 'update', 'apply']):
                    transition = self._parse_method_as_transition(item, source_code, class_name)
                    if transition:
                        logic.state_transitions.append(transition)

    def _extract_function_logic(self, node: ast.FunctionDef, source_code: str, logic: InteractionLogic):
        """Extract logic from function definitions."""
        func_name = node.name
        logger.debug(f"Analyzing function: {func_name}")

        # Check for state transition patterns
        if any(keyword in func_name for keyword in ['transition', 'move', 'change', 'update', 'apply', 'execute']):
            transition = self._parse_method_as_transition(node, source_code, None)
            if transition:
                logic.state_transitions.append(transition)

    def _extract_assignment_logic(self, node: ast.Assign, source_code: str, logic: InteractionLogic):
        """Extract logic from assignments (often state definitions)."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                # Check for spatial/temporal/causal assignments
                for pattern in self.spatial_patterns:
                    if re.search(pattern, ast.unparse(node) if hasattr(ast, 'unparse') else str(node)):
                        logic.spatial_rules.append({
                            "variable": var_name,
                            "pattern": pattern,
                            "line": node.lineno
                        })
                        break

    def _parse_method_as_transition(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
                                    source_code: str, class_name: Optional[str]) -> Optional[StateTransition]:
        """Parse a method as a state transition."""
        func_name = node.name

        # Extract docstring for metadata
        docstring = ast.get_docstring(node) or ""

        # Try to infer source state, action, target state from function name and args
        parts = func_name.split('_')

        # Heuristic: if name contains 'to', it might be a transition
        if 'to' in parts:
            idx = parts.index('to')
            if idx > 0 and idx < len(parts) - 1:
                source_state = '_'.join(parts[:idx])
                target_state = '_'.join(parts[idx+1:])
                action = func_name
            else:
                return None
        else:
            # Generic transition
            source_state = "unknown_source"
            target_state = f"after_{func_name}"
            action = func_name

        # Extract preconditions from arguments and docstring
        preconditions = []
        postconditions = []
        spatial_constraints = []
        causal_deps = []

        # Analyze arguments
        for arg in node.args.args:
            arg_name = arg.arg
            preconditions.append(f"has_{arg_name}")

        # Analyze docstring for patterns
        for pattern in self.spatial_patterns:
            matches = re.findall(pattern, docstring, re.IGNORECASE)
            if matches:
                spatial_constraints.extend([str(m) for m in matches])

        for pattern in self.causal_patterns:
            matches = re.findall(pattern, docstring, re.IGNORECASE)
            if matches:
                causal_deps.extend([str(m) for m in matches])

        # Check for return statements (postconditions)
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                if child.value:
                    try:
                        return_expr = ast.unparse(child.value) if hasattr(ast, 'unparse') else str(child.value)
                        postconditions.append(f"returns_{return_expr}")
                    except:
                        postconditions.append("returns_value")

        return StateTransition(
            source_state=source_state,
            action=action,
            target_state=target_state,
            preconditions=preconditions,
            postconditions=postconditions,
            spatial_constraints=spatial_constraints,
            causal_dependencies=causal_deps,
            source_file=class_name if class_name else None,
            source_line=node.lineno
        )

    def _apply_pattern_extraction(self, source_code: str, logic: InteractionLogic):
        """Apply regex pattern extraction as a fallback."""
        logger.debug("Applying pattern-based extraction")

        # Spatial patterns
        for pattern in self.spatial_patterns:
            matches = re.finditer(pattern, source_code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                logic.spatial_rules.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "groups": match.groups(),
                    "line": source_code[:match.start()].count('\n') + 1
                })

        # Temporal patterns
        for pattern in self.temporal_patterns:
            matches = re.finditer(pattern, source_code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                logic.temporal_rules.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "groups": match.groups(),
                    "line": source_code[:match.start()].count('\n') + 1
                })

        # Causal patterns
        for pattern in self.causal_patterns:
            matches = re.finditer(pattern, source_code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                logic.causal_rules.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "groups": match.groups(),
                    "line": source_code[:match.start()].count('\n') + 1
                })

    def parse_directory(self, dir_path: Union[str, Path]) -> InteractionLogic:
        """Parse all Python files in a directory recursively."""
        dir_path = Path(dir_path)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {dir_path}")

        logger.info(f"Parsing directory: {dir_path}")

        combined_logic = InteractionLogic()
        combined_logic.metadata["source_directory"] = str(dir_path)
        combined_logic.metadata["files_parsed"] = []

        py_files = list(dir_path.rglob("*.py"))
        logger.info(f"Found {len(py_files)} Python files")

        for py_file in py_files:
            # Skip test files and __init__.py
            if py_file.name.startswith('test_') or py_file.name == '__init__.py':
                continue

            try:
                file_logic = self.parse_file(py_file)
                combined_logic.spatial_rules.extend(file_logic.spatial_rules)
                combined_logic.temporal_rules.extend(file_logic.temporal_rules)
                combined_logic.causal_rules.extend(file_logic.causal_rules)
                combined_logic.state_transitions.extend(file_logic.state_transitions)
                combined_logic.metadata["files_parsed"].append(str(py_file))
            except Exception as e:
                logger.warning(f"Failed to parse {py_file}: {e}")
                continue

        combined_logic.metadata["total_transitions"] = len(combined_logic.state_transitions)
        combined_logic.metadata["total_spatial_rules"] = len(combined_logic.spatial_rules)
        combined_logic.metadata["total_temporal_rules"] = len(combined_logic.temporal_rules)
        combined_logic.metadata["total_causal_rules"] = len(combined_logic.causal_rules)

        return combined_logic


def parse_qwen_agentworld(source_path: Union[str, Path, None] = None,
                          output_path: Optional[Union[str, Path]] = None) -> InteractionLogic:
    """
    Main entry point for parsing Qwen-AgentWorld source code.

    Args:
        source_path: Path to the Qwen-AgentWorld source code (file or directory).
                    If None, attempts to load from default location or loader.
        output_path: Optional path to write the parsed oracle as JSON.

    Returns:
        InteractionLogic object containing extracted logic.
    """
    parser = QwenAgentWorldParser(source_path)

    if source_path:
        source_path = Path(source_path)
        if source_path.is_file():
            logic = parser.parse_file(source_path)
        elif source_path.is_dir():
            logic = parser.parse_directory(source_path)
        else:
            raise ValueError(f"Invalid source path: {source_path}")
    else:
        # Try to load via the loader utility
        try:
            source_data = load_oracle_source_code()
            if isinstance(source_data, dict) and 'content' in source_data:
                # Write to temp file and parse
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(source_data['content'])
                    temp_path = f.name
                logic = parser.parse_file(temp_path)
                Path(temp_path).unlink()
            else:
                raise ValueError("Loader did not return expected data format")
        except Exception as e:
            logger.error(f"Failed to load source via loader: {e}")
            raise

    # Write output if requested
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(logic.to_dict(), f, indent=2)

        logger.info(f"Wrote parsed oracle to {output_path}")

    return logic


def main():
    """CLI entry point for the parser."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description='Parse Qwen-AgentWorld source code')
    parser.add_argument('--source', '-s', type=str, required=True,
                       help='Path to source file or directory')
    parser.add_argument('--output', '-o', type=str,
                       help='Output path for JSON oracle (optional)')

    args = parser.parse_args()

    try:
        logic = parse_qwen_agentworld(args.source, args.output)
        print(f"Successfully parsed {len(logic.state_transitions)} state transitions")
        print(f"Spatial rules: {len(logic.spatial_rules)}")
        print(f"Temporal rules: {len(logic.temporal_rules)}")
        print(f"Causal rules: {len(logic.causal_rules)}")

        if args.output:
            print(f"Oracle written to: {args.output}")

    except Exception as e:
        logger.error(f"Parser failed: {e}")
        raise


if __name__ == "__main__":
    main()
