"""
Static analysis wrapper for detecting code errors using AST and Pylint.

Detects:
- Missing imports
- Undefined variables
- Syntax/parse errors
"""
import ast
import subprocess
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Try to import pylint, but handle gracefully if not installed
try:
    from pylint.lint import Run
    from pylint.reporters.text import TextReporter
    import io
    HAS_PYLINT = True
except ImportError:
    HAS_PYLINT = False


def analyze_syntax_errors(code_str: str) -> List[Dict[str, Any]]:
    """
    Detect syntax errors using Python's AST module.
    
    Args:
        code_str: The source code as a string
        
    Returns:
        List of error dictionaries with type, message, and line number
    """
    errors = []
    try:
        ast.parse(code_str)
    except SyntaxError as e:
        errors.append({
            "type": "syntax_error",
            "message": str(e.msg),
            "line": e.lineno or 0,
            "column": e.offset or 0,
            "details": e.text.strip() if e.text else ""
        })
    return errors


def analyze_undefined_variables(code_str: str) -> List[Dict[str, Any]]:
    """
    Detect undefined variables using AST analysis.
    
    Args:
        code_str: The source code as a string
        
    Returns:
        List of error dictionaries for undefined variables
    """
    errors = []
    try:
        tree = ast.parse(code_str)
    except SyntaxError:
        # Can't analyze undefined variables if there's a syntax error
        return errors
    
    # Collect all defined names (imports, function defs, class defs, assignments)
    defined_names = set()
    
    class NameCollector(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            defined_names.add(node.name)
            self.generic_visit(node)
        
        def visit_AsyncFunctionDef(self, node):
            defined_names.add(node.name)
            self.generic_visit(node)
        
        def visit_ClassDef(self, node):
            defined_names.add(node.name)
            self.generic_visit(node)
        
        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                defined_names.add(name.split('.')[0])
            self.generic_visit(node)
        
        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                defined_names.add(name)
            self.generic_visit(node)
        
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Store):
                defined_names.add(node.id)
            self.generic_visit(node)
    
    collector = NameCollector()
    collector.visit(tree)
    
    # Find all loaded names that aren't defined
    class NameChecker(ast.NodeVisitor):
        def __init__(self):
            self.undefined = []
        
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                if node.id not in defined_names:
                    self.undefined.append({
                        "type": "undefined_variable",
                        "message": f"Name '{node.id}' is not defined",
                        "line": node.lineno,
                        "column": node.col_offset,
                        "variable": node.id
                    })
            self.generic_visit(node)
    
    checker = NameChecker()
    checker.visit(tree)
    
    return checker.undefined


def analyze_missing_imports(code_str: str) -> List[Dict[str, Any]]:
    """
    Detect missing imports using AST analysis.
    
    Args:
        code_str: The source code as a string
        
    Returns:
        List of error dictionaries for missing imports
    """
    errors = []
    try:
        tree = ast.parse(code_str)
    except SyntaxError:
        return errors
    
    # Collect all imported names
    imported_names = set()
    
    class ImportCollector(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imported_names.add(name.split('.')[0])
            self.generic_visit(node)
        
        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imported_names.add(name)
            self.generic_visit(node)
    
    collector = ImportCollector()
    collector.visit(tree)
    
    # Check for common standard library modules that might be missing
    # This is a simplified check - in practice, we'd need a full dependency resolver
    stdlib_modules = {
        'os', 'sys', 'json', 're', 'math', 'random', 'copy', 
        'typing', 'pathlib', 'collections', 'itertools', 'functools',
        'datetime', 'time', 'hashlib', 'ast', 'subprocess', 'io',
        'logging', 'unittest', 'pytest', 'dataclasses', 'enum'
    }
    
    # Find attribute accesses that might indicate missing imports
    class ImportChecker(ast.NodeVisitor):
        def __init__(self):
            self.missing = []
        
        def visit_Attribute(self, node):
            # Check if the attribute access is on a name that's not imported
            if isinstance(node.value, ast.Name):
                if node.value.id not in imported_names and node.value.id not in stdlib_modules:
                    # This might be a missing import, but could also be a user-defined variable
                    # We'll flag it for manual review
                    pass
            self.generic_visit(node)
    
    # Use Pylint for more accurate missing import detection
    if HAS_PYLINT:
        return analyze_with_pylint(code_str, "import-error")
    
    return errors


def analyze_with_pylint(code_str: str, error_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Use Pylint to detect various code errors.
    
    Args:
        code_str: The source code as a string
        error_type: Specific error type to filter (e.g., "import-error", "undefined-variable")
        
    Returns:
        List of error dictionaries
    """
    if not HAS_PYLINT:
        return []
    
    errors = []
    
    # Create a temporary file for pylint to analyze
    temp_file = Path("/tmp/temp_pylint_check.py")
    temp_file.write_text(code_str)
    
    try:
        # Capture pylint output
        output = io.StringIO()
        reporter = TextReporter(output)
        
        # Run pylint with specific checks
        try:
            Run(
                [str(temp_file), "--disable=all", "--enable=undefined-variable,import-error,syntax-error", "--output-format=text"],
                reporter=reporter,
                exit=False
            )
        except SystemExit:
            pass  # Pylint might call sys.exit
        
        result = output.getvalue()
        
        # Parse pylint output
        for line in result.split('\n'):
            if not line.strip():
                continue
            
            # Pylint format: filename:line:col: [type] message
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    try:
                        line_num = int(parts[1])
                        col_num = int(parts[2])
                        rest = ':'.join(parts[3:])
                        
                        # Extract error type and message
                        if '[' in rest and ']' in rest:
                            error_start = rest.index('[') + 1
                            error_end = rest.index(']')
                            error_type_found = rest[error_start:error_end].strip()
                            message = rest[error_end+1:].strip()
                            
                            if error_type is None or error_type in error_type_found.lower():
                                errors.append({
                                    "type": error_type_found.lower(),
                                    "message": message,
                                    "line": line_num,
                                    "column": col_num,
                                    "source": "pylint"
                                })
                    except (ValueError, IndexError):
                        continue
    finally:
        # Clean up temporary file
        if temp_file.exists():
            temp_file.unlink()
    
    return errors


def run_static_analysis(code_str: str) -> Dict[str, Any]:
    """
    Run comprehensive static analysis on code.
    
    Args:
        code_str: The source code as a string
        
    Returns:
        Dictionary containing all detected errors and analysis metadata
    """
    result = {
        "syntax_errors": [],
        "undefined_variables": [],
        "missing_imports": [],
        "total_errors": 0,
        "is_valid": True,
        "analysis_source": []
    }
    
    # Check for syntax errors
    syntax_errors = analyze_syntax_errors(code_str)
    result["syntax_errors"] = syntax_errors
    if syntax_errors:
        result["is_valid"] = False
        result["analysis_source"].append("ast")
    
    # If no syntax errors, check for undefined variables and missing imports
    if result["is_valid"]:
        undefined_vars = analyze_undefined_variables(code_str)
        result["undefined_variables"] = undefined_vars
        
        missing_imports = analyze_missing_imports(code_str)
        result["missing_imports"] = missing_imports
        
        # Also run pylint if available for more comprehensive checks
        if HAS_PYLINT:
            pylint_errors = analyze_with_pylint(code_str)
            # Merge pylint errors with our findings
            for error in pylint_errors:
                if error["type"] == "undefined-variable":
                    result["undefined_variables"].append(error)
                elif error["type"] == "import-error":
                    result["missing_imports"].append(error)
                elif error["type"] == "syntax-error":
                    result["syntax_errors"].append(error)
            if pylint_errors:
                result["analysis_source"].append("pylint")
        
        result["total_errors"] = (
            len(result["undefined_variables"]) + 
            len(result["missing_imports"])
        )
        if result["total_errors"] > 0:
            result["is_valid"] = False
    
    return result


def format_analysis_report(analysis_result: Dict[str, Any]) -> str:
    """
    Format analysis results as a human-readable report.
    
    Args:
        analysis_result: The result from run_static_analysis
        
    Returns:
        Formatted string report
    """
    lines = []
    lines.append("Static Analysis Report")
    lines.append("=" * 40)
    
    if analysis_result["is_valid"]:
        lines.append("Status: ✓ Code is valid")
    else:
        lines.append("Status: ✗ Code has errors")
    
    lines.append(f"Total Errors: {analysis_result['total_errors']}")
    lines.append(f"Analysis Sources: {', '.join(analysis_result['analysis_source'])}")
    lines.append("")
    
    if analysis_result["syntax_errors"]:
        lines.append("Syntax Errors:")
        for error in analysis_result["syntax_errors"]:
            lines.append(f"  Line {error['line']}, Col {error['column']}: {error['message']}")
        lines.append("")
    
    if analysis_result["undefined_variables"]:
        lines.append("Undefined Variables:")
        for error in analysis_result["undefined_variables"]:
            lines.append(f"  Line {error['line']}: {error['message']}")
        lines.append("")
    
    if analysis_result["missing_imports"]:
        lines.append("Missing Imports:")
        for error in analysis_result["missing_imports"]:
            lines.append(f"  Line {error['line']}: {error['message']}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    """CLI entry point for static analysis."""
    if len(sys.argv) < 2:
        print("Usage: python static_analysis.py <code_file_or_string>")
        print("  If argument starts with '-', it's treated as a code string")
        print("  Otherwise, it's treated as a file path")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg.startswith('-'):
        # Treat as code string (remove leading dash)
        code_str = arg[1:]
    else:
        # Treat as file path
        code_path = Path(arg)
        if not code_path.exists():
            print(f"Error: File not found: {code_path}")
            sys.exit(1)
        code_str = code_path.read_text()
    
    result = run_static_analysis(code_str)
    report = format_analysis_report(result)
    print(report)
    
    # Exit with error code if there are errors
    sys.exit(0 if result["is_valid"] else 1)


if __name__ == "__main__":
    main()