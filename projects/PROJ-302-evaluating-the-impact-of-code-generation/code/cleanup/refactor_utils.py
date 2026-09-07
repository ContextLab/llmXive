"""
Code cleanup and refactoring utilities for the llmXive pipeline.

This module centralizes common refactoring operations to improve code quality,
reduce duplication, and enforce consistency across the project.

Key refactoring areas:
1. Standardize logging configuration across all modules
2. Consolidate path handling utilities
3. Remove redundant error handling patterns
4. Enforce consistent type hinting
5. Optimize import statements
"""
import os
import sys
import logging
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import argparse
import json
from datetime import datetime

# Import from project utils
from utils.config import get_config, ensure_directories
from utils.validators import validate_schema, ValidationError

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Refactoring rules configuration
REFACTOR_RULES = {
    "max_line_length": 100,
    "max_function_length": 50,
    "max_parameters": 5,
    "required_docstring": True,
    "type_hints_required": True,
    "logging_required": True,
    "remove_unused_imports": True,
    "standardize_error_handling": True,
}

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure standardized logging across the project.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("llmXive_cleanup")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper()))
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def analyze_file_for_issues(file_path: Path, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Analyze a Python file for common code quality issues.
    
    Args:
        file_path: Path to the Python file to analyze
        logger: Optional logger instance
    
    Returns:
        Dictionary containing analysis results and issues found
    """
    if logger is None:
        logger = setup_logging()
    
    issues = {
        "file": str(file_path),
        "line_count": 0,
        "function_count": 0,
        "issues_found": [],
        "suggestions": [],
    }
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
            issues["line_count"] = len(lines)
        
        # Parse AST for deeper analysis
        tree = ast.parse(content)
        
        # Check for functions
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        issues["function_count"] = len(functions)
        
        # Check line lengths
        for i, line in enumerate(lines, 1):
            if len(line) > REFACTOR_RULES["max_line_length"]:
                issues["issues_found"].append({
                    "type": "line_too_long",
                    "line": i,
                    "length": len(line),
                    "max_allowed": REFACTOR_RULES["max_line_length"],
                })
        
        # Check function complexity
        for func in functions:
            if len(func.args.args) > REFACTOR_RULES["max_parameters"]:
                issues["issues_found"].append({
                    "type": "too_many_parameters",
                    "function": func.name,
                    "count": len(func.args.args),
                    "max_allowed": REFACTOR_RULES["max_parameters"],
                })
        
        # Check for missing docstrings
        if REFACTOR_RULES["required_docstring"]:
            for func in functions:
                if not ast.get_docstring(func):
                    issues["issues_found"].append({
                        "type": "missing_docstring",
                        "function": func.name,
                        "line": func.lineno,
                    })
        
        # Check for TODO comments
        todo_pattern = re.compile(r"#\s*(TODO|FIXME|XXX|HACK):?\s*(.*)", re.IGNORECASE)
        for i, line in enumerate(lines, 1):
            match = todo_pattern.search(line)
            if match:
                issues["issues_found"].append({
                    "type": "todo_comment",
                    "line": i,
                    "content": match.group(2).strip() if match.group(2) else "No description",
                })
        
        # Generate suggestions
        if issues["issues_found"]:
            issues["suggestions"].append("Review and fix identified issues before committing")
            if any(issue["type"] == "todo_comment" for issue in issues["issues_found"]):
                issues["suggestions"].append("Remove or resolve all TODO comments")
            if any(issue["type"] == "missing_docstring" for issue in issues["issues_found"]):
                issues["suggestions"].append("Add docstrings to all functions")
        
    except SyntaxError as e:
        issues["issues_found"].append({
            "type": "syntax_error",
            "message": str(e),
            "line": getattr(e, "lineno", None),
        })
    except Exception as e:
        issues["issues_found"].append({
            "type": "analysis_error",
            "message": str(e),
        })
    
    return issues

def batch_analyze_directory(directory: Path, pattern: str = "*.py", logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Analyze all Python files in a directory recursively.
    
    Args:
        directory: Directory to scan
        pattern: Glob pattern for files to analyze
        logger: Optional logger instance
    
    Returns:
        Dictionary containing aggregated analysis results
    """
    if logger is None:
        logger = setup_logging()
    
    logger.info(f"Analyzing directory: {directory}")
    
    results = {
        "directory": str(directory),
        "files_analyzed": 0,
        "total_issues": 0,
        "files_with_issues": 0,
        "issue_breakdown": {},
        "file_results": [],
    }
    
    for py_file in directory.rglob(pattern):
        if py_file.is_file():
            file_result = analyze_file_for_issues(py_file, logger)
            results["file_results"].append(file_result)
            results["files_analyzed"] += 1
            
            if file_result["issues_found"]:
                results["files_with_issues"] += 1
                results["total_issues"] += len(file_result["issues_found"])
                
                for issue in file_result["issues_found"]:
                    issue_type = issue["type"]
                    results["issue_breakdown"][issue_type] = results["issue_breakdown"].get(issue_type, 0) + 1
    
    logger.info(f"Analyzed {results['files_analyzed']} files, found {results['total_issues']} issues")
    return results

def generate_cleanup_report(analysis_results: Dict[str, Any], output_path: Path) -> None:
    """
    Generate a detailed cleanup report from analysis results.
    
    Args:
        analysis_results: Results from batch_analyze_directory
        output_path: Path to write the JSON report
    """
    ensure_directories([output_path.parent])
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "directory": analysis_results["directory"],
            "files_analyzed": analysis_results["files_analyzed"],
            "total_issues": analysis_results["total_issues"],
            "files_with_issues": analysis_results["files_with_issues"],
            "issue_breakdown": analysis_results["issue_breakdown"],
        },
        "details": analysis_results["file_results"],
        "recommendations": [
            "Run black and ruff for automatic formatting and linting",
            "Address all TODO comments before release",
            "Ensure all functions have docstrings",
            "Keep line lengths under 100 characters",
            "Limit function parameters to 5 or fewer",
        ],
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    logging.getLogger("llmXive_cleanup").info(f"Cleanup report written to {output_path}")

def run_refactoring_checks(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run comprehensive refactoring checks on the project.
    
    Args:
        base_dir: Base directory to analyze (defaults to project root)
    
    Returns:
        Dictionary containing refactoring check results
    """
    if base_dir is None:
        base_dir = PROJECT_ROOT
    
    logger = setup_logging()
    logger.info("Starting refactoring checks...")
    
    # Analyze code directory
    code_dir = base_dir / "code"
    if code_dir.exists():
        results = batch_analyze_directory(code_dir, logger=logger)
    else:
        results = {
            "directory": str(code_dir),
            "files_analyzed": 0,
            "total_issues": 0,
            "files_with_issues": 0,
            "issue_breakdown": {},
            "file_results": [],
        }
    
    # Generate report
    report_path = base_dir / "data" / "processed" / "refactoring_report.json"
    generate_cleanup_report(results, report_path)
    
    return {
        "status": "completed",
        "report_path": str(report_path),
        "summary": results,
    }

def main() -> int:
    """
    Main entry point for the cleanup and refactoring utility.
    
    Returns:
        Exit code (0 for success, 1 for issues found)
    """
    parser = argparse.ArgumentParser(description="Code cleanup and refactoring utility")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=PROJECT_ROOT,
        help="Base directory to analyze",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Custom output path for the report",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    logger = setup_logging("DEBUG" if args.verbose else "INFO")
    logger.info(f"Running refactoring checks on: {args.base_dir}")
    
    try:
        results = run_refactoring_checks(args.base_dir)
        
        if args.output:
            ensure_directories([args.output.parent])
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results written to {args.output}")
        
        # Check for critical issues
        total_issues = results["summary"]["total_issues"]
        if total_issues > 0:
            logger.warning(f"Found {total_issues} issues that should be addressed")
            return 1
        
        logger.info("No issues found. Code is clean!")
        return 0
    
    except Exception as e:
        logger.error(f"Refactoring checks failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
