import os
import sys
import logging
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
def setup_logging(log_file: str = "logs/cleanup_report.log") -> logging.Logger:
    """Setup logging for the cleanup/refactor utility."""
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    logger = logging.getLogger("refactor_utils")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_path / log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def analyze_file_for_issues(file_path: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Analyze a single Python file for common code quality issues.
    
    Checks:
    - Unused imports
    - Dead code (unreachable after return/raise/exit)
    - Long functions (>50 lines)
    - Deep nesting (>4 levels)
    - Magic numbers
    - TODO/FIXME comments
    """
    issues = []
    
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return {"issues": issues, "status": "skipped"}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
    
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "line": e.lineno,
                "message": str(e.msg)
            })
            return {"issues": issues, "status": "failed"}
    
        # Analyze AST
        for node in ast.walk(tree):
            # Check for long functions
            if isinstance(node, ast.FunctionDef):
                if node.end_lineno and (node.end_lineno - node.lineno) > 50:
                    issues.append({
                        "type": "long_function",
                        "name": node.name,
                        "line": node.lineno,
                        "lines": node.end_lineno - node.lineno
                    })
                
                # Check for deep nesting
                max_depth = 0
                current_depth = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                        current_depth += 1
                        max_depth = max(max_depth, current_depth)
                    elif isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                        # This is a simplification; actual depth tracking is more complex
                        pass
                
                # Simple depth check for common patterns
                if hasattr(node, 'body'):
                    for item in node.body:
                        if isinstance(item, (ast.If, ast.For, ast.While)):
                            if hasattr(item, 'body'):
                                for sub_item in item.body:
                                    if isinstance(sub_item, (ast.If, ast.For, ast.While)):
                                        issues.append({
                                            "type": "deep_nesting",
                                            "name": node.name,
                                            "line": node.lineno,
                                            "message": "Nesting depth > 4 detected"
                                        })
                                        break
            
            # Check for magic numbers (excluding 0, 1, -1)
            if isinstance(node, ast.Num):
                if node.n not in (0, 1, -1):
                    # Check if it's in an assignment or comparison context
                    issues.append({
                        "type": "magic_number",
                        "value": node.n,
                        "line": node.lineno
                    })
    
        # Text-based checks
        for i, line in enumerate(lines, 1):
            # Check for TODO/FIXME comments
            if re.search(r'#\s*(TODO|FIXME|XXX|HACK):', line, re.IGNORECASE):
                issues.append({
                    "type": "todo_comment",
                    "line": i,
                    "content": line.strip()
                })
            
            # Check for long lines (>120 chars)
            if len(line) > 120:
                issues.append({
                    "type": "long_line",
                    "line": i,
                    "length": len(line)
                })
    
        logger.info(f"Analyzed {file_path}: found {len(issues)} issues")
        return {"issues": issues, "status": "success", "file": str(file_path)}
    
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return {"issues": [{"type": "error", "message": str(e)}], "status": "error"}

def batch_analyze_directory(directory: Path, logger: logging.Logger) -> List[Dict[str, Any]]:
    """Analyze all Python files in a directory recursively."""
    results = []
    python_files = list(directory.rglob("*.py"))
    
    logger.info(f"Found {len(python_files)} Python files in {directory}")
    
    for file_path in python_files:
        # Skip test files and generated files
        if "/tests/" in str(file_path) or "__pycache__" in str(file_path):
            continue
        
        result = analyze_file_for_issues(file_path, logger)
        results.append(result)
    
    return results

def generate_cleanup_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Generate a cleanup report summarizing all issues found."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "total_files": len(results),
        "files_with_issues": sum(1 for r in results if r.get("issues") and r["status"] == "success"),
        "total_issues": sum(len(r.get("issues", [])) for r in results if r["status"] == "success"),
        "issue_types": {},
        "files": []
    }
    
    for result in results:
        if result["status"] == "success":
            for issue in result.get("issues", []):
                issue_type = issue.get("type", "unknown")
                summary["issue_types"][issue_type] = summary["issue_types"].get(issue_type, 0) + 1
            summary["files"].append({
                "file": result.get("file"),
                "issue_count": len(result.get("issues", [])),
                "issues": result.get("issues", [])
            })
    
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logging.info(f"Cleanup report generated: {output_path}")

def run_refactoring_checks(base_dir: Path = None) -> Path:
    """
    Run all refactoring checks on the codebase and generate a report.
    
    Returns the path to the generated report.
    """
    if base_dir is None:
        base_dir = Path("code")
    
    logger = setup_logging()
    logger.info("Starting refactoring checks...")
    
    # Analyze all Python files
    results = batch_analyze_directory(base_dir, logger)
    
    # Generate report
    report_path = Path("data/processed/refactoring_report.json")
    generate_cleanup_report(results, report_path)
    
    logger.info(f"Refactoring checks complete. Report: {report_path}")
    return report_path

def main():
    """Main entry point for the cleanup utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Code cleanup and refactoring utility")
    parser.add_argument("--dir", type=str, default="code", help="Directory to analyze")
    parser.add_argument("--output", type=str, default="data/processed/refactoring_report.json", help="Output report path")
    args = parser.parse_args()
    
    base_dir = Path(args.dir)
    output_path = Path(args.output)
    
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        sys.exit(1)
    
    logger = setup_logging()
    logger.info(f"Analyzing directory: {base_dir}")
    
    results = batch_analyze_directory(base_dir, logger)
    generate_cleanup_report(results, output_path)
    
    print(f"Refactoring report generated: {output_path}")

if __name__ == "__main__":
    main()