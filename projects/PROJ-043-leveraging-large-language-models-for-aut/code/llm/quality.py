"""
Quality Metrics and Delta Calculation Module.

Calculates cyclomatic complexity and pylint scores for original, refactored,
and baseline code. Computes deltas and validates baseline identity.
"""

import ast
import logging
import sys
from typing import Dict, Any, List, Optional, Tuple

from radon.complexity import cc_visit
from radon.visitors import ComplexityVisitor
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from io import StringIO

from models.entities import FunctionSample, MetricDelta
from utils.logging import get_logger, ValidationFailedError, LLMRefactoringError

logger = get_logger(__name__)


def calculate_cyclomatic_complexity(code: str) -> float:
    """
    Calculate the cyclomatic complexity of a code snippet using radon.

    Args:
        code: Python code string.

    Returns:
        The total cyclomatic complexity (sum of all functions/classes).
        Returns 0.0 if parsing fails.
    """
    if not code or not code.strip():
        return 0.0

    try:
        # Parse the AST to ensure it's valid Python before calculating complexity
        ast.parse(code)
        
        # radon cc_visit returns a list of Block objects
        results = cc_visit(code)
        total_complexity = sum(block.complexity for block in results)
        return float(total_complexity)
    except SyntaxError:
        logger.warning("Syntax error in code during complexity calculation.")
        return 0.0
    except Exception as e:
        logger.warning(f"Error calculating complexity: {e}")
        return 0.0


def calculate_pylint_score(code: str) -> float:
    """
    Calculate the pylint score (0-10) for a code snippet.

    Args:
        code: Python code string.

    Returns:
        The pylint score as a float. Returns 0.0 if calculation fails.
    """
    if not code or not code.strip():
        return 0.0

    try:
        # Redirect stdout to capture pylint output
        output = StringIO()
        reporter = TextReporter(output)
        
        # Run pylint on the code string
        # We use a temporary file approach or pass code directly via stdin if supported,
        # but pylint.lint.Run usually expects file paths. 
        # To avoid file I/O, we can write to a temp file or use a workaround.
        # Given constraints, we'll use a temporary file approach for robustness.
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            # Run pylint with specific options to suppress non-score output if needed
            # We capture the score from the summary line
            results = Run(
                [temp_path, "--score=yes", "--msg-template={score}"], 
                reporter=reporter, 
                do_exit=False
            )
            
            # The score is usually stored in the reporter or results
            # Accessing the score directly from the Linter object if available
            # pylint.lint.Run creates a Linter instance
            linter = results.linter
            score = linter.stats.global_note if hasattr(linter.stats, 'global_note') else 0.0
            
            if score is None:
                score = 0.0
                
            return float(score)
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        logger.warning(f"Error calculating pylint score: {e}")
        return 0.0


def calculate_metrics(code: str) -> Dict[str, float]:
    """
    Calculate all structural metrics for a given code snippet.

    Args:
        code: Python code string.

    Returns:
        Dictionary with 'complexity' and 'pylint_score'.
    """
    return {
        "complexity": calculate_cyclomatic_complexity(code),
        "pylint_score": calculate_pylint_score(code)
    }


def compute_deltas(
    original_metrics: Dict[str, float],
    refactored_metrics: Dict[str, float],
    baseline_metrics: Dict[str, float]
) -> Dict[str, float]:
    """
    Compute deltas between original, refactored, and baseline metrics.

    Args:
        original_metrics: Metrics for the original code.
        refactored_metrics: Metrics for the refactored code.
        baseline_metrics: Metrics for the baseline (identity) code.

    Returns:
        Dictionary containing deltas:
        - complexity_delta: refactored - original
        - pylint_delta: refactored - original
        - baseline_complexity_delta: baseline - original
        - baseline_pylint_delta: baseline - original
    """
    deltas = {}
    
    # Refactoring deltas
    deltas["complexity_delta"] = (
        refactored_metrics["complexity"] - original_metrics["complexity"]
    )
    deltas["pylint_delta"] = (
        refactored_metrics["pylint_score"] - original_metrics["pylint_score"]
    )
    
    # Baseline deltas (should be ~0 for identity)
    deltas["baseline_complexity_delta"] = (
        baseline_metrics["complexity"] - original_metrics["complexity"]
    )
    deltas["baseline_pylint_delta"] = (
        baseline_metrics["pylint_score"] - original_metrics["pylint_score"]
    )
    
    return deltas


def validate_baseline_identity(deltas: Dict[str, float], threshold: float = 0.01) -> None:
    """
    Validate that the baseline (identity transformation) produces negligible deltas.

    Args:
        deltas: Dictionary containing baseline deltas.
        threshold: Maximum allowed absolute delta value.

    Raises:
        ValueError: If |baseline_delta| >= threshold for any metric.
    """
    baseline_complexity_delta = deltas.get("baseline_complexity_delta", 0.0)
    baseline_pylint_delta = deltas.get("baseline_pylint_delta", 0.0)

    if abs(baseline_complexity_delta) >= threshold:
        raise ValidationFailedError(
            f"Baseline validation failed: |complexity_delta| = {abs(baseline_complexity_delta):.4f} >= {threshold}. "
            "Identity transformation did not preserve complexity."
        )

    if abs(baseline_pylint_delta) >= threshold:
        raise ValidationFailedError(
            f"Baseline validation failed: |pylint_delta| = {abs(baseline_pylint_delta):.4f} >= {threshold}. "
            "Identity transformation did not preserve pylint score."
        )

    logger.info(f"Baseline validation passed: complexity_delta={baseline_complexity_delta:.4f}, pylint_delta={baseline_pylint_delta:.4f}")


def analyze_function_quality(
    original: FunctionSample,
    refactored_code: Optional[str],
    baseline_code: str
) -> Tuple[Dict[str, Any], bool, Optional[str]]:
    """
    Analyze quality metrics for a function sample including original, refactored, and baseline.

    Args:
        original: The original FunctionSample.
        refactored_code: The refactored code string (may be None if refactoring failed).
        baseline_code: The baseline code string (identity).

    Returns:
        Tuple of:
        - metrics_dict: Dictionary with all metrics and deltas.
        - is_valid: Boolean indicating if analysis succeeded and baseline is valid.
        - error_message: Error string if validation failed, None otherwise.
    """
    # Calculate metrics for original
    original_metrics = calculate_metrics(original.code)
    
    # Calculate metrics for baseline
    baseline_metrics = calculate_metrics(baseline_code)
    
    # Calculate metrics for refactored (if available)
    refactored_metrics = {"complexity": 0.0, "pylint_score": 0.0}
    refactoring_success = False
    
    if refactored_code and refactored_code.strip():
        try:
            # Verify it's valid Python
            ast.parse(refactored_code)
            refactored_metrics = calculate_metrics(refactored_code)
            refactoring_success = True
        except SyntaxError:
            logger.warning("Refactored code has syntax errors. Marking as failed.")
            refactoring_success = False
        except Exception as e:
            logger.warning(f"Error analyzing refactored code: {e}")
            refactoring_success = False
    
    # Compute deltas
    deltas = compute_deltas(original_metrics, refactored_metrics, baseline_metrics)
    
    # Validate baseline identity
    try:
        validate_baseline_identity(deltas)
        baseline_valid = True
    except ValidationFailedError as e:
        baseline_valid = False
        logger.error(f"Baseline validation error: {e}")
        return {
            "original": original_metrics,
            "refactored": refactored_metrics if refactoring_success else None,
            "baseline": baseline_metrics,
            "deltas": deltas,
            "refactoring_success": refactoring_success,
            "baseline_valid": False
        }, False, str(e)
    
    return {
        "original": original_metrics,
        "refactored": refactored_metrics if refactoring_success else None,
        "baseline": baseline_metrics,
        "deltas": deltas,
        "refactoring_success": refactoring_success,
        "baseline_valid": True
    }, True, None


def main():
    """
    Main entry point for quality analysis.
    This function is intended to be called by the pipeline (T022).
    """
    logger.info("Quality analysis module loaded. Use analyze_function_quality for processing.")


if __name__ == "__main__":
    main()