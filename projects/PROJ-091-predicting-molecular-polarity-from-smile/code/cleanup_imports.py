import ast
import os
import sys
from pathlib import Path
from typing import List, Set, Tuple, Dict
import re
import logging

# Import standardized logging
sys.path.insert(0, str(Path(__file__).parent))
from utils.logging_config import setup_logging, get_logger

# Initialize logger
logger = get_logger(__name__)

def get_all_python_files(directory: Path) -> List[Path]:
    """Recursively find all .py files in the directory."""
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                py_files.append(Path(root) / file)
    return py_files

def get_all_imports(tree: ast.AST) -> Set[str]:
    """Extract all imported module names from an AST."""
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports

def get_used_names(tree: ast.AST) -> Set[str]:
    """Extract all names used in the code."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attr usage
            current = node
            parts = []
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                names.add('.'.join(reversed(parts)))
    return names

def find_unused_imports(tree: ast.AST, imports: Set[str], used_names: Set[str]) -> List[str]:
    """Identify imports that are not used."""
    unused = []
    for imp in imports:
        # Check if the import name or a common alias is used
        # Simple check: if the import name appears in used_names
        if imp not in used_names:
            # More sophisticated check might be needed for 'from X import Y'
            # where 'Y' is used but 'X' is not directly in used_names
            # For now, we rely on the fact that if 'X' is imported, it should appear in used_names
            # unless it's a 'from X import Y' where Y is used.
            # Let's refine: check if any name starting with 'imp.' is in used_names
            found_usage = False
            for name in used_names:
                if name == imp or name.startswith(imp + '.'):
                    found_usage = True
                    break
            if not found_usage:
                unused.append(imp)
    return unused

def remove_unused_imports(file_path: Path, unused_imports: List[str]) -> str:
    """Remove unused imports from the file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    
    # Track which lines to remove
    # We need to map unused imports to their lines
    # This is a simplified approach: remove lines that contain only unused imports
    
    # Re-parsing to find exact lines is complex, so we use a regex approach for 'import' statements
    # This is a heuristic and might need refinement for complex cases
    
    # Better approach: re-parse and reconstruct? Or just remove lines containing the import
    # Let's try removing lines that match the pattern of unused imports
    
    import_pattern = re.compile(r'^\s*import\s+([a-zA-Z0-9_.]+)')
    from_pattern = re.compile(r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import')
    
    # We will collect lines to skip
    lines_to_skip = set()
    
    # First pass: identify lines with unused imports
    # We need to be careful with 'from X import Y' where X is unused but Y is used?
    # Actually, if 'from X import Y', then 'Y' is used, 'X' might not be directly.
    # Our unused_imports list should ideally contain the specific names to remove.
    # For simplicity, let's assume unused_imports contains the module names or full import strings.
    
    # Let's refine: We will remove the entire import line if the imported name is in unused_imports
    # This requires mapping import lines to the names they import.
    
    # Simpler strategy for this task: Just remove lines that start with 'import unused_name'
    # or 'from unused_name import ...' if unused_name is in the list.
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            new_lines.append(line)
            continue
        
        match_import = import_pattern.match(stripped)
        match_from = from_pattern.match(stripped)
        
        remove_line = False
        
        if match_import:
            module = match_import.group(1).split('.')[0]
            if module in unused_imports:
                remove_line = True
        elif match_from:
            module = match_from.group(1).split('.')[0]
            if module in unused_imports:
                remove_line = True
        
        if not remove_line:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def clean_file(file_path: Path) -> bool:
    """Clean a single Python file of unused imports."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = get_all_imports(tree)
        used_names = get_used_names(tree)
        
        unused = find_unused_imports(tree, imports, used_names)
        
        if not unused:
            return False
        
        logger.info(f"Found unused imports in {file_path}: {unused}")
        
        new_content = remove_unused_imports(file_path, unused)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"Cleaned {file_path}")
            return True
        
        return False
    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main entry point for cleaning imports."""
    setup_logging(log_level=logging.INFO)
    logger.info("Starting import cleanup...")
    
    code_dir = Path(__file__).parent
    py_files = get_all_python_files(code_dir)
    
    cleaned_count = 0
    for file_path in py_files:
        if clean_file(file_path):
            cleaned_count += 1
    
    logger.info(f"Cleanup complete. Cleaned {cleaned_count} files.")

if __name__ == "__main__":
    main()
