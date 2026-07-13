"""
Test coverage measurement via coverage.py.

Computes the percentage of test lines covered by the test suite for a given
code submission. Uses the coverage.py library to instrument execution and
report coverage statistics.

Output: Percentage 0-100% with at least 0.01 precision.
"""
import os
import sys
import json
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure coverage is available
try:
    import coverage
except ImportError:
    logger.error("coverage.py is not installed. Please install it via requirements.txt")
    raise

@dataclass
class CoverageResult:
    """Result of coverage measurement."""
    coverage_percent: float
    num_statements: int
    num_missed: int
    num_covered: int
    excluded_lines: int
    success: bool
    error_message: Optional[str] = None

def compute_coverage(
    source_code: str,
    test_code: str,
    timeout_seconds: int = 300
) -> CoverageResult:
    """
    Compute test coverage for a given source code against a test suite.
    
    Args:
        source_code: The Python source code to be tested.
        test_code: The test code (e.g., HumanEval test harness) to run.
        timeout_seconds: Maximum time allowed for test execution.
        
    Returns:
        CoverageResult with coverage percentage and statistics.
        
    Raises:
        RuntimeError: If coverage measurement fails unexpectedly.
    """
    if not source_code or not test_code:
        return CoverageResult(
            coverage_percent=0.0,
            num_statements=0,
            num_missed=0,
            num_covered=0,
            excluded_lines=0,
            success=False,
            error_message="Source code or test code is empty"
        )

    # Create a temporary directory for the test run
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Write source code to a file
        source_file = temp_path / "solution.py"
        source_file.write_text(source_code)
        
        # Write test code to a file
        test_file = temp_path / "test_solution.py"
        test_file.write_text(test_code)
        
        # Initialize coverage object
        cov = coverage.Coverage(
            source=[str(source_file)],
            branch=True,
            omit=["*/site-packages/*", "*/.venv/*"]
        )
        
        try:
            # Start coverage measurement
            cov.start()
            
            # Execute the test file
            # We use subprocess to ensure isolation and handle timeouts
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=str(temp_path),
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            
            # Stop coverage measurement
            cov.stop()
            cov.save()
            
            # Analyze results
            analysis = cov.analysis(str(source_file))
            
            num_statements = analysis[0]  # Total executable lines
            num_covered = len(analysis[2])  # Covered lines
            num_missed = num_statements - num_covered
            excluded_lines = len(analysis[3])  # Excluded lines (comments, etc.)
            
            # Calculate percentage
            if num_statements > 0:
                coverage_percent = (num_covered / num_statements) * 100.0
            else:
                coverage_percent = 0.0
            
            # Ensure precision and bounds
            coverage_percent = round(coverage_percent, 2)
            coverage_percent = max(0.0, min(100.0, coverage_percent))
            
            return CoverageResult(
                coverage_percent=coverage_percent,
                num_statements=num_statements,
                num_missed=num_missed,
                num_covered=num_covered,
                excluded_lines=excluded_lines,
                success=True
            )
            
        except subprocess.TimeoutExpired:
            return CoverageResult(
                coverage_percent=0.0,
                num_statements=0,
                num_missed=0,
                num_covered=0,
                excluded_lines=0,
                success=False,
                error_message=f"Test execution timed out after {timeout_seconds} seconds"
            )
        except Exception as e:
            # Log the error but return a failure result
            logger.error(f"Coverage measurement failed: {str(e)}")
            return CoverageResult(
                coverage_percent=0.0,
                num_statements=0,
                num_missed=0,
                num_covered=0,
                excluded_lines=0,
                success=False,
                error_message=str(e)
            )
        finally:
            # Clean up coverage data
            try:
                cov.erase()
            except Exception:
                pass

def analyze_code_quality(
    source_code: str,
    test_code: str,
    submission_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze code quality by computing test coverage.
    
    Args:
        source_code: The Python source code to analyze.
        test_code: The test code to run against the source.
        submission_id: Optional ID for logging purposes.
        
    Returns:
        Dictionary containing coverage metrics.
    """
    logger.info(f"Computing coverage for submission: {submission_id or 'unknown'}")
    
    result = compute_coverage(source_code, test_code)
    
    metrics = {
        "submission_id": submission_id,
        "coverage_percent": result.coverage_percent,
        "num_statements": result.num_statements,
        "num_missed": result.num_missed,
        "num_covered": result.num_covered,
        "excluded_lines": result.excluded_lines,
        "success": result.success,
        "error_message": result.error_message
    }
    
    if result.success:
        logger.info(
            f"Coverage: {result.coverage_percent:.2f}% "
            f"({result.num_covered}/{result.num_statements} lines)"
        )
    else:
        logger.warning(f"Coverage failed: {result.error_message}")
        
    return metrics

def main():
    """
    Command-line interface for coverage measurement.
    
    Usage:
        python code/quality/coverage.py --source <source_file> --test <test_file>
        
    Or with inline code:
        python code/quality/coverage.py --source-code "def add(a,b): return a+b" --test-code "assert add(1,2)==3"
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute test coverage for Python code")
    parser.add_argument("--source", help="Path to source file")
    parser.add_argument("--test", help="Path to test file")
    parser.add_argument("--source-code", help="Inline source code")
    parser.add_argument("--test-code", help="Inline test code")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--output", help="Output JSON file path")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.source and not args.source_code:
        parser.error("Either --source or --source-code must be provided")
    if not args.test and not args.test_code:
        parser.error("Either --test or --test-code must be provided")
    
    # Read source code
    if args.source:
        if not os.path.exists(args.source):
            logger.error(f"Source file not found: {args.source}")
            sys.exit(1)
        with open(args.source, 'r', encoding='utf-8') as f:
            source_code = f.read()
    else:
        source_code = args.source_code
        
    # Read test code
    if args.test:
        if not os.path.exists(args.test):
            logger.error(f"Test file not found: {args.test}")
            sys.exit(1)
        with open(args.test, 'r', encoding='utf-8') as f:
            test_code = f.read()
    else:
        test_code = args.test_code
        
    # Compute coverage
    result = analyze_code_quality(source_code, test_code)
    
    # Output results
    output_json = json.dumps(result, indent=2)
    print(output_json)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        logger.info(f"Results written to {args.output}")
        
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()