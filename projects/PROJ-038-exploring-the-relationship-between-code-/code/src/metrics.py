"""
Module for extracting code complexity metrics from Java files.
Currently implements Line of Code (LOC) calculation via AST traversal.
Future tasks will add Cyclomatic Complexity and Halstead Volume.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

# Try to import tree-sitter, but allow graceful degradation if not available
# The project plan mentions tree-sitter in requirements, so we assume it's installed
try:
    import tree_sitter_java
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    Language = None
    Parser = None


def calculate_loc_ast(file_path: str) -> int:
    """
    Calculate Lines of Code (LOC) for a Java file using tree-sitter AST traversal.
    
    This counts non-blank, non-comment lines by traversing the AST and identifying
    actual code nodes.
    
    Args:
        file_path: Path to the Java file
        
    Returns:
        int: Number of lines of code (excluding blanks and comments)
    """
    if not TREE_SITTER_AVAILABLE:
        # Fallback to simple line counting if tree-sitter is not available
        return _calculate_loc_simple(file_path)
    
    try:
        # Initialize tree-sitter parser for Java
        java_language = Language(tree_sitter_java.language())
        parser = Parser(java_language)
        
        # Read the file
        with open(file_path, 'rb') as f:
            source_code = f.read()
        
        # Parse the source code
        tree = parser.parse(source_code)
        root_node = tree.root_node
        
        # Traverse the AST to count code lines
        return _count_code_lines_from_ast(root_node, source_code)
        
    except Exception as e:
        # If tree-sitter parsing fails, fall back to simple counting
        print(f"Warning: tree-sitter failed for {file_path}: {e}. Using fallback.")
        return _calculate_loc_simple(file_path)


def _count_code_lines_from_ast(node, source_code: bytes) -> int:
    """
    Recursively count code lines from AST nodes.
    
    Args:
        node: tree-sitter node
        source_code: Original source code as bytes
        
    Returns:
        int: Count of code lines
    """
    # Get the line range for this node
    start_point = node.start_point
    end_point = node.end_point
    
    # Convert to line numbers (0-indexed)
    start_line = start_point[0]
    end_line = end_point[0]
    
    # Count lines covered by this node
    lines_counted = 0
    
    # Get the source text for this node to analyze
    node_text = node.text.decode('utf-8', errors='ignore')
    
    # Check if this node is a comment node
    node_type = node.type
    if node_type in ['line_comment', 'block_comment', 'documentation_comment']:
        return 0  # Don't count comment lines
    
    # For non-comment nodes, count the lines they span
    # But we need to be careful not to double-count
    if start_line == end_line:
        # Single line node
        lines_counted = 1
    else:
        # Multi-line node
        lines_counted = end_line - start_line + 1
    
    # Recursively count children, but avoid double counting
    # by only counting leaf nodes or nodes that add new lines
    child_lines = 0
    for child in node.children:
        child_lines += _count_code_lines_from_ast(child, source_code)
    
    # If we have children, we trust their count more than the span
    # This prevents double counting
    if node.children:
        return child_lines if child_lines > 0 else lines_counted
    
    return lines_counted


def _calculate_loc_simple(file_path: str) -> int:
    """
    Simple LOC calculation as fallback.
    Counts non-blank, non-comment lines.
    
    Args:
        file_path: Path to the Java file
        
    Returns:
        int: Number of lines of code
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        loc = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Handle block comments
            if in_block_comment:
                if '*/' in stripped:
                    in_block_comment = False
                    # Check if there's code after the comment ends
                    after_comment = stripped.split('*/', 1)[1].strip()
                    if after_comment and not after_comment.startswith('//'):
                        loc += 1
                continue
            
            if stripped.startswith('/*'):
                if '*/' in stripped:
                    # Single line block comment
                    continue
                else:
                    in_block_comment = True
                    continue
            
            # Skip single line comments
            if stripped.startswith('//'):
                continue
            
            # Count as code
            loc += 1
        
        return loc
        
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return 0


def calculate_loc_batch(file_paths: List[str]) -> Dict[str, int]:
    """
    Calculate LOC for multiple Java files.
    
    Args:
        file_paths: List of paths to Java files
        
    Returns:
        Dict mapping file path to LOC count
    """
    results = {}
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            results[file_path] = 0
            continue
        
        try:
            loc = calculate_loc_ast(file_path)
            results[file_path] = loc
        except Exception as e:
            print(f"Error calculating LOC for {file_path}: {e}")
            results[file_path] = 0
    
    return results


def main():
    """
    Main function to demonstrate LOC calculation.
    Can be run as a script to process files from a directory.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.metrics <file_or_directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    if os.path.isfile(target):
        if target.endswith('.java'):
            loc = calculate_loc_ast(target)
            print(f"LOC for {target}: {loc}")
        else:
            print(f"Error: {target} is not a Java file")
            sys.exit(1)
    elif os.path.isdir(target):
        java_files = list(Path(target).rglob('*.java'))
        if not java_files:
            print(f"No Java files found in {target}")
            sys.exit(0)
        
        results = calculate_loc_batch([str(f) for f in java_files])
        
        total_loc = sum(results.values())
        print(f"Processed {len(results)} Java files")
        print(f"Total LOC: {total_loc}")
        print(f"Average LOC per file: {total_loc / len(results):.2f}")
        
        # Show top 5 largest files
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        print("\nTop 5 largest files:")
        for path, loc in sorted_results[:5]:
            print(f"  {path}: {loc}")
    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)


if __name__ == '__main__':
    main()
