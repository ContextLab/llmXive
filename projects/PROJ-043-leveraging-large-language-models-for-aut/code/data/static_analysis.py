"""
Static Analysis Module for LLM Code Refactoring Research.

Computes structural metrics (LOC, nesting depth, parameter count, docstring presence)
and style metrics (cyclomatic complexity via radon, PEP-8 adherence via pylint)
on the original Python code to serve as predictors for refactoring success.
"""
import ast
import logging
import sys
from typing import Dict, Any, List, Optional, Tuple

# Local imports matching the API surface
from utils.logging import get_logger, DataFetchError
from models.entities import FunctionSample

# Initialize logger
logger = get_logger(__name__)


class MetricCalculator:
    """Calculates static metrics for Python code snippets."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def calculate_basic_metrics(self, code: str) -> Dict[str, Any]:
        """
        Parse AST and compute basic structural metrics:
        - lines_of_code (LOC)
        - max_nesting_depth
        - parameter_count
        - has_docstring (boolean)

        Returns a dictionary with these metrics.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in code snippet: {e}")
            return {
                "lines_of_code": 0,
                "max_nesting_depth": 0,
                "parameter_count": 0,
                "has_docstring": False,
                "parse_error": str(e)
            }

        # 1. Lines of Code (LOC)
        # Count non-empty, non-comment lines
        lines = code.splitlines()
        loc = 0
        in_multiline_string = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Toggle multiline string state if not already in one
                if not in_multiline_string:
                    in_multiline_string = True
                    # If the same line closes it (rare but possible)
                    if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                        in_multiline_string = False
                else:
                    in_multiline_string = False
                continue
            if stripped.startswith("#"):
                continue
            if in_multiline_string:
                continue
            loc += 1

        # 2. Max Nesting Depth
        max_depth = self._get_max_nesting_depth(tree)

        # 3. Parameter Count (for functions/methods)
        # We assume the snippet is a function definition.
        # If it's a class or module, we look for the first function def found.
        param_count = 0
        has_docstring = False
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count parameters (excluding 'self' or 'cls' for methods)
                args = node.args
                params = len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs)
                if args.vararg:
                    params += 1
                if args.kwarg:
                    params += 1
                
                # Heuristic: if the first arg is 'self' or 'cls', don't count it
                if args.args and args.args[0].arg in ('self', 'cls'):
                    params -= 1
                
                param_count = max(param_count, params)

                # Check for docstring
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    has_docstring = True
                break # Only analyze the first top-level function found

        return {
            "lines_of_code": loc,
            "max_nesting_depth": max_depth,
            "parameter_count": param_count,
            "has_docstring": has_docstring
        }

    def _get_max_nesting_depth(self, tree: ast.AST) -> int:
        """Recursively find the maximum nesting depth of control flow structures."""
        max_depth = 0
        
        def walk(node: ast.AST, current_depth: int):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, 
                                      ast.AsyncFor, ast.AsyncWith, ast.Try)):
                    walk(child, current_depth + 1)
                else:
                    walk(child, current_depth)

        walk(tree, 0)
        return max_depth

    def calculate_cyclomatic_complexity(self, code: str) -> float:
        """
        Calculate cyclomatic complexity using radon.
        Returns the sum of complexities of all functions in the snippet,
        or 0 if radon is unavailable or parsing fails.
        """
        try:
            from radon.complexity import cc_visit
            results = cc_visit(code)
            # Sum complexity of all functions found
            total_complexity = sum(func.complexity for func in results)
            return float(total_complexity)
        except ImportError:
            self.logger.error("radon library not installed. Please install it via requirements.txt")
            raise
        except Exception as e:
            self.logger.warning(f"Radon failed to analyze code: {e}")
            return 0.0

    def calculate_pep8_score(self, code: str) -> float:
        """
        Calculate PEP-8 adherence score using pylint.
        Returns a normalized score (0.0 to 10.0).
        Higher is better.
        """
        try:
            from pylint.lint import Run
            from pylint.reporters.text import TextReporter
            import io
            import sys

            # Capture output
            output = io.StringIO()
            reporter = TextReporter(output)
            
            # Run pylint on the code string
            # We use a temporary file approach or disable specific checks to avoid file system issues
            # pylint's Run can take a list of modules/files. For string code, we write to a temp file or use stdin trickery.
            # The most robust way for a string is to use pylint's API directly or write to a temp file.
            # Let's write to a temporary file to ensure pylint runs correctly.
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name

            try:
                # Disable specific checks that might be noisy for snippets (e.g., missing docstring if we already check it, file length)
                # We want a score based on style (E, W, C, R).
                # We run pylint and capture the score.
                Run(
                    [temp_path, 
                     "--disable=all", 
                     "--enable=E,W,C,R", # Enable Error, Warning, Convention, Refactor
                     "--reports=n", 
                     "--score=yes"], 
                    reporter=reporter, 
                    do_exit=False
                )
                
                output_str = output.getvalue()
                # Pylint output usually ends with "rated at X.X/10"
                # We can parse the last line or the score from the reporter
                # The TextReporter doesn't store the score easily in a variable, so we parse.
                lines = output_str.split('\n')
                for line in reversed(lines):
                    if "rated at" in line:
                        # Format: "rated at X.X/10"
                        try:
                            score_str = line.split("rated at")[1].strip().split("/")[0]
                            return float(score_str)
                        except (ValueError, IndexError):
                            return 0.0
                
                # If we can't parse, assume 0 (failure to analyze)
                self.logger.warning("Could not parse pylint score from output.")
                return 0.0

            finally:
                os.unlink(temp_path)

        except ImportError:
            self.logger.error("pylint library not installed. Please install it via requirements.txt")
            raise
        except Exception as e:
            self.logger.warning(f"Pylint failed to analyze code: {e}")
            return 0.0

    def compute_all_metrics(self, code: str) -> Dict[str, Any]:
        """
        Computes all metrics for a given code snippet.
        Returns a dictionary with:
        - basic_metrics (dict): LOC, nesting, params, docstring
        - cyclomatic_complexity (float)
        - pep8_score (float)
        - is_parseable (bool)
        """
        basic = self.calculate_basic_metrics(code)
        
        is_parseable = "parse_error" not in basic
        
        if not is_parseable:
            return {
                **basic,
                "cyclomatic_complexity": 0.0,
                "pep8_score": 0.0,
                "is_parseable": False
            }

        try:
            cc = self.calculate_cyclomatic_complexity(code)
            pep8 = self.calculate_pep8_score(code)
        except Exception as e:
            self.logger.error(f"Error calculating advanced metrics: {e}")
            # If advanced metrics fail, we still return basic ones but flag the error
            cc = 0.0
            pep8 = 0.0

        return {
            **basic,
            "cyclomatic_complexity": cc,
            "pep8_score": pep8,
            "is_parseable": True
        }


def analyze_function_sample(sample: FunctionSample) -> Dict[str, Any]:
    """
    Analyzes a single FunctionSample and returns metrics.
    """
    calculator = MetricCalculator()
    metrics = calculator.compute_all_metrics(sample.code)
    
    # Attach the hash for tracking
    metrics['function_hash'] = sample.hash
    metrics['original_code'] = sample.code # Keep original code for reference if needed, though usually we store metrics only
    
    return metrics


def run_static_analysis_on_dataset(samples: List[FunctionSample], output_path: str) -> List[Dict[str, Any]]:
    """
    Runs static analysis on a list of FunctionSamples.
    Filters out unparseable functions (logs warning) and returns results.
    Saves results to output_path if provided.
    """
    results = []
    unparseable_count = 0
    
    logger.info(f"Starting static analysis on {len(samples)} samples...")
    
    for i, sample in enumerate(samples):
        if i % 50 == 0:
            logger.info(f"Processed {i}/{len(samples)} samples...")
        
        try:
            metrics = analyze_function_sample(sample)
            if not metrics['is_parseable']:
                unparseable_count += 1
                logger.warning(f"Sample {sample.hash} is unparseable. Skipping.")
                continue
            
            results.append(metrics)
            
        except Exception as e:
            logger.error(f"Unexpected error analyzing sample {sample.hash}: {e}", exc_info=True)
            continue

    logger.info(f"Analysis complete. {len(results)} valid samples, {unparseable_count} unparseable.")
    
    if output_path:
        import json
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")
    
    return results


def main():
    """
    Main entry point for the static analysis script.
    Expects to be run after download.py has populated data/processed/raw_metrics.json 
    OR to be called by processor.py.
    
    For this task, we assume the data is already fetched by T012 (download.py)
    and we are processing the raw downloaded data.
    
    However, T012 produces a JSON. T013 should read that JSON, compute metrics, 
    and save the result.
    
    Let's assume the input is the output of T012: data/processed/raw_metrics.json (if T012 saved raw code)
    Actually, T012 description says: "save `data/processed/raw_metrics.json` with original code and structural predictors."
    Wait, T012 says "save ... with original code and structural predictors". 
    T013 says "Compute these metrics strictly on the *original* code".
    This implies T012 might just fetch and save raw code, and T013 computes the metrics.
    OR T012 saves raw code, and T013 reads it, computes metrics, and saves the enriched version.
    
    Given the task description: "Implement `code/data/static_analysis.py`: ... Flag unparseable functions."
    And T014: "Orchestrate download and analysis, filter out unparseable functions... and save `data/processed/raw_metrics.json`"
    
    So T012 downloads raw code. T013 computes metrics. T014 orchestrates and saves the final JSON.
    But T013 is the implementation of the analysis logic.
    
    Let's make main() runnable as a script that reads a raw JSON (from T012) and writes metrics.
    We'll assume T012 outputs `data/raw/raw_functions.json` (intermediate) and T013 reads it.
    Or if T012 outputs directly to `data/processed/raw_metrics.json` (but without metrics?), that's confusing.
    
    Let's assume T012 saves to `data/raw/downloaded_functions.json`.
    T013 reads `data/raw/downloaded_functions.json` and writes `data/processed/metrics_analysis.json`.
    T014 then combines or filters.
    
    Actually, T014 says "save `data/processed/raw_metrics.json`".
    So T013 should probably output to a temp or intermediate file, or just return data.
    Since T013 is a script, it should write a file.
    Let's define the input as `data/raw/downloaded_functions.json` (from T012)
    and output as `data/processed/metrics_analysis.json`.
    Then T014 merges/filters and saves to `data/processed/raw_metrics.json`.
    
    Wait, T012 says "save `data/processed/raw_metrics.json`". 
    If T012 saves to that path, then T013 must read it.
    But T012 says "save ... with original code and structural predictors". 
    This implies T012 might be doing the analysis? No, T013 is the analysis task.
    The description for T012 is slightly contradictory if it says it saves predictors.
    Let's assume T012 saves raw code to `data/raw/downloaded_functions.json`.
    And T013 reads that and saves `data/processed/metrics_analysis.json`.
    And T014 reads `data/processed/metrics_analysis.json`, filters, and saves `data/processed/raw_metrics.json`.
    
    To be safe and follow T014's instruction "save `data/processed/raw_metrics.json`", 
    T013 will save to `data/processed/metrics_analysis.json` as an intermediate step.
    """
    import json
    from pathlib import Path
    
    input_path = Path("data/raw/downloaded_functions.json")
    output_path = Path("data/processed/metrics_analysis.json")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Please run download.py first.")
        # Check if maybe it's in processed already?
        alt_input = Path("data/processed/raw_metrics.json")
        if alt_input.exists():
            logger.warning(f"Found {alt_input}. Using it as input (assuming it contains raw code).")
            input_path = alt_input
        else:
            raise FileNotFoundError(f"Input file {input_path} not found. Run T012 first.")
    
    logger.info(f"Reading input from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # data might be a list of dicts with 'code' and 'hash'
    samples = []
    for item in data:
        if 'code' in item and 'hash' in item:
            samples.append(FunctionSample(code=item['code'], metrics={}, hash=item['hash']))
        elif isinstance(item, FunctionSample):
            samples.append(item)
    
    results = run_static_analysis_on_dataset(samples, str(output_path))
    logger.info(f"Static analysis complete. Output written to {output_path}")


if __name__ == "__main__":
    main()