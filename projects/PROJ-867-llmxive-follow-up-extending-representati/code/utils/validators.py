"""
JSON/Markdown syntax parsing and AST edit distance calculation.

This module provides validators for ensuring syntactic correctness of
structured text outputs (JSON and Markdown) and calculates the
Abstract Syntax Tree (AST) edit distance between two documents.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from difflib import SequenceMatcher
import ast

# Optional markdown parsing - handled gracefully if not installed
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    # Fallback: basic regex validation for markdown
    pass


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


def validate_json_syntax(text: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate JSON syntax and parse if valid.

    Args:
        text: The string to validate as JSON.

    Returns:
        Tuple of (is_valid, parsed_data, error_message)
    """
    if not text or not isinstance(text, str):
        return False, None, "Input must be a non-empty string"

    try:
        parsed = json.loads(text)
        return True, parsed, None
    except json.JSONDecodeError as e:
        return False, None, f"JSON decode error: {str(e)}"


def validate_markdown_syntax(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Markdown syntax.

    Uses the 'markdown' library for full parsing if available,
    otherwise falls back to basic structural checks.

    Args:
        text: The string to validate as Markdown.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not isinstance(text, str):
        return False, "Input must be a non-empty string"

    if HAS_MARKDOWN:
        try:
            # Try to convert to HTML to validate syntax
            html = markdown.markdown(text)
            if not html:
                # Empty output might indicate severe syntax issues
                # but markdown library often returns empty for valid empty docs
                pass
            return True, None
        except Exception as e:
            return False, f"Markdown parsing error: {str(e)}"
    else:
        # Fallback: basic structural validation
        # Check for balanced brackets/parentheses (very basic)
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        for char in text:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack or brackets[stack[-1]] != char:
                    return False, f"Unbalanced bracket: {char}"
                stack.pop()

        # Check for unclosed brackets
        if stack:
            return False, f"Unclosed brackets: {stack}"

        return True, None


def parse_json_ast(text: str) -> Any:
    """
    Parse JSON into a Python object (acting as AST representation).

    Args:
        text: JSON string.

    Returns:
        Parsed Python object (dict, list, str, int, float, bool, None).
    """
    is_valid, parsed, error = validate_json_syntax(text)
    if not is_valid:
        raise ValidationError(f"Invalid JSON: {error}")
    return parsed


def parse_markdown_ast(text: str) -> List[Dict[str, Any]]:
    """
    Parse Markdown into a simplified AST representation.

    Converts Markdown into a list of block elements with their types.
    Since 'markdown' library doesn't expose AST directly, we use a
    heuristic approach to identify block structures.

    Args:
        text: Markdown string.

    Returns:
        List of dictionaries representing block elements.
    """
    if not HAS_MARKDOWN:
        # Basic regex-based parser if library not available
        blocks = []
        lines = text.split('\n')
        current_block = {'type': 'text', 'content': []}

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_block['content']:
                    blocks.append(current_block)
                    current_block = {'type': 'text', 'content': []}
                continue

            # Header detection
            header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            if header_match:
                if current_block['content']:
                    blocks.append(current_block)
                    current_block = {'type': 'text', 'content': []}
                level = len(header_match.group(1))
                blocks.append({
                    'type': f'header_{level}',
                    'content': header_match.group(2)
                })
                continue

            # List item detection
            list_match = re.match(r'^[\*\-\+]\s+(.+)$', stripped)
            if list_match:
                if current_block['type'] != 'list':
                    if current_block['content']:
                        blocks.append(current_block)
                    current_block = {'type': 'list', 'items': []}
                current_block['items'].append(list_match.group(1))
                continue

            # Code block detection
            if stripped.startswith('```'):
                if current_block['content']:
                    blocks.append(current_block)
                    current_block = {'type': 'text', 'content': []}
                blocks.append({
                    'type': 'code_block',
                    'content': stripped[3:].strip()
                })
                continue

            # Default: text
            current_block['content'].append(stripped)

        if current_block['content']:
            blocks.append(current_block)

        return blocks

    # Full parsing with markdown library
    try:
        html = markdown.markdown(text)
        # Since markdown library doesn't expose AST, we return a simplified
        # representation based on HTML structure analysis
        blocks = []

        # Simple HTML tag-based parsing for AST representation
        # This is a simplified approach; for production, consider using
        # a dedicated markdown AST parser like 'markdown-it-py'
        current_block = {'type': 'text', 'content': ''}

        # Split by common block elements
        lines = text.split('\n')
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_block['content']:
                    blocks.append(current_block)
                    current_block = {'type': 'text', 'content': ''}
                continue

            header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            if header_match:
                if current_block['content']:
                    blocks.append(current_block)
                    current_block = {'type': 'text', 'content': ''}
                level = len(header_match.group(1))
                blocks.append({
                    'type': f'header_{level}',
                    'content': header_match.group(2)
                })
                continue

            list_match = re.match(r'^[\*\-\+]\s+(.+)$', stripped)
            if list_match:
                if current_block['type'] != 'list':
                    if current_block['content']:
                        blocks.append(current_block)
                    current_block = {'type': 'list', 'items': []}
                current_block['items'].append(list_match.group(1))
                continue

            current_block['content'] += ' ' + stripped

        if current_block['content']:
            blocks.append(current_block)

        return blocks
    except Exception as e:
        raise ValidationError(f"Failed to parse Markdown: {str(e)}")


def ast_edit_distance(ast1: Any, ast2: Any) -> int:
    """
    Calculate the edit distance between two AST representations.

    Uses a simplified tree edit distance algorithm based on
    serialized representations for efficiency. For complex nested
    structures, this provides a reasonable approximation.

    Args:
        ast1: First AST (parsed JSON or Markdown block list).
        ast2: Second AST.

    Returns:
        Integer edit distance (number of operations to transform ast1 to ast2).
    """
    # Serialize ASTs to comparable strings
    try:
        str1 = json.dumps(ast1, sort_keys=True) if not isinstance(ast1, list) else json.dumps(ast1, sort_keys=True)
        str2 = json.dumps(ast2, sort_keys=True) if not isinstance(ast2, list) else json.dumps(ast2, sort_keys=True)
    except (TypeError, ValueError):
        # Fallback for non-serializable objects
        str1 = str(ast1)
        str2 = str(ast2)

    if str1 == str2:
        return 0

    # Use SequenceMatcher for a reasonable approximation
    matcher = SequenceMatcher(None, str1, str2)
    ratio = matcher.ratio()

    # Convert similarity ratio to edit distance
    # This is an approximation; exact tree edit distance is O(n^3)
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 0

    # Estimate edit distance based on difference ratio
    diff_ratio = 1.0 - ratio
    estimated_distance = int(diff_ratio * max_len)

    # Ensure at least 1 if strings are different
    return max(1, estimated_distance)


def calculate_json_edit_distance(json1: str, json2: str) -> int:
    """
    Calculate AST edit distance between two JSON strings.

    Args:
        json1: First JSON string.
        json2: Second JSON string.

    Returns:
        Integer edit distance.

    Raises:
        ValidationError: If either JSON is invalid.
    """
    ast1 = parse_json_ast(json1)
    ast2 = parse_json_ast(json2)
    return ast_edit_distance(ast1, ast2)


def calculate_markdown_edit_distance(md1: str, md2: str) -> int:
    """
    Calculate AST edit distance between two Markdown strings.

    Args:
        md1: First Markdown string.
        md2: Second Markdown string.

    Returns:
        Integer edit distance.

    Raises:
        ValidationError: If either Markdown is invalid.
    """
    is_valid1, error1 = validate_markdown_syntax(md1)
    if not is_valid1:
        raise ValidationError(f"Invalid Markdown 1: {error1}")

    is_valid2, error2 = validate_markdown_syntax(md2)
    if not is_valid2:
        raise ValidationError(f"Invalid Markdown 2: {error2}")

    ast1 = parse_markdown_ast(md1)
    ast2 = parse_markdown_ast(md2)
    return ast_edit_distance(ast1, ast2)


def validate_structured_output(text: str, format_type: str = 'json') -> Tuple[bool, Optional[str]]:
    """
    Generic validator for structured text outputs.

    Args:
        text: The text to validate.
        format_type: Either 'json' or 'markdown'.

    Returns:
        Tuple of (is_valid, error_message).
    """
    format_type = format_type.lower()

    if format_type == 'json':
        return validate_json_syntax(text)[:2]
    elif format_type == 'markdown':
        return validate_markdown_syntax(text)
    else:
        raise ValidationError(f"Unsupported format type: {format_type}. Use 'json' or 'markdown'.")


def main():
    """
    Command-line interface for validators.
    Usage: python -m code.utils.validators [validate|edit_distance] [format] [file1] [file2]
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.validators [validate|edit_distance] [json|markdown] [file1] [file2]")
        sys.exit(1)

    command = sys.argv[1]
    format_type = sys.argv[2]

    if command == 'validate':
        if len(sys.argv) < 4:
            print("Error: File path required for validation")
            sys.exit(1)

        file_path = sys.argv[3]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            is_valid, error = validate_structured_output(content, format_type)
            if is_valid:
                print(f"✓ {file_path} is valid {format_type}")
                sys.exit(0)
            else:
                print(f"✗ {file_path} is invalid: {error}")
                sys.exit(1)
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

    elif command == 'edit_distance':
        if len(sys.argv) < 5:
            print("Error: Two file paths required for edit distance calculation")
            sys.exit(1)

        file1 = sys.argv[3]
        file2 = sys.argv[4]

        try:
            with open(file1, 'r', encoding='utf-8') as f:
                content1 = f.read()
            with open(file2, 'r', encoding='utf-8') as f:
                content2 = f.read()

            if format_type == 'json':
                distance = calculate_json_edit_distance(content1, content2)
            elif format_type == 'markdown':
                distance = calculate_markdown_edit_distance(content1, content2)
            else:
                print(f"Error: Unsupported format type: {format_type}")
                sys.exit(1)

            print(f"AST Edit Distance ({format_type}): {distance}")
            sys.exit(0)
        except FileNotFoundError as e:
            print(f"Error: File not found: {str(e)}")
            sys.exit(1)
        except ValidationError as e:
            print(f"Validation Error: {str(e)}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()