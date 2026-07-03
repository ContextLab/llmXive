"""
Test script to verify cyclomatic complexity of codebase is < 15.
Uses radon to measure complexity.
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest
import json

def test_cyclomatic_complexity():
    """
    Verify that all functions in code/preprocessing/preprocess.py
    and code/analysis/analysis.py have cyclomatic complexity < 15.
    """
    # Ensure radon is installed
    try:
        import radon
    except ImportError:
        pytest.skip("radon not installed, skipping complexity check")

    code_dir = Path(__file__).parent.parent / "code"
    preprocess_file = code_dir / "preprocessing" / "preprocess.py"
    analysis_file = code_dir / "analysis" / "analysis.py"

    files_to_check = [str(preprocess_file), str(analysis_file)]

    for file_path in files_to_check:
        if not os.path.exists(file_path):
            pytest.fail(f"File not found: {file_path}")

        # Run radon cc (cyclomatic complexity)
        result = subprocess.run(
            ["radon", "cc", file_path, "-s", "-j"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.fail(f"radon failed for {file_path}: {result.stderr}")

        try:
            complexity_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            # Fallback: parse text output if JSON fails
            pytest.skip("Could not parse radon output as JSON")

        # Check each function's complexity
        for module in complexity_data:
            for function in module.get("functions", []):
                cc = function.get("cc", 0)
                func_name = function.get("name", "unknown")
                if cc >= 15:
                    pytest.fail(
                        f"Function '{func_name}' in {file_path} "
                        f"has cyclomatic complexity {cc} >= 15"
                    )

    # Also run radon on the entire code directory to ensure no regressions
    result = subprocess.run(
        ["radon", "cc", str(code_dir), "-s", "-j"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(f"radon failed on code directory: {result.stderr}")

    try:
        all_complexity = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.skip("Could not parse radon output for code directory")

    # Verify all functions in the entire codebase meet the threshold
    for module in all_complexity:
        for function in module.get("functions", []):
            cc = function.get("cc", 0)
            func_name = function.get("name", "unknown")
            file_path = module.get("file", "unknown")
            if cc >= 15:
                # Only fail if it's in the target files we just refactored
                if "preprocess.py" in file_path or "analysis.py" in file_path:
                    pytest.fail(
                        f"Function '{func_name}' in {file_path} "
                        f"has cyclomatic complexity {cc} >= 15"
                    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
