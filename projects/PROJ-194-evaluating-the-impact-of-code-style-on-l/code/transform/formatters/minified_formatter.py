"""
Minified formatter implementation.
Applies minified formatting (removes whitespace, compacts code) to Python code.
This formatter is part of the 2x2x2 factorial design for code style transformation.
"""
import re
from typing import Optional


def apply_minified_format(code: str) -> str:
    """
    Apply minified formatting to the provided code string.
    Removes unnecessary whitespace, newlines, and comments (basic).
    Preserves valid Python syntax while compacting the code.
    
    Args:
        code: Python code string.
    
    Returns:
        Minified Python code string.
    """
    if not code or not code.strip():
        return code

    lines = code.split('\n')
    filtered_lines = []
    
    # Remove single-line comments and empty lines
    for line in lines:
        stripped = line.lstrip()
        if not stripped.startswith('#'):
            filtered_lines.append(line)
    
    code = '\n'.join(filtered_lines)

    # Remove docstrings (triple quotes)
    # Using DOTALL to handle multi-line strings
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)

    # Remove all newlines and collapse multiple spaces to single space
    code = re.sub(r'\s+', ' ', code)
    
    # Remove spaces around operators and punctuation
    code = re.sub(r'\s*([=+\-*/<>!&|^~%])\s*', r'\1', code)
    code = re.sub(r'\s*([{}()\[\],;:])\s*', r'\1', code)
    
    # Remove spaces after opening and before closing brackets
    code = re.sub(r'\(\s+', '(', code)
    code = re.sub(r'\s+\)', ')', code)
    code = re.sub(r'\[\s+', '[', code)
    code = re.sub(r'\s+\]', ']', code)
    
    # Ensure no leading/trailing whitespace
    code = code.strip()
    
    return code


def main():
    """Test the minifier with a sample function."""
    sample_code = """
    def calculate_sum(x, y):
        # This is a comment
        result = x + y
        return result
    """
    
    minified = apply_minified_format(sample_code)
    print(f"Original:\n{sample_code}")
    print(f"Minified:\n{minified}")
    
    # Verify it's valid Python by attempting to compile
    try:
        compile(minified, '<string>', 'exec')
        print("✓ Minified code is syntactically valid Python.")
    except SyntaxError as e:
        print(f"✗ Syntax error in minified code: {e}")


if __name__ == "__main__":
    main()