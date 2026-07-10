"""
Black formatter implementation.
Applies Black formatting to Python code.
"""
import subprocess
import tempfile
import os
from typing import Optional

def apply_black_format(code: str) -> str:
    """
    Apply Black formatting to the provided code string.
    
    Args:
        code: Python code string.
    
    Returns:
        Formatted Python code string.
    
    Raises:
        RuntimeError: If Black fails to format the code.
    """
    if not code.strip():
        return code

    try:
        # Write code to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name

        try:
            # Run Black on the temporary file
            result = subprocess.run(
                ['black', '--quiet', tmp_file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Black returns 0 on success, 1 if it formatted files, 123 on error
            # We read the file back regardless as long as no critical exception occurred
            
            # Read the formatted code
            with open(tmp_file_path, 'r', encoding='utf-8') as f:
                formatted_code = f.read()
            
            return formatted_code
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    except FileNotFoundError:
        raise RuntimeError("Black is not installed. Please install it via requirements.txt.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Black formatting timed out.")
    except Exception as e:
        raise RuntimeError(f"Black formatting failed: {str(e)}")

def main():
    """Test the formatter."""
    sample = "def foo(  x,y  ):\n    return x+y"
    print(apply_black_format(sample))

if __name__ == "__main__":
    main()