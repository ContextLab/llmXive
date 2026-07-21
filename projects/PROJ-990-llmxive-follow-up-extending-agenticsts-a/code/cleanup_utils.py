import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import logging

# Configure logging for cleanup analysis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_python_files(root_dir: Path) -> List[Path]:
    """
    Recursively find all Python files in the given directory.
    
    Args:
        root_dir: The root directory to search.
        
    Returns:
        A list of Path objects for all .py files found.
    """
    python_files = []
    for path in root_dir.rglob('*.py'):
        # Skip __pycache__ and hidden directories
        if '__pycache__' not in str(path) and not path.name.startswith('.'):
            python_files.append(path)
    return python_files


def check_for_todos(file_path: Path) -> List[Dict[str, any]]:
    """
    Scan a Python file for TODO, FIXME, HACK, and XXX comments.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        A list of dictionaries containing line number and comment text.
    """
    issues = []
    pattern = re.compile(r'#\s*(TODO|FIXME|HACK|XXX):?\s*(.*)', re.IGNORECASE)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                match = pattern.search(line)
                if match:
                    issues.append({
                        'line': line_num,
                        'type': match.group(1).upper(),
                        'text': match.group(2).strip()
                    })
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        
    return issues


def check_for_pass_only_functions(file_path: Path) -> List[Dict[str, any]]:
    """
    Identify functions/classes that contain only 'pass' statements.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        A list of dictionaries containing name and line number.
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
        return issues
    except Exception as e:
        logger.warning(f"Could not parse {file_path}: {e}")
        return issues
        
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Check if body has exactly one statement which is 'pass'
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                issues.append({
                    'name': node.name,
                    'type': 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class',
                    'line': node.lineno
                })
                
    return issues


def check_import_groups(file_path: Path) -> List[Dict[str, any]]:
    """
    Check for inconsistent or missing blank lines between import groups.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        A list of dictionaries describing import issues.
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return issues
        
    in_import_block = False
    last_import_line = -1
    import_type = None  # 'stdlib', 'thirdparty', 'local'
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip comments and empty lines for import detection
        if not stripped or stripped.startswith('#'):
            continue
            
        is_import = stripped.startswith('import ') or stripped.startswith('from ')
        
        if is_import:
            # Determine import type
            if stripped.startswith('from ') or stripped.startswith('import '):
                module_part = stripped.split()[1].split('.')[0] if ' ' in stripped else stripped.split('.')[0]
                
                current_type = 'local'
                if module_part in ['os', 'sys', 're', 'ast', 'json', 'logging', 'pathlib', 'typing', 'random', 'time', 'hashlib', 'pickle', 'numpy', 'pandas']:
                    if module_part in ['numpy', 'pandas']:
                        current_type = 'thirdparty'
                    else:
                        current_type = 'stdlib'
                
                if import_type and import_type != current_type:
                    # Check if there was a blank line between groups
                    if i - last_import_line > 1:
                        # There is a blank line, which is good
                        pass
                    else:
                        issues.append({
                            'line': i + 1,
                            'type': 'import_group',
                            'text': f"Missing blank line between {import_type} and {current_type} imports"
                        })
                
                import_type = current_type
                in_import_block = True
                last_import_line = i
        else:
            if in_import_block:
                in_import_block = False
                
    return issues


def analyze_code_quality(root_dir: Path) -> Dict[str, any]:
    """
    Perform a comprehensive code quality analysis on all Python files.
    
    Args:
        root_dir: The root directory containing the code.
        
    Returns:
        A dictionary containing analysis results.
    """
    python_files = find_python_files(root_dir)
    total_files = len(python_files)
    total_issues = 0
    
    todos = []
    empty_functions = []
    import_issues = []
    
    logger.info(f"Analyzing {total_files} Python files in {root_dir}")
    
    for file_path in python_files:
        # Check for TODOs
        file_todos = check_for_todos(file_path)
        if file_todos:
            todos.extend([{'file': str(file_path), **todo} for todo in file_todos])
            total_issues += len(file_todos)
            
        # Check for pass-only functions
        file_empty = check_for_pass_only_functions(file_path)
        if file_empty:
            empty_functions.extend([{'file': str(file_path), **item} for item in file_empty])
            total_issues += len(file_empty)
            
        # Check import groups
        file_import_issues = check_import_groups(file_path)
        if file_import_issues:
            import_issues.extend([{'file': str(file_path), **issue} for issue in file_import_issues])
            total_issues += len(file_import_issues)
            
    return {
        'total_files': total_files,
        'total_issues': total_issues,
        'todos': todos,
        'empty_functions': empty_functions,
        'import_issues': import_issues,
        'summary': {
            'todo_count': len(todos),
            'empty_function_count': len(empty_functions),
            'import_issue_count': len(import_issues)
        }
    }


def generate_cleanup_report(root_dir: Path, output_path: Path) -> Dict[str, any]:
    """
    Generate a cleanup report and save it to the specified path.
    
    Args:
        root_dir: The root directory to analyze.
        output_path: Path where the report will be saved.
        
    Returns:
        The report dictionary.
    """
    logger.info(f"Generating cleanup report for {root_dir}")
    
    report = analyze_code_quality(root_dir)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save report as JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Cleanup report saved to {output_path}")
    logger.info(f"Found {report['summary']['todo_count']} TODOs, "
               f"{report['summary']['empty_function_count']} empty functions, "
               f"{report['summary']['import_issue_count']} import issues")
    
    return report


def main():
    """Main entry point for the cleanup analysis script."""
    import json
    
    # Default paths
    root_dir = Path('code')
    output_file = Path('data/processed/cleanup_report.json')
    
    # Parse command line arguments if provided
    import sys
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
        
    try:
        report = generate_cleanup_report(root_dir, output_file)
        print(f"Analysis complete. Report saved to {output_file}")
        print(f"Total issues found: {report['total_issues']}")
        return 0
    except Exception as e:
        logger.error(f"Error during cleanup analysis: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
