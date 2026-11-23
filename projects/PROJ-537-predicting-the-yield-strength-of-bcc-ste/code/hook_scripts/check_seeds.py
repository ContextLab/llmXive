#!/usr/bin/env python3
"""
Git hook script to verify that random seeds are properly set in the codebase.
Ensures reproducibility by checking for explicit seed definitions.
"""
import os
import sys
import re
from pathlib import Path

# Pattern to match seed assignments in Python files
# Matches: random.seed(42), np.random.seed(42), set_seed(42), etc.
SEED_PATTERNS = [
    r'\brandom\.seed\s*\(\s*\d+\s*\)',
    r'\bnp\.random\.seed\s*\(\s*\d+\s*\)',
    r'\bnumpy\.random\.seed\s*\(\s*\d+\s*\)',
    r'\bset_seed\s*\(\s*\d+\s*\)',
    r'\bseed\s*=\s*\d+',
    r'\bRANDOM_SEED\s*=\s*\d+',
]

def find_python_files(root_dir):
    """Find all Python files in the given directory."""
    python_files = []
    for root, _, files in os.walk(root_dir):
        # Skip common non-code directories
        if any(skip in root for skip in ['.git', '__pycache__', 'venv', 'env', '.venv']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def check_seeds_in_file(filepath):
    """Check if a file contains proper seed initialization."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for seed patterns
        for pattern in SEED_PATTERNS:
            if re.search(pattern, content):
                return True, f"Found seed pattern: {pattern}"
        
        # Special case: Check if file is config.py or imports from config
        if 'config.py' in filepath or 'config' in filepath:
            # Config files often define seeds at module level
            if re.search(r'\bSEED\s*=\s*\d+', content) or re.search(r'\bRANDOM_SEED\s*=\s*\d+', content):
                return True, "Config file with seed definition"
        
        return False, "No seed initialization found"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def main():
    """Main hook function."""
    repo_root = Path(__file__).parent.parent.parent
    code_dir = repo_root / 'code'
    
    if not code_dir.exists():
        print("Warning: code/ directory not found. Skipping seed check.")
        return 0
    
    python_files = find_python_files(str(code_dir))
    files_without_seeds = []
    
    print("Checking for random seed initialization...")
    
    for filepath in python_files:
        has_seed, message = check_seeds_in_file(filepath)
        if not has_seed:
            # Check if it's a test file or utility that might not need seeds
            if 'test' not in filepath and 'utils' not in filepath and 'setup' not in filepath:
                files_without_seeds.append((filepath, message))
    
    if files_without_seeds:
        print("\n❌ WARNING: The following files do not have explicit seed initialization:")
        for filepath, message in files_without_seeds:
            print(f"  - {filepath}: {message}")
        print("\nPlease ensure random seeds are set for reproducibility.")
        print("Add 'random.seed(42)' or 'np.random.seed(42)' at the beginning of your scripts.")
        print("Or define SEED = 42 in your config.")
        # Return 0 to allow commit (warning only, not blocking)
        return 0
    
    print("✅ All checked files have proper seed initialization.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
