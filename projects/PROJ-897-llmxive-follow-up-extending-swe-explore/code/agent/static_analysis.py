"""
Static Analysis Module for SWE-Explore Agent.

Provides functions to analyze code for syntax errors, undefined variables,
missing imports, and general linting issues using `ast` and `pylint`.
Implements robust error handling to prevent agent crashes on tool failure.
"""
import ast
import subprocess
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_syntax_errors(code: str) -> List[Dict[str, Any]]:
    """
    Analyze code for syntax errors using the ast module.

    Args:
        code: The Python code string to analyze.

    Returns:
        A list of dictionaries containing error details.
    """
    errors = []
    try:
        ast.parse(code)
    except SyntaxError as e:
        errors.append({
            "type": "syntax_error",
            "message": str(e),
            "lineno": e.lineno,
            "offset": e.offset,
            "text": e.text
        })
    except Exception as e:
        # Catch any unexpected parsing errors to prevent crashes
        errors.append({
            "type": "parsing_exception",
            "message": f"Unexpected error during AST parsing: {str(e)}",
            "lineno": None,
            "offset": None,
            "text": None
        })
    return errors

def analyze_undefined_variables(code: str) -> List[Dict[str, Any]]:
    """
    Analyze code for undefined variables using a custom AST visitor.

    Args:
        code: The Python code string to analyze.

    Returns:
        A list of dictionaries containing undefined variable details.
    """
    errors = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # If there's a syntax error, undefined variable analysis is unreliable
        return [{"type": "syntax_error_prevents_analysis", "message": "Cannot analyze undefined variables due to syntax errors."}]
    except Exception as e:
        return [{"type": "parsing_exception", "message": f"Unexpected error: {str(e)}"}]

    class UndefinedVariableVisitor(ast.NodeVisitor):
        def __init__(self):
            self.defined_names = set()
            self.undefined = []

        def visit_FunctionDef(self, node):
            self.defined_names.add(node.name)
            # Add arguments to defined names
            for arg in node.args.args:
                self.defined_names.add(arg.arg)
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            self.defined_names.add(node.name)
            self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Store):
                self.defined_names.add(node.id)
            elif isinstance(node.ctx, ast.Load):
                if node.id not in self.defined_names and node.id not in dir(__builtins__):
                    self.undefined.append({
                        "type": "undefined_variable",
                        "name": node.id,
                        "lineno": node.lineno,
                        "offset": node.col_offset
                    })
            self.generic_visit(node)

        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self.defined_names.add(name)
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self.defined_names.add(name)
            self.generic_visit(node)

    visitor = UndefinedVariableVisitor()
    visitor.visit(tree)
    return visitor.undefined

def analyze_missing_imports(code: str) -> List[Dict[str, Any]]:
    """
    Analyze code for missing imports (basic check against standard library).
    Note: This is a heuristic and may have false positives for non-standard libs.

    Args:
        code: The Python code string to analyze.

    Returns:
        A list of dictionaries containing missing import details.
    """
    # Simplified check: look for common standard library imports that are used but not imported
    # This is a basic implementation; a full check would require resolving all names.
    errors = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return [{"type": "syntax_error_prevents_analysis", "message": "Cannot analyze imports due to syntax errors."}]
    except Exception as e:
        return [{"type": "parsing_exception", "message": f"Unexpected error: {str(e)}"}]

    imports = set()
    used_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.asname if alias.asname else alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.add(alias.asname if alias.asname else alias.name.split('.')[0])
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_names.add(node.id)

    # Check for common stdlib modules used but not imported
    # This is a very basic heuristic.
    common_stdlib = {'json', 'os', 'sys', 're', 'math', 'random', 'collections', 'itertools', 'functools', 'pathlib', 'typing', 'datetime', 'time', 'subprocess', 'logging'}
    
    for name in used_names:
        if name in common_stdlib and name not in imports:
            errors.append({
                "type": "missing_import",
                "name": name,
                "lineno": None, # Hard to determine exact line without more complex analysis
                "offset": None,
                "suggestion": f"import {name}"
            })

    return errors

def analyze_with_pylint(code: str) -> List[Dict[str, Any]]:
    """
    Analyze code using pylint.

    Args:
        code: The Python code string to analyze.

    Returns:
        A list of dictionaries containing pylint issues.
    """
    issues = []
    try:
        # Write code to a temporary file for pylint to analyze
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Run pylint with specific flags to get JSON output
            result = subprocess.run(
                [sys.executable, '-m', 'pylint', '--output-format=json', temp_file],
                capture_output=True,
                text=True,
                timeout=30 # Timeout after 30 seconds
            )
            
            if result.returncode == 0 or result.returncode == 1: # 1 means issues found, 0 means no issues
                try:
                    pylint_output = json.loads(result.stdout)
                    for issue in pylint_output:
                        issues.append({
                            "type": "pylint_issue",
                            "message": issue.get('message', ''),
                            "symbol": issue.get('symbol', ''),
                            "lineno": issue.get('line', 0),
                            "column": issue.get('column', 0),
                            "severity": issue.get('confidence', {}).get('name', 'unknown')
                        })
                except json.JSONDecodeError:
                    logger.warning("Pylint output was not valid JSON. Raw output: %s", result.stdout)
            else:
                logger.warning(f"Pylint failed with return code {result.returncode}. Stderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            issues.append({
                "type": "pylint_timeout",
                "message": "Pylint analysis timed out.",
                "lineno": None,
                "column": None,
                "severity": "error"
            })
        except FileNotFoundError:
            issues.append({
                "type": "pylint_not_found",
                "message": "Pylint is not installed or not in PATH.",
                "lineno": None,
                "column": None,
                "severity": "error"
            })
        finally:
            os.unlink(temp_file)
    except Exception as e:
        issues.append({
            "type": "pylint_exception",
            "message": f"Unexpected error during pylint analysis: {str(e)}",
            "lineno": None,
            "column": None,
            "severity": "error"
        })
    return issues

def run_static_analysis(code: str) -> Dict[str, Any]:
    """
    Run all static analysis functions on the provided code.

    Args:
        code: The Python code string to analyze.

    Returns:
        A dictionary containing the results of all analyses.
    """
    analysis_results = {
        "syntax_errors": analyze_syntax_errors(code),
        "undefined_variables": analyze_undefined_variables(code),
        "missing_imports": analyze_missing_imports(code),
        "pylint_issues": []
    }

    # Attempt pylint only if basic checks pass or as a separate pass
    # If syntax errors exist, pylint might not be useful, but we can still try.
    if not analysis_results["syntax_errors"]:
        analysis_results["pylint_issues"] = analyze_with_pylint(code)
    else:
        analysis_results["pylint_issues"].append({
            "type": "skipped_pylint_due_to_syntax_error",
            "message": "Pylint analysis skipped due to existing syntax errors.",
            "lineno": None,
            "column": None,
            "severity": "info"
        })

    return analysis_results

def format_analysis_report(analysis_results: Dict[str, Any]) -> str:
    """
    Format the analysis results into a human-readable string.

    Args:
        analysis_results: The dictionary of analysis results.

    Returns:
        A formatted string report.
    """
    report_lines = []
    report_lines.append("Static Analysis Report")
    report_lines.append("=" * 20)

    if analysis_results["syntax_errors"]:
        report_lines.append("\nSyntax Errors:")
        for err in analysis_results["syntax_errors"]:
            report_lines.append(f"  - Line {err.get('lineno')}: {err.get('message')}")
    else:
        report_lines.append("\nNo syntax errors found.")

    if analysis_results["undefined_variables"]:
        report_lines.append("\nUndefined Variables:")
        for err in analysis_results["undefined_variables"]:
            report_lines.append(f"  - Line {err.get('lineno')}: '{err.get('name')}' is not defined")
    else:
        report_lines.append("\nNo undefined variables found.")

    if analysis_results["missing_imports"]:
        report_lines.append("\nMissing Imports (Heuristic):")
        for err in analysis_results["missing_imports"]:
            report_lines.append(f"  - '{err.get('name')}' might need to be imported. Suggestion: {err.get('suggestion')}")
    else:
        report_lines.append("\nNo missing imports detected (heuristic).")

    if analysis_results["pylint_issues"]:
        report_lines.append("\nPylint Issues:")
        for issue in analysis_results["pylint_issues"]:
            if issue["type"] in ["skipped_pylint_due_to_syntax_error", "pylint_timeout", "pylint_not_found", "pylint_exception"]:
                report_lines.append(f"  - {issue.get('message')}")
            else:
                report_lines.append(f"  - Line {issue.get('lineno')}, Col {issue.get('column')}: [{issue.get('symbol')}] {issue.get('message')} ({issue.get('severity')})")
    else:
        report_lines.append("\nNo pylint issues found.")

    return "\n".join(report_lines)

def main():
    """
    Main function for testing the static analysis module.
    """
    sample_code = """
    import json

    def calculate_sum(a, b):
        result = a + b
        return result

    def process_data(data):
        # This function has an undefined variable 'undefined_var'
        total = sum(undefined_var)
        return total
    
    def unused_function():
        pass
    """

    print("Analyzing sample code...")
    results = run_static_analysis(sample_code)
    print(format_analysis_report(results))

if __name__ == "__main__":
    main()