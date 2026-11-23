"""
Unit tests for the verify_oracle_independence.py script.
Tests the static analysis logic to ensure it correctly detects violations.
"""

import ast
import tempfile
import os
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.verify_oracle_independence import (
    analyze_file,
    OracleIndependenceVisitor,
    ORACLE_MODULE,
    ORACLE_VALIDATION_METHODS,
    ORACLE_EXECUTION_METHODS
)

def test_no_violations_in_clean_file():
    """Test that a file with only validation calls passes."""
    clean_code = """
    from engines.oracle_policy import OraclePolicyEngine

    class TestEngine:
        def __init__(self):
            self.oracle = OraclePolicyEngine()

        def execute(self, workflow):
            result = self.oracle.validate(workflow, self.node)
            return result
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(clean_code)
        temp_path = f.name

    try:
        violations = analyze_file(temp_path)
        assert len(violations) == 0, f"Expected no violations, found: {violations}"
    finally:
        os.unlink(temp_path)

def test_violation_detected_execution_call():
    """Test that a file with execution logic is flagged."""
    violation_code = """
    from engines.oracle_policy import OraclePolicyEngine

    class TestEngine:
        def __init__(self):
            self.oracle = OraclePolicyEngine()

        def execute(self, workflow):
            # This should be a violation
            self.oracle.execute_policy(workflow)
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(violation_code)
        temp_path = f.name

    try:
        violations = analyze_file(temp_path)
        assert len(violations) == 1, f"Expected 1 violation, found: {len(violations)}"
        assert "VIOLATION" in violations[0], "Violation message should contain 'VIOLATION'"
        assert "execute_policy" in violations[0], "Violation should mention the execution method"
    finally:
        os.unlink(temp_path)

def test_violation_detected_direct_execution_import():
    """Test that direct import of execution functions is flagged."""
    violation_code = """
    from engines.oracle_policy import execute_policy

    def my_logic(workflow):
        execute_policy(workflow)
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(violation_code)
        temp_path = f.name

    try:
        violations = analyze_file(temp_path)
        assert len(violations) == 1, f"Expected 1 violation, found: {len(violations)}"
        assert "execute_policy" in violations[0], "Violation should mention the execution function"
    finally:
        os.unlink(temp_path)

def test_syntax_error_handling():
    """Test that syntax errors are handled gracefully."""
    invalid_code = """
    from engines.oracle_policy import OraclePolicyEngine
    def broken(:
        pass
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(invalid_code)
        temp_path = f.name

    try:
        violations = analyze_file(temp_path)
        assert len(violations) == 1, f"Expected 1 error, found: {len(violations)}"
        assert "Syntax error" in violations[0], "Should report syntax error"
    finally:
        os.unlink(temp_path)

def test_file_not_found():
    """Test that missing files are reported."""
    violations = analyze_file("nonexistent_file.py")
    assert len(violations) == 1, "Should report file not found"
    assert "not found" in violations[0].lower(), "Should mention file not found"

def test_ast_visitor_initialization():
    """Test the AST visitor initialization."""
    visitor = OracleIndependenceVisitor("test.py")
    assert visitor.filename == "test.py"
    assert len(visitor.violations) == 0
    assert len(visitor.imports) == 0
    assert len(visitor.imported_names) == 0