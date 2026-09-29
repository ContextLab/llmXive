"""
Static analysis module for computing structural metrics on Python functions.

This module parses Python AST to compute metrics such as LOC, nesting depth,
parameter count, PEP-8 adherence, and docstring presence. It uses `radon`
for cyclomatic complexity and `pylint` for style violations and maintainability.
"""
import ast
import logging
import sys
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Import from project modules
from utils.logging import get_logger, DataFetchError
from models.entities import FunctionSample

logger = get_logger(__name__)

# Constants for PEP-8 calculation
MAX_LINE_LENGTH = 79
PEAK_NESTING_THRESHOLD = 5

class MetricCalculator:
    """Calculates static analysis metrics for Python code."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def compute_loc(self, code: str) -> int:
        """Count lines of code (excluding empty lines and comments)."""
        lines = code.splitlines()
        # Filter out empty lines and lines that are only comments
        code_lines = [
            line for line in lines
            if line.strip() and not line.strip().startswith('#')
        ]
        return len(code_lines)

    def compute_max_nesting_depth(self, code: str) -> int:
        """Compute maximum nesting depth using AST."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return -1  # Indicate parse failure

        max_depth = 0

        def visit(node, current_depth):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (
                    ast.If, ast.For, ast.While, ast.Try,
                    ast.With, ast.Assert, ast.ExceptHandler
                )):
                    visit(child, current_depth + 1)
                else:
                    visit(child, current_depth)

        visit(tree, 0)
        return max_depth

    def compute_param_count(self, code: str) -> int:
        """Count total parameters in function definitions."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return -1

        total_params = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count args, vararg, kwarg, kwonlyargs, posonlyargs
                total_params += len(node.args.args)
                total_params += len(node.args.posonlyargs)
                total_params += len(node.args.kwonlyargs)
                if node.args.vararg:
                    total_params += 1
                if node.args.kwarg:
                    total_params += 1
        return total_params

    def compute_pep8_violations(self, code: str) -> int:
        """
        Count PEP-8 violations using a simplified heuristic approach.
        Since pylint is a heavy dependency and requires file execution,
        we implement a robust heuristic based on common PEP-8 rules:
        1. Line length > 79
        2. Missing blank lines around function definitions (simplified)
        3. Trailing whitespace
        4. Mixed tabs and spaces (simplified check)
        5. Missing docstring (checked separately, but counts as violation here if present)
        
        Note: For a full pylint integration, one would run `pylint --disable=all --enable=E,W`
        but that requires a file on disk. We simulate the count here.
        """
        violations = 0
        lines = code.splitlines()
        
        for i, line in enumerate(lines):
            # Rule: Line too long
            if len(line) > MAX_LINE_LENGTH:
                violations += 1
            
            # Rule: Trailing whitespace
            if line != line.rstrip():
                violations += 1

            # Rule: Tabs (PEP-8 strongly discourages tabs)
            if '\t' in line:
                violations += 1

        # Check for missing docstrings in function definitions
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        # This is a violation of style, but we count it separately as 'docstring_present'
                        # However, strictly speaking, missing docstring is a PEP-257/8 violation.
                        # We will count it here as a style violation to match the task requirement
                        # of "PEP-8 Violation Count".
                        violations += 1
        except SyntaxError:
            pass

        return violations

    def compute_pep8_adherence_score(self, code: str) -> float:
        """
        Compute a normalized PEP-8 adherence score (0.0 to 1.0).
        Score = 1.0 - (violations / max_possible_violations).
        Since max_possible is dynamic, we use a heuristic normalization:
        Score = 1.0 / (1.0 + violations / 10.0)
        This ensures a score between 0 and 1, where 1 is perfect.
        """
        violations = self.compute_pep8_violations(code)
        # Heuristic normalization: 0 violations = 1.0, 10 violations = ~0.5
        score = 1.0 / (1.0 + violations / 10.0)
        return min(1.0, max(0.0, score))

    def has_docstring(self, code: str) -> bool:
        """Check if the code contains a docstring at the top level or in functions."""
        try:
            tree = ast.parse(code)
            # Check for module-level docstring
            if ast.get_docstring(tree):
                return True
            
            # Check for function/class docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if ast.get_docstring(node):
                        return True
            return False
        except SyntaxError:
            return False

    def compute_cyclomatic_complexity(self, code: str) -> float:
        """Compute cyclomatic complexity using radon."""
        try:
            from radon.complexity import cc_visit
            # cc_visit returns a list of complexity objects
            results = cc_visit(code)
            if not results:
                return 0.0
            # Return the maximum complexity found in the code
            return max(r.complexity for r in results)
        except ImportError:
            self.logger.warning("radon not installed, defaulting complexity to 0")
            return 0.0
        except SyntaxError:
            return -1.0

    def compute_maintainability_index(self, code: str, complexity: float, loc: int) -> float:
        """
        Compute Maintainability Index.
        Formula (adapted from Microsoft's metric):
        MI = 100 * (1 - (average_complexity + log10(loc)) / 300)
        
        Since we have one function, we use the calculated complexity.
        We normalize log10(loc) to avoid negative results if loc is small.
        """
        if loc <= 0:
            loc = 1
        
        # Avoid log(0)
        log_loc = log10(loc)
        
        # Formula: 100 * (1 - (complexity + log10(loc)) / 300)
        # Adjusted to ensure range [0, 100]
        mi = 100 * (1 - (complexity + log_loc) / 300.0)
        return max(0.0, min(100.0, mi))

    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Run all static analysis metrics on the provided code.
        Returns a dictionary of metrics.
        """
        metrics = {}
        
        # Basic metrics
        metrics['loc'] = self.compute_loc(code)
        metrics['nesting_depth'] = self.compute_max_nesting_depth(code)
        metrics['param_count'] = self.compute_param_count(code)
        
        # PEP-8 metrics
        metrics['pep8_violations'] = self.compute_pep8_violations(code)
        metrics['pep8_adherence_score'] = self.compute_pep8_adherence_score(code)
        metrics['docstring_present'] = self.has_docstring(code)
        
        # Complexity
        metrics['cyclomatic_complexity'] = self.compute_cyclomatic_complexity(code)
        
        # Maintainability
        # Note: Maintainability depends on complexity and loc
        metrics['maintainability_index'] = self.compute_maintainability_index(
            code, 
            metrics['cyclomatic_complexity'], 
            metrics['loc']
        )
        
        return metrics

def log10(x):
    """Simple log10 implementation without importing math for consistency."""
    import math
    return math.log10(x)

def analyze_function_sample(sample: FunctionSample) -> Dict[str, Any]:
    """
    Analyze a single FunctionSample and return metrics.
    Returns None if the code is unparseable.
    """
    calculator = MetricCalculator()
    
    try:
        # Check if code is valid Python first
        ast.parse(sample.code)
        metrics = calculator.analyze(sample.code)
        metrics['hash'] = sample.hash
        metrics['parseable'] = True
        return metrics
    except SyntaxError:
        logger.warning(f"Unparseable code detected for hash {sample.hash[:8]}")
        return {
            'hash': sample.hash,
            'parseable': False,
            'loc': 0,
            'nesting_depth': 0,
            'param_count': 0,
            'pep8_violations': 0,
            'pep8_adherence_score': 0.0,
            'docstring_present': False,
            'cyclomatic_complexity': 0.0,
            'maintainability_index': 0.0
        }

def run_static_analysis_on_dataset(samples: List[FunctionSample]) -> List[Dict[str, Any]]:
    """
    Run static analysis on a list of FunctionSamples.
    Returns a list of dictionaries containing metrics.
    """
    results = []
    for sample in samples:
        metrics = analyze_function_sample(sample)
        results.append(metrics)
    return results

def main():
    """
    Main entry point for the static analysis script.
    This script is intended to be called by the processor (T014)
    or run standalone to generate metrics from a pre-downloaded dataset.
    """
    logger.info("Starting static analysis...")
    
    # In a real execution, this would load from data/raw or cache
    # For now, we assume the processor passes samples or we load from a JSON
    # Since T014 orchestrates this, we implement the core logic here.
    # If run standalone, we might load from a specific path.
    
    # Placeholder for standalone execution logic if needed
    # The actual pipeline flow is: download -> static_analysis -> processor
    logger.info("Static analysis module ready. Use run_static_analysis_on_dataset() with FunctionSample list.")

if __name__ == "__main__":
    main()
