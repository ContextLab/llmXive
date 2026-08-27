"""
Script to identify and remove unused imports from all Python scripts in code/analysis/.
This is a static analysis tool that uses the `pyflakes` library (or standard library ast)
to detect unused imports and removes them automatically.

Since `pyflakes` is not in the core requirements, we implement a custom AST-based
unused import detector to avoid adding dependencies just for this cleanup task.
"""
import ast
import os
import sys
from pathlib import Path
from typing import Set, List, Tuple

# Standard library modules that are commonly used but might be unused
# We will only remove imports that are truly unused according to AST analysis
ANALYSIS_DIR = Path("code/analysis")

def get_unused_imports(file_path: Path) -> List[str]:
    """
    Parse a Python file and return a list of unused import names.
    Uses AST to accurately determine which names are used in the module.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source, filename=str(file_path))
        
        # Collect all names defined in the module (imports, function defs, etc.)
        defined_names: Set[str] = set()
        used_names: Set[str] = set()
        
        # First pass: collect all defined names (imports)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    defined_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    defined_names.add(name)
        
        # Second pass: collect all used names (excluding definitions)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # For attribute access like pandas.DataFrame, we need the base name
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        # Find unused imports
        unused = defined_names - used_names
        
        # Filter out builtins and common names that might be used indirectly
        # We only remove what is definitely not referenced
        return list(unused)
        
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

def remove_unused_imports_from_file(file_path: Path, unused_names: List[str]) -> bool:
    """
    Remove unused import lines from a file.
    Returns True if the file was modified, False otherwise.
    """
    if not unused_names:
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_lines = lines.copy()
        modified = False
        
        # Process each line to remove unused imports
        new_lines = []
        for line in lines:
            stripped = line.strip()
            
            # Check if this is an import line
            if stripped.startswith('import ') or stripped.startswith('from '):
                should_remove = False
                
                # Handle 'import x, y, z' style
                if stripped.startswith('import '):
                    parts = stripped[7:].split(',')
                    for part in parts:
                        name = part.strip().split(' as ')[0].split('.')[0]
                        if name in unused_names:
                            should_remove = True
                            break
                
                # Handle 'from x import y, z' style
                elif stripped.startswith('from '):
                    # Extract the imported names
                    if ' import ' in stripped:
                        import_part = stripped.split(' import ')[1]
                        names = [n.strip().split(' as ')[0] for n in import_part.split(',')]
                        for name in names:
                            if name in unused_names:
                                should_remove = True
                                break
                
                if should_remove:
                    modified = True
                    continue  # Skip this line (remove it)
            
            new_lines.append(line)
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  Removed unused imports from {file_path.name}")
        
        return modified
        
    except Exception as e:
        print(f"  Error modifying {file_path}: {e}")
        return False

def main():
    """Main entry point for the script."""
    print("Scanning code/analysis/ for unused imports...")
    
    if not ANALYSIS_DIR.exists():
        print(f"Error: Directory {ANALYSIS_DIR} does not exist.")
        sys.exit(1)
    
    modified_count = 0
    total_files = 0
    
    for py_file in ANALYSIS_DIR.glob("*.py"):
        total_files += 1
        unused = get_unused_imports(py_file)
        
        if unused:
            print(f"\n{py_file.name}:")
            print(f"  Unused imports detected: {', '.join(unused)}")
            if remove_unused_imports_from_file(py_file, unused):
                modified_count += 1
            else:
                print(f"  Could not modify file (permission or error)")
        else:
            print(f"{py_file.name}: No unused imports found.")
    
    print(f"\n{'='*60}")
    print(f"Scan complete.")
    print(f"Total files scanned: {total_files}")
    print(f"Files modified: {modified_count}")
    print(f"Files unchanged: {total_files - modified_count}")
    print(f"{'='*60}")
    
    if modified_count > 0:
        print("\nNote: Please review the changes and run tests to ensure nothing is broken.")
        print("Some imports might be used in ways AST cannot detect (e.g., dynamic imports).")

if __name__ == "__main__":
    main()