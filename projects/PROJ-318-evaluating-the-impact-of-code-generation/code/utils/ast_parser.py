"""
Robust AST parser utility for extracting method signatures and docstrings.

Handles syntax errors gracefully by skipping malformed files and logging warnings.
"""
import ast
import logging
from typing import List, Optional, Tuple, Any, Dict

logger = logging.getLogger(__name__)


class ASTParsingException(Exception):
    """Raised when AST parsing fails due to unexpected conditions."""
    pass


def _get_signature(node: ast.FunctionDef) -> str:
    """
    Extract the full function signature from an AST node.
    
    Args:
        node: The AST FunctionDef node.
        
    Returns:
        A string representation of the function signature.
    """
    args = node.args
    positional_args = []
    
    # Handle positional arguments
    for arg in args.args:
        annotation = ""
        if arg.annotation:
            annotation = f": {ast.unparse(arg.annotation)}"
        positional_args.append(f"{arg.arg}{annotation}")
    
    # Handle *args
    if args.vararg:
        var_annotation = ""
        if args.vararg.annotation:
            var_annotation = f": {ast.unparse(args.vararg.annotation)}"
        positional_args.append(f"*{args.vararg.arg}{var_annotation}")
    
    # Handle keyword-only arguments
    for arg in args.kwonlyargs:
        annotation = ""
        if arg.annotation:
            annotation = f": {ast.unparse(arg.annotation)}"
        positional_args.append(f"{arg.arg}{annotation}")
    
    # Handle **kwargs
    if args.kwarg:
        kw_annotation = ""
        if args.kwarg.annotation:
            kw_annotation = f": {ast.unparse(args.kwarg.annotation)}"
        positional_args.append(f"**{args.kwarg.arg}{kw_annotation}")
    
    # Build return annotation
    return_annotation = ""
    if node.returns:
        return_annotation = f" -> {ast.unparse(node.returns)}"
    
    return f"def {node.name}({', '.join(positional_args)}){return_annotation}"


def _get_docstring(node: ast.FunctionDef) -> Optional[str]:
    """
    Extract the docstring from a function node.
    
    Args:
        node: The AST FunctionDef node.
        
    Returns:
        The docstring text if present, None otherwise.
    """
    docstring = ast.get_docstring(node)
    return docstring if docstring else None


def _is_public_method(name: str) -> bool:
    """
    Check if a method name indicates it is public.
    
    Args:
        name: The method name to check.
        
    Returns:
        True if the method is public (doesn't start with underscore).
    """
    return not name.startswith('_')


def parse_python_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a Python file and extract public method signatures and docstrings.
    
    Args:
        file_path: Path to the Python file to parse.
        
    Returns:
        A list of dictionaries containing method information.
        Each dictionary has keys: 'signature', 'docstring'
        
    Raises:
        ASTParsingException: If the file cannot be read or parsed.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except IOError as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise ASTParsingException(f"Failed to read file {file_path}: {e}")
    
    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path} at line {e.lineno}: {e.msg}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing {file_path}: {e}")
        raise ASTParsingException(f"Unexpected error parsing {file_path}: {e}")
    
    methods = []
    
    # Walk the AST to find class definitions and function definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if _is_public_method(node.name):
                signature = _get_signature(node)
                docstring = _get_docstring(node)
                
                methods.append({
                    'signature': signature,
                    'docstring': docstring
                })
    
    return methods


def parse_python_files(file_paths: List[str]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Parse multiple Python files and extract public method signatures and docstrings.
    
    Args:
        file_paths: List of paths to Python files to parse.
        
    Returns:
        A tuple containing:
        - A list of dictionaries with method information from all successfully parsed files.
        - The count of files that failed to parse (syntax errors or read errors).
    """
    all_methods = []
    failed_count = 0
    
    for file_path in file_paths:
        try:
            methods = parse_python_file(file_path)
            all_methods.extend(methods)
        except ASTParsingException:
            failed_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}")
            failed_count += 1
    
    return all_methods, failed_count