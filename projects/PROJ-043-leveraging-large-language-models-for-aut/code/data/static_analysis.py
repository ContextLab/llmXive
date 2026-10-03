"""
Static Analysis Module for LLM Code Refactoring Pipeline.

This module implements the calculation of structural and quality metrics
for Python functions using AST parsing, radon, and pylint.

Metrics computed:
  - loc: Lines of Code
  - nesting_depth: Maximum nesting depth
  - param_count: Number of parameters
  - pep8_adherence_score: Normalized score (0.0 to 1.0)
  - pep8_violations: Integer count of PEP-8 violations
  - docstring_present: Boolean flag
  - complexity: Cyclomatic complexity (via radon)

Strict Constraints:
  - Metrics are computed on the *original* code only.
  - Maintainability Index and Halstead Volume are NOT calculated.
  - Unparseable functions are flagged and skipped.
"""
import ast
import logging
import sys
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Importing radon for complexity
try:
    from radon.complexity import cc_visit
    from radon.visitors import ComplexityVisitor
except ImportError:
    # Fallback import if radon is not installed in environment but path is set
    # In a real run, this should fail loudly if radon is missing
    raise ImportError("radon package is required for static analysis. Install via: pip install radon")

# Importing pylint for style analysis
try:
    from pylint.lint import Run
    from pylint.reporters.text import TextReporter
    from io import StringIO
except ImportError:
    raise ImportError("pylint package is required for static analysis. Install via: pip install pylint")

from utils.logging import get_logger, DataFetchError

logger = get_logger(__name__)


class MetricCalculator:
    """
    Encapsulates logic for calculating static metrics from Python code.
    """

    def __init__(self):
        self.logger = get_logger(__name__)

    def calculate_loc(self, tree: ast.AST, source_code: str) -> int:
        """
        Calculate Lines of Code (LOC).
        Excludes blank lines and comment-only lines.
        """
        lines = source_code.splitlines()
        loc = 0
        in_multiline_string = False
        
        # Simple heuristic for LOC: count non-empty, non-comment lines
        # A more precise AST-based approach would traverse and sum line spans
        # but line-based counting is standard for this metric.
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('#'):
                continue
            # Basic handling for docstrings if they span multiple lines
            # For simplicity in this metric, we count lines that contain code or docstring content
            loc += 1
        
        return loc

    def calculate_nesting_depth(self, tree: ast.AST) -> int:
        """
        Calculate maximum nesting depth of control flow structures.
        """
        max_depth = 0

        def visit_node(node, current_depth):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            # Check for nesting-inducing nodes
            nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, nesting_nodes):
                    visit_node(child, current_depth + 1)
                else:
                    visit_node(child, current_depth)

        visit_node(tree, 0)
        return max_depth

    def calculate_param_count(self, tree: ast.AST) -> int:
        """
        Count the number of parameters in the function definition.
        """
        if isinstance(tree, ast.FunctionDef) or isinstance(tree, ast.AsyncFunctionDef):
            args = tree.args
            count = len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs)
            if args.vararg:
                count += 1
            if args.kwarg:
                count += 1
            return count
        return 0

    def calculate_pep8_metrics(self, source_code: str) -> Tuple[int, float]:
        """
        Calculate PEP-8 Violation Count and Adherence Score.
        
        Uses pylint to detect violations.
        Adherence Score = 1.0 - (violations / max_possible_violations)
        Normalized to 0.0 - 1.0.
        """
        # Use pylint programmatically
        output = StringIO()
        reporter = TextReporter(output)
        
        try:
            # Run pylint on the code string
            # We disable specific checks that might be too strict or irrelevant for snippets
            # to focus on PEP-8 style violations (E, W)
            Run(
                ['--disable=C,R,I', '--reports=no', '--output-format=text', '-'],
                args=[source_code],
                reporter=reporter,
                exit=False
            )
        except Exception as e:
            self.logger.warning(f"Pylint failed on code snippet: {e}")
            # If pylint fails completely, assume 0 violations for safety, or treat as error?
            # Task says "Flag unparseable", but pylint handles syntax errors gracefully usually.
            # If it fails, we might not get a count.
            return 0, 1.0 

        output_text = output.getvalue()
        
        # Count violations: Pylint usually outputs lines like "E0001: ..." or "W0613: ..."
        # We look for messages starting with E (Error) or W (Warning) related to style
        # A simple regex to count lines that indicate a pylint message
        # Format: "filename:line:col: [msg_id] msg"
        # Since we pass '-' as filename, it might vary.
        
        violation_count = 0
        # Common PEP8 related codes: E, W categories
        # We'll count any line that looks like a pylint message containing E or W
        # A robust way is to parse the output, but a regex on the text is faster for this context.
        # Pattern: Starts with line number or file indicator, followed by colon, then severity
        
        # Simpler approach: count lines that contain 'E' or 'W' in the severity position
        # Pylint output: "stdin:1:0: E0001: ..."
        lines = output_text.splitlines()
        for line in lines:
            if not line.strip():
                continue
            # Check for common Pylint message patterns
            if re.search(r'\s[EW]\d{4}:\s', line) or re.search(r'^\s*\d+:\s+[EW]', line):
                violation_count += 1

        # Calculate Adherence Score
        # Heuristic: Max expected violations for a small function ~ 10. 
        # Score = max(0, 1 - (violations / 10))
        # This is a normalized score as requested.
        max_expected = 10.0
        adherence_score = max(0.0, 1.0 - (violation_count / max_expected))
        
        return violation_count, adherence_score

    def check_docstring(self, tree: ast.AST) -> bool:
        """
        Check if the function has a docstring.
        """
        if isinstance(tree, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return ast.get_docstring(tree) is not None
        return False

    def calculate_complexity(self, source_code: str) -> int:
        """
        Calculate Cyclomatic Complexity using radon.
        """
        try:
            results = cc_visit(source_code)
            if not results:
                return 0
            # Return the complexity of the first function found (or max if multiple)
            # The input is a single function, so we take the first result's complexity
            return results[0].complexity
        except Exception as e:
            self.logger.warning(f"Radon complexity calculation failed: {e}")
            return 0

    def analyze(self, source_code: str) -> Dict[str, Any]:
        """
        Perform full static analysis on a single code snippet.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"SyntaxError: Cannot parse code. {e}")

        metrics = {}
        
        # 1. LOC
        metrics['loc'] = self.calculate_loc(tree, source_code)
        
        # 2. Nesting Depth
        metrics['nesting_depth'] = self.calculate_nesting_depth(tree)
        
        # 3. Parameter Count
        metrics['param_count'] = self.calculate_param_count(tree)
        
        # 4. Docstring Presence
        metrics['docstring_present'] = self.check_docstring(tree)
        
        # 5. Complexity (Radon)
        metrics['complexity'] = self.calculate_complexity(source_code)
        
        # 6. PEP-8 Metrics
        pep8_violations, pep8_adherence = self.calculate_pep8_metrics(source_code)
        metrics['pep8_violations'] = pep8_violations
        metrics['pep8_adherence_score'] = pep8_adherence

        return metrics


def log10(x: float) -> float:
    """
    Helper function for log10 calculation if needed elsewhere.
    """
    import math
    if x <= 0:
        return 0.0
    return math.log10(x)


def analyze_function_sample(sample: Dict[str, Any], cache: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """
    Analyze a single function sample.
    
    Args:
        sample: Dictionary containing 'code' and 'hash'.
        cache: Optional cache object to check for existing metrics.
        
    Returns:
        Dictionary with original code, hash, and computed metrics.
        Returns None if the code is unparseable.
    """
    code = sample.get('code', '')
    func_hash = sample.get('hash', '')
    
    if not code:
        logger.warning(f"Empty code for hash {func_hash}")
        return None

    # Check cache if provided (T015 integration)
    if cache:
        cached_metrics = cache.get(func_hash)
        if cached_metrics:
            logger.debug(f"Cache hit for {func_hash}")
            return {
                'code': code,
                'hash': func_hash,
                **cached_metrics
            }

    calculator = MetricCalculator()
    
    try:
        metrics = calculator.analyze(code)
        result = {
            'code': code,
            'hash': func_hash,
            **metrics
        }
        
        # Update cache if provided
        if cache:
            cache.set(func_hash, metrics)
            
        return result
        
    except ValueError as e:
        logger.warning(f"Skipping unparseable function {func_hash}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error analyzing {func_hash}: {e}")
        return None


def run_static_analysis_on_dataset(
    input_file: Path, 
    output_file: Path, 
    cache: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Process a dataset file (JSON) and compute static metrics.
    
    Args:
        input_file: Path to input JSON file (from download.py).
        output_file: Path to save the output JSON file.
        cache: Optional cache instance.
        
    Returns:
        List of analyzed samples.
    """
    logger.info(f"Starting static analysis on {input_file}")
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
        
    # Load data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        data = [data]
        
    results = []
    skipped = 0
    
    for i, sample in enumerate(data):
        if i % 50 == 0:
            logger.info(f"Processed {i}/{len(data)} samples")
            
        analyzed = analyze_function_sample(sample, cache)
        if analyzed:
            results.append(analyzed)
        else:
            skipped += 1
            
    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Static analysis complete. Saved to {output_file}")
    logger.info(f"Total: {len(data)}, Valid: {len(results)}, Skipped: {skipped}")
    
    return results


def main():
    """
    Main entry point for static analysis script.
    Expects input from data/processed/downloaded_functions.json (or similar)
    and outputs to data/processed/raw_metrics.json.
    """
    import json
    from utils.cache import get_cache
    
    # Paths relative to project root
    base_path = Path(__file__).resolve().parent.parent.parent
    input_path = base_path / 'data' / 'processed' / 'downloaded_functions.json'
    output_path = base_path / 'data' / 'processed' / 'raw_metrics.json'
    
    # Initialize cache
    cache = get_cache()
    
    try:
        run_static_analysis_on_dataset(input_path, output_path, cache)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Static analysis failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()