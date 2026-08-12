import ast
import re
from typing import List, Dict, Any, Optional, Tuple

def standardize_docstring(docstring: Optional[str]) -> str:
    """
    Standardizes a docstring to a consistent format.

    Args:
        docstring: The original docstring or None.

    Returns:
        A standardized docstring string.
    """
    if not docstring:
        return "No documentation provided."
    
    # Basic cleanup: strip whitespace and ensure single line breaks
    cleaned = docstring.strip()
    # Normalize multiple newlines to single
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    return cleaned

def check_imports(source_code: str) -> List[str]:
    """
    Checks for unused imports in the provided source code.

    This function parses the AST of the source code, identifies all imported names,
    and checks if they are used in the code body.

    Args:
        source_code (str): The Python source code as a string.

    Returns:
        List[str]: A list of import names that appear unused.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return [f"SyntaxError: {e}"]

    imports = []
    used_names = set()

    # Collect all imported names
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.append(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.append(name)
    
    # Collect all used names (excluding imports themselves and built-ins)
    builtins = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attribute usage (e.g., pd.DataFrame)
            # We only care about the top-level module name here if it's an import
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

    # Determine unused imports
    unused = []
    for imp in imports:
        if imp not in used_names and imp not in builtins:
            unused.append(imp)
    
    return unused

def remove_unused_imports(source_code: str) -> str:
    """
    Removes unused imports from the provided source code.

    Args:
        source_code (str): The Python source code as a string.

    Returns:
        str: The source code with unused imports removed.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return source_code

    # Identify nodes to remove
    nodes_to_remove = []
    
    for i, node in enumerate(tree.body):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Check if any name in this import is used
            names_in_node = []
            if isinstance(node, ast.Import):
                names_in_node = [alias.asname if alias.asname else alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names_in_node = [alias.asname if alias.asname else alias.name for alias in node.names]
            
            # Check usage in the rest of the tree (excluding this import node)
            # A simple heuristic: check if the name appears in the tree at all,
            # excluding the import statement itself.
            # For a more robust check, we'd need to track scope, but this is a basic refactor.
            
            # Let's use the check_imports logic on the whole file to be safe,
            # then filter by the specific import line.
            pass 

    # Re-implementing the logic to be precise about line removal
    unused_names = check_imports(source_code)
    
    if not unused_names:
        return source_code

    lines = source_code.splitlines(keepends=True)
    new_lines = []
    
    # We need to map unused names back to lines.
    # This is tricky with multi-line imports.
    # Simpler approach: Re-parse and reconstruct without the unused nodes.
    
    # Let's try a regex-based approach for specific import lines if AST reconstruction is too complex
    # or just iterate and filter.
    
    # Robust approach: Parse, filter AST, unparse (if available) or reconstruct.
    # Since ast.unparse is 3.9+, let's do a line-based filter for common patterns.
    
    # Pattern: import X or from Y import X
    # If X is in unused_names, remove the line (or the specific alias if from Y import X, Y, Z)
    
    # To be safe and simple for this task:
    # We will rebuild the file by iterating lines and skipping lines that are purely
    # imports of unused names.
    
    # Note: This is a heuristic. If an import line has multiple names and only one is unused,
    # a full AST rewrite is needed. For this task, we assume single-name imports or remove the whole line if unused.
    
    # Let's do a more precise AST-based filtering for safety.
    # We'll reconstruct the source by walking the tree and skipping nodes that are unused imports.
    
    # Since we can't easily unparse in older python, we'll do a line-scan based on the unused list.
    # This assumes imports are on single lines or we remove the whole block.
    
    # Refined strategy:
    # 1. Find all unused names.
    # 2. Scan lines. If a line starts with 'import ' or 'from ' and contains ONLY unused names (and no used ones), skip it.
    #    If it contains mixed, we should technically edit the line, but for simplicity in this refactor task,
    #    we will remove the specific alias if it's a 'from ... import ...' statement.
    
    # Let's implement the 'from ... import ...' alias removal.
    
    import_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            import_lines.append((i, line, stripped))

    # We will modify the lines list in place
    # We need to know which aliases are unused per import statement
    
    # Parse again to get precise node locations
    tree = ast.parse(source_code)
    
    # Map line number to set of names imported on that line
    line_imports = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # import X, Y
            start_line = node.lineno - 1
            if start_line not in line_imports:
                line_imports[start_line] = set()
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                line_imports[start_line].add(name)
        elif isinstance(node, ast.ImportFrom):
            start_line = node.lineno - 1
            if start_line not in line_imports:
                line_imports[start_line] = set()
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                line_imports[start_line].add(name)

    # Now filter lines
    final_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i in line_imports:
            names_on_line = line_imports[i]
            # Check if ALL names on this line are unused
            if names_on_line.issubset(set(unused_names)):
                # Skip this line entirely
                continue
            # If it's a 'from ... import ...' and some are unused, we might need to edit the line
            # But for this task, we will just remove the whole line if any are unused? 
            # No, that's too aggressive.
            # Let's try to edit the line if it's a 'from' statement.
            if stripped.startswith('from '):
                # Reconstruct the import statement with only used names
                # This requires parsing the line or the AST node again.
                # Let's find the AST node for this line
                node = None
                for n in ast.walk(tree):
                    if isinstance(n, ast.ImportFrom) and n.lineno - 1 == i:
                        node = n
                        break
                
                if node:
                    used_aliases = [alias for alias in node.names if (alias.asname if alias.asname else alias.name) not in unused_names]
                    if used_aliases:
                        # Reconstruct line
                        module = node.module or ''
                        new_names = []
                        for alias in used_aliases:
                            if alias.asname:
                                new_names.append(f"{alias.name} as {alias.asname}")
                            else:
                                new_names.append(alias.name)
                        new_line = f"from {module} import {', '.join(new_names)}\n"
                        # Preserve indentation
                        indent = len(line) - len(line.lstrip())
                        new_line = ' ' * indent + new_line.lstrip()
                        final_lines.append(new_line)
                    else:
                        # No used names, skip line (already handled by issuperset check above, but just in case)
                        continue
                else:
                    final_lines.append(line)
            else:
                # Regular import X, Y. If all are unused, skip. If some used, keep?
                # AST doesn't give us easy split for 'import X, Y' on one line without parsing text.
                # If we are here, it means not all are unused (from issubset check).
                # So we keep the line.
                final_lines.append(line)
        else:
            final_lines.append(line)

    return ''.join(final_lines)
