"""
Integration test for simplification of a batch of functions.

This test verifies the end-to-end flow of the simplification pipeline:
1. Loading a batch of validated functions from data/processed/validated_functions.jsonl
2. Processing them through the simplification logic (mocked for speed/reliability in CI)
3. Verifying output validity: valid Python syntax, distinct from input, generated within limits.

Note: Since T022 (loader.py) and T023 (simplify.py) are not yet implemented,
this test uses a deterministic mock simplification strategy that satisfies the
structural requirements (valid AST, distinct code) without requiring the actual
LLM to be loaded. This allows the integration test to run in the CI environment
while the model components are being developed.
"""

import ast
import json
import os
import sys
import time
import tempfile
from pathlib import Path

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock imports for components not yet implemented
# In a real scenario, these would be imported from code/models/
from unittest.mock import MagicMock, patch

def mock_simplify_function(original_code: str, max_time_seconds: float = 60.0) -> str:
    """
    Mock simplification function that returns valid, distinct Python code.
    
    This simulates the behavior of the LLM simplification logic for testing purposes.
    It adds a harmless comment to ensure the code is distinct but syntactically valid.
    """
    try:
        # Verify input is valid Python
        ast.parse(original_code)
    except SyntaxError:
        raise ValueError("Input code is not valid Python")
    
    # Simple transformation: add a comment and re-format (ast unparse if available, else string manipulation)
    # For compatibility with older Python, we'll do a simple string operation
    # that ensures the code is distinct but valid.
    
    # Check if code has a docstring or comments to append to
    lines = original_code.split('\n')
    if lines and lines[0].strip().startswith('"""'):
        # Find end of docstring
        end_idx = 1
        while end_idx < len(lines) and not lines[end_idx].strip().endswith('"""'):
            end_idx += 1
        if end_idx < len(lines):
            lines[end_idx] = lines[end_idx].rstrip('"""') + '  # Simplified by integration test' + '\n' + '"""'
        else:
            lines.append('# Simplified by integration test')
    else:
        lines.insert(0, '# Simplified by integration test')
    
    simplified_code = '\n'.join(lines)
    
    # Verify output is valid Python
    try:
        ast.parse(simplified_code)
    except SyntaxError as e:
        raise ValueError(f"Generated code is not valid Python: {e}")
    
    # Ensure it's distinct from input
    if simplified_code == original_code:
        raise ValueError("Generated code must be distinct from input")
        
    return simplified_code

def run_batch_simplification(input_file: Path, output_file: Path, max_time_per_func: float = 60.0) -> dict:
    """
    Simulate the batch simplification process.
    
    Args:
        input_file: Path to validated_functions.jsonl
        output_file: Path to write simplified_functions.jsonl
        max_time_per_func: Maximum time allowed per function
        
    Returns:
        Dictionary with processing statistics
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
        
    results = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "timeouts": 0,
        "errors": []
    }
    
    processed_functions = []
    
    with open(input_file, 'r', encoding='utf-8') as f_in:
        for line in f_in:
            if not line.strip():
                continue
                
            func_data = json.loads(line)
            original_code = func_data.get('code', '')
            
            if not original_code:
                results["errors"].append({"type": "empty_code", "data": func_data.get('id', 'unknown')})
                results["failed"] += 1
                continue
                
            results["total"] += 1
            start_time = time.time()
            
            try:
                # Check time budget
                if time.time() - start_time > max_time_per_func:
                    results["timeouts"] += 1
                    results["errors"].append({
                        "type": "timeout", 
                        "id": func_data.get('id', 'unknown'),
                        "elapsed": time.time() - start_time
                    })
                    continue
                    
                simplified_code = mock_simplify_function(original_code, max_time_per_func)
                elapsed = time.time() - start_time
                
                if elapsed > max_time_per_func:
                    results["timeouts"] += 1
                    results["errors"].append({
                        "type": "timeout", 
                        "id": func_data.get('id', 'unknown'),
                        "elapsed": elapsed
                    })
                    continue
                    
                # Create output record
                result_record = {
                    "id": func_data.get('id', 'unknown'),
                    "original_code": original_code,
                    "simplified_code": simplified_code,
                    "elapsed_time": elapsed,
                    "status": "success"
                }
                processed_functions.append(result_record)
                results["success"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "type": "exception",
                    "id": func_data.get('id', 'unknown'),
                    "error": str(e)
                })
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for func in processed_functions:
            f_out.write(json.dumps(func) + '\n')
            
    return results

@pytest.fixture
def sample_validated_functions(tmp_path):
    """Create a sample validated_functions.jsonl file for testing."""
    sample_data = [
        {
            "id": "func_001",
            "code": "def add(a, b):\n    return a + b",
            "stratum": "0-10",
            "loc": 2
        },
        {
            "id": "func_002",
            "code": "def multiply(x, y):\n    \"\"\"Multiply two numbers.\"\"\"\n    return x * y",
            "stratum": "11-50",
            "loc": 3
        },
        {
            "id": "func_003",
            "code": "def complex_calc(a, b, c):\n    # Complex calculation\n    temp = a * b\n    result = temp + c\n    return result / (b + 1)",
            "stratum": "11-50",
            "loc": 5
        },
        {
            "id": "func_004",
            "code": "def simple_subtract(p, q):\n    return p - q",
            "stratum": "0-10",
            "loc": 2
        },
        {
            "id": "func_005",
            "code": "def divide(numerator, denominator):\n    if denominator == 0:\n        raise ValueError(\"Cannot divide by zero\")\n    return numerator / denominator",
            "stratum": "11-50",
            "loc": 5
        }
    ]
    
    input_file = tmp_path / "validated_functions.jsonl"
    with open(input_file, 'w', encoding='utf-8') as f:
        for item in sample_data:
            f.write(json.dumps(item) + '\n')
            
    return input_file

@pytest.fixture
def output_file(tmp_path):
    """Create a temporary output file path."""
    return tmp_path / "simplified_functions.jsonl"

class TestSimplificationIntegration:
    """Integration tests for the simplification batch processing."""

    def test_batch_simplification_creates_output_file(self, sample_validated_functions, output_file):
        """Verify that batch simplification creates the output file."""
        results = run_batch_simplification(sample_validated_functions, output_file)
        
        assert output_file.exists(), "Output file was not created"
        assert results["success"] > 0, "No functions were successfully simplified"

    def test_batch_simplification_validates_output_syntax(self, sample_validated_functions, output_file):
        """Verify that all generated code is valid Python syntax."""
        results = run_batch_simplification(sample_validated_functions, output_file)
        
        assert results["success"] > 0, "No functions were successfully simplified"
        
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                simplified_code = record["simplified_code"]
                
                # Verify syntax
                try:
                    ast.parse(simplified_code)
                except SyntaxError as e:
                    pytest.fail(f"Generated code has invalid syntax: {e}")

    def test_batch_simplification_produces_distinct_code(self, sample_validated_functions, output_file):
        """Verify that generated code is distinct from input."""
        results = run_batch_simplification(sample_validated_functions, output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                original = record["original_code"]
                simplified = record["simplified_code"]
                
                assert original != simplified, f"Code must be distinct: {record['id']}"

    def test_batch_simplification_timing_constraints(self, sample_validated_functions, output_file):
        """Verify that processing respects time limits."""
        start_time = time.time()
        results = run_batch_simplification(sample_validated_functions, output_file, max_time_per_func=5.0)
        total_time = time.time() - start_time
        
        # With 5 functions and 5s limit each, total should be reasonable (< 30s)
        assert total_time < 30.0, f"Processing took too long: {total_time}s"
        
        # Verify no timeouts occurred in this small batch
        assert results["timeouts"] == 0, "Unexpected timeouts in test batch"

    def test_batch_simplification_handles_empty_code(self, tmp_path):
        """Verify that empty code entries are handled gracefully."""
        input_file = tmp_path / "invalid_functions.jsonl"
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps({"id": "empty", "code": "", "stratum": "0-10"}) + '\n')
            f.write(json.dumps({"id": "valid", "code": "def x(): pass", "stratum": "0-10"}) + '\n')
            
        output_file = tmp_path / "output.jsonl"
        results = run_batch_simplification(input_file, output_file)
        
        assert results["failed"] == 1, "Empty code should fail"
        assert results["success"] == 1, "Valid code should succeed"
        assert results["total"] == 2, "Should process 2 items"

    def test_batch_simplification_error_logging(self, sample_validated_functions, output_file):
        """Verify that errors are properly logged in the results."""
        results = run_batch_simplification(sample_validated_functions, output_file)
        
        # Should have no errors in our clean sample
        assert len(results["errors"]) == 0, f"Unexpected errors: {results['errors']}"
        
        # Verify error structure if any exist
        for error in results["errors"]:
            assert "type" in error, "Error must have type"
            assert "id" in error, "Error must have id"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])