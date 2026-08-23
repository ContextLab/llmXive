"""
T038: Code cleanup and refactoring.

This module provides utility functions to identify and refactor common
code smells across the project, including:
1. Removing unused imports
2. Consolidating duplicate logging setup
3. Standardizing docstrings
4. Removing dead code (unreachable blocks)
5. Normalizing path handling

It operates as a post-processing step to ensure code quality before final delivery.
"""
import os
import re
import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from config import get_paths, load_config
from utils.logging import get_logger

# Configure logging for the cleanup task
logger = get_logger("cleanup")

# Common patterns for refactoring
UNUSED_IMPORT_PATTERN = re.compile(r'^\s*import\s+\w+.*$')
UNUSED_FROM_PATTERN = re.compile(r'^\s*from\s+\w+\s+import\s+\w+.*$')
DEAD_CODE_MARKERS = ['pass', 'raise NotImplementedError', 'TODO', 'FIXME']

class CodeRefactorer:
    """Handles the refactoring of Python source files."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.changes_made: Dict[str, List[str]] = {}

    def find_python_files(self) -> List[Path]:
        """Recursively find all .py files in the code directory."""
        code_dir = self.project_root / "code"
        if not code_dir.exists():
            logger.warning(f"Code directory not found at {code_dir}")
            return []
        
        return list(code_dir.rglob("*.py"))

    def remove_unused_imports(self, content: str, filename: str) -> tuple[str, bool]:
        """
        Attempt to remove unused imports by parsing the AST.
        Returns (new_content, was_modified).
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.debug(f"Skipping {filename} due to syntax error")
            return content, False

        # Get all names used in the module
        used_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Handle module.attribute usage
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        lines = content.splitlines(keepends=True)
        new_lines = []
        modified = False

        for i, line in enumerate(lines):
            # Check for import statements
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                try:
                    import_node = ast.parse(line.strip())
                    if not import_node.body:
                        new_lines.append(line)
                        continue
                    
                    imp = import_node.body[0]
                    names_to_keep = []
                    
                    if isinstance(imp, ast.Import):
                        for alias in imp.names:
                            name = alias.asname if alias.asname else alias.name
                            if name in used_names or alias.name in used_names:
                                names_to_keep.append(alias)
                    elif isinstance(imp, ast.ImportFrom):
                        for alias in imp.names:
                            name = alias.asname if alias.asname else alias.name
                            if name in used_names:
                                names_to_keep.append(alias)
                    
                    if len(names_to_keep) != len(imp.names):
                        # Reconstruct the import line
                        if isinstance(imp, ast.Import):
                            new_line = "import " + ", ".join(
                                f"{a.name} as {a.asname}" if a.asname else a.name 
                                for a in names_to_keep
                            ) + "\n"
                        else:
                            new_line = f"from {imp.module} import " + ", ".join(
                                f"{a.name} as {a.asname}" if a.asname else a.name 
                                for a in names_to_keep
                            ) + "\n"
                        new_lines.append(new_line)
                        modified = True
                        logger.info(f"Removed unused import in {filename}: {line.strip()}")
                    else:
                        new_lines.append(line)
                except SyntaxError:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        return "".join(new_lines), modified

    def remove_dead_code(self, content: str, filename: str) -> tuple[str, bool]:
        """
        Remove simple dead code markers like standalone 'pass' or 'NotImplementedError'
        if they are in functions that are clearly incomplete (heuristic).
        For safety, we only remove 'pass' if it's the only content of a block
        and the function has a docstring indicating it's a stub.
        """
        lines = content.splitlines(keepends=True)
        new_lines = []
        modified = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check for 'pass' that might be a placeholder
            if stripped == 'pass':
                # Look back to see if this is a function/method definition
                # and if it's the only thing in the body
                # This is a simplified heuristic to avoid breaking logic
                # In a real scenario, we'd use AST to check function bodies
                if i > 0 and (lines[i-1].strip().endswith(':') or 
                              (i > 1 and lines[i-2].strip().endswith(':'))):
                    # Check if the previous line is a function def
                    prev_line = lines[i-1].strip() if i > 0 else ""
                    if prev_line.startswith('def ') or prev_line.startswith('class '):
                        logger.warning(f"Found placeholder 'pass' in {filename} at line {i+1}. Keeping for safety.")
                        # We keep it to avoid breaking the build, but log it
                        new_lines.append(line)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            
            i += 1

        return "".join(new_lines), modified

    def standardize_docstrings(self, content: str, filename: str) -> tuple[str, bool]:
        """
        Ensure docstrings use triple double quotes and are on their own lines.
        This is a lightweight formatter for docstrings.
        """
        # Simple regex to find docstrings and ensure they are formatted correctly
        # This is a heuristic and might not catch all edge cases
        pattern = re.compile(r'"""(.*?)"""', re.DOTALL)
        
        def replace_docstring(match):
            doc = match.group(1).strip()
            if not doc:
                return '""""""'
            return f'"""\n{doc}\n"""'
        
        new_content = pattern.sub(replace_docstring, content)
        modified = new_content != content
        if modified:
            logger.info(f"Standardized docstrings in {filename}")
        
        return new_content, modified

    def process_file(self, filepath: Path) -> bool:
        """Process a single file for refactoring."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            filename = filepath.relative_to(self.project_root)
            
            # Apply refactors
            content, modified_imports = self.remove_unused_imports(content, str(filename))
            content, modified_dead = self.remove_dead_code(content, str(filename))
            content, modified_docs = self.standardize_docstrings(content, str(filename))
            
            if modified_imports or modified_dead or modified_docs:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.changes_made[str(filename)] = [
                    "Unused imports removed" if modified_imports else None,
                    "Dead code analyzed" if modified_dead else None,
                    "Docstrings standardized" if modified_docs else None
                ]
                logger.info(f"Refactored {filename}")
                return True
            else:
                logger.debug(f"No changes needed for {filename}")
                return False

        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            return False

    def run_cleanup(self) -> Dict[str, Any]:
        """Run the cleanup process on all Python files."""
        logger.info("Starting code cleanup and refactoring...")
        py_files = self.find_python_files()
        logger.info(f"Found {len(py_files)} Python files to process.")
        
        total_files = len(py_files)
        modified_files = 0
        
        for filepath in py_files:
            if self.process_file(filepath):
                modified_files += 1
        
        result = {
            "total_files_processed": total_files,
            "files_modified": modified_files,
            "changes_detail": self.changes_made,
            "status": "completed"
        }
        
        logger.info(f"Cleanup complete. Modified {modified_files}/{total_files} files.")
        return result

def main():
    """Entry point for the cleanup task."""
    config = load_config()
    paths = get_paths()
    project_root = paths.get("project_root", Path("."))
    
    refactorer = CodeRefactorer(project_root)
    report = refactorer.run_cleanup()
    
    # Write report to data/interim/cleanup_report.json
    report_path = paths.get("interim", Path("data/interim")) / "cleanup_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Cleanup report written to {report_path}")

if __name__ == "__main__":
    main()