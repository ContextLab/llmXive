"""
T032: Code cleanup script to remove unused imports and fix linting errors.
This script scans all Python files in the code/ directory, identifies unused
imports, and fixes common linting issues (like missing newlines at EOF).
"""
import os
import ast
import re
import logging
import subprocess
from pathlib import Path
from typing import List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_python_files(directory: Path) -> List[Path]:
    """Recursively find all Python files in the given directory."""
    return list(directory.rglob('*.py'))

def get_used_names(tree: ast.AST) -> Set[str]:
    """Extract all names used in the AST (excluding import definitions)."""
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attribute usage
            if isinstance(node.value, ast.Name):
                used.add(node.value.id)
    return used

def get_imported_names(tree: ast.AST) -> List[Tuple[str, str]]:
    """
    Extract imported names and their aliases.
    Returns list of (original_name, alias) tuples.
    """
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.append((alias.name, name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                if alias.name == '*':
                    continue
                name = alias.asname if alias.asname else alias.name
                imports.append((f"{module}.{alias.name}", name))
    return imports

def find_unused_imports(file_path: Path) -> List[Tuple[str, str, int]]:
    """
    Find unused imports in a Python file.
    Returns list of (original_name, alias, line_number) tuples.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        used_names = get_used_names(tree)
        imported_names = get_imported_names(tree)
        
        unused = []
        for original, alias in imported_names:
            # Check if the alias is used (excluding the import line itself)
            if alias not in used_names:
                # Find line number (approximate)
                for i, line in enumerate(content.splitlines(), 1):
                    if f'import {alias}' in line or f'as {alias}' in line:
                        unused.append((original, alias, i))
                        break
        
        return unused
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return []

def remove_unused_imports(file_path: Path, unused_imports: List[Tuple[str, str, int]]) -> bool:
    """Remove unused imports from the file."""
    if not unused_imports:
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Sort by line number in descending order to avoid line number shifts
        unused_imports.sort(key=lambda x: x[2], reverse=True)
        
        modified = False
        for original, alias, line_num in unused_imports:
            if 0 < line_num <= len(lines):
                line_idx = line_num - 1
                line_content = lines[line_idx]
                
                # Remove the import line
                if line_content.strip().startswith('import') or line_content.strip().startswith('from'):
                    lines[line_idx] = ''
                    modified = True
            
        if modified:
            # Write back only if changed
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(line for line in lines if line.strip())
            logger.info(f"Removed unused imports from {file_path}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Failed to modify {file_path}: {e}")
        return False

def ensure_newline_at_eof(file_path: Path) -> bool:
    """Ensure the file ends with a newline."""
    try:
        with open(file_path, 'rb') as f:
            f.seek(0, 2)  # End of file
            if f.tell() == 0:
                return False  # Empty file
            f.seek(-1, 2)
            last_char = f.read(1)
            
        if last_char != b'\n':
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\n')
            logger.info(f"Added newline at EOF for {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking EOF for {file_path}: {e}")
        return False

def run_black(file_path: Path) -> bool:
    """Run black formatter on the file if available."""
    try:
        result = subprocess.run(
            ['black', str(file_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            logger.info(f"Formatted {file_path} with black")
            return True
        elif result.returncode == 1:
            logger.warning(f"Black had formatting changes for {file_path}")
            return True
        else:
            logger.error(f"Black failed on {file_path}: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.warning("black not found, skipping formatting")
        return False
    except Exception as e:
        logger.error(f"Error running black on {file_path}: {e}")
        return False

def run_flake8(file_path: Path) -> List[str]:
    """Run flake8 on the file and return list of issues."""
    try:
        result = subprocess.run(
            ['flake8', str(file_path), '--select=E9,F63,F7,F82'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.stdout:
            return result.stdout.strip().split('\n')
        return []
    except FileNotFoundError:
        logger.warning("flake8 not found, skipping critical error check")
        return []
    except Exception as e:
        logger.error(f"Error running flake8 on {file_path}: {e}")
        return []

def main():
    """Main function to clean up code directory."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / 'code'
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1
    
    logger.info(f"Starting cleanup for {code_dir}")
    
    python_files = get_python_files(code_dir)
    logger.info(f"Found {len(python_files)} Python files")
    
    total_unused = 0
    total_formatted = 0
    total_eof_fixed = 0
    critical_errors = 0
    
    for file_path in python_files:
        logger.info(f"Processing {file_path}")
        
        # Find and remove unused imports
        unused = find_unused_imports(file_path)
        if unused:
            logger.info(f"Found {len(unused)} unused imports in {file_path}")
            if remove_unused_imports(file_path, unused):
                total_unused += len(unused)
        
        # Ensure newline at EOF
        if ensure_newline_at_eof(file_path):
            total_eof_fixed += 1
        
        # Run black if available
        run_black(file_path)
        total_formatted += 1
        
        # Check for critical flake8 errors
        errors = run_flake8(file_path)
        if errors:
            critical_errors += len(errors)
            for error in errors:
                logger.error(f"Critical error in {file_path}: {error}")
    
    logger.info(f"Cleanup complete:")
    logger.info(f"  - Unused imports removed: {total_unused}")
    logger.info(f"  - Files formatted: {total_formatted}")
    logger.info(f"  - EOF newlines added: {total_eof_fixed}")
    logger.info(f"  - Critical errors found: {critical_errors}")
    
    if critical_errors > 0:
        logger.error(f"Found {critical_errors} critical errors that need manual review")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())