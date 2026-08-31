"""
Fix missing 'sys' import in preprocess.py which caused a NameError during execution.
This script modifies code/preprocess.py to ensure 'sys' is imported.
"""
import os
import re
from pathlib import Path

def fix_preprocess_imports():
    preprocess_path = Path("code/preprocess.py")
    if not preprocess_path.exists():
        print(f"Error: {preprocess_path} not found.")
        return False

    content = preprocess_path.read_text()
    
    # Check if 'sys' is already imported
    if 'import sys' in content:
        print("sys is already imported in preprocess.py")
        return True

    # Insert 'import sys' after 'import os'
    # Pattern to match 'import os' line
    pattern = r'(import os)'
    replacement = r'\1\nimport sys'
    
    new_content = re.sub(pattern, replacement, content, count=1)
    
    if new_content == content:
        # Fallback: just add to the top if pattern fails
        lines = content.splitlines()
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if line.strip() == 'import os' and not inserted:
                new_lines.append('import sys')
                inserted = True
        if not inserted:
            # If still not found, prepend
            new_lines.insert(0, 'import sys')
        new_content = '\n'.join(new_lines)

    preprocess_path.write_text(new_content)
    print("Fixed: Added 'import sys' to code/preprocess.py")
    return True

if __name__ == "__main__":
    success = fix_preprocess_imports()
    exit(0 if success else 1)
