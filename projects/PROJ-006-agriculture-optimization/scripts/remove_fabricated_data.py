"""
Utility script to remove fabricated data from validate_dataset_schema.py.

This script removes the fabricated/dummy data generation code that was flagged
as a fabrication violation.
"""
import re
from pathlib import Path

def fix_validate_dataset_schema():
    script_path = Path("code/scripts/validate_dataset_schema.py")
    
    if not script_path.exists():
        print(f"File not found: {script_path}")
        return False
    
    content = script_path.read_text()
    
    # Remove fabricated data generation
    # Look for patterns like "Provide dummy values" or "random.uniform"
    lines = content.split('\n')
    clean_lines = []
    in_fabricated_block = False
    
    for line in lines:
        # Detect start of fabricated block
        if 'Provide dummy values' in line or 'dummy values' in line.lower():
            in_fabricated_block = True
            continue
        
        # Detect end of fabricated block (when we hit a real function or comment)
        if in_fabricated_block:
            if line.strip().startswith('def ') or line.strip().startswith('# ') or line.strip() == '':
                in_fabricated_block = False
                if line.strip().startswith('def '):
                    clean_lines.append(line)
            continue
        
        # Skip lines with random.uniform or np.random
        if 'random.uniform' in line or 'np.random' in line or 'random.randint' in line:
            continue
        
        clean_lines.append(line)
    
    # Write cleaned content
    script_path.write_text('\n'.join(clean_lines))
    print(f"Removed fabricated data from {script_path}")
    return True

if __name__ == "__main__":
    fix_validate_dataset_schema()
