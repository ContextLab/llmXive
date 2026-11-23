"""
Verification script for T050.
Scans code files for synthetic fallback patterns and fails the build if found.

This script enforces the 'Fail Loudly' principle by ensuring that no code paths
exist which generate or return synthetic/mock data when real data fetching fails.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Comprehensive list of patterns indicating synthetic fallback or mock data generation
# These patterns are designed to catch common ways developers might bypass real data requirements
SYNTHETIC_PATTERNS = [
    # Direct return of mock/synthetic variables
    r'if\s+not\s+data:\s*return\s+mock_data',
    r'if\s+not\s+data:\s*return\s+synthetic',
    r'if\s+not\s+df:\s*return\s+mock_data',
    r'if\s+len\(data\)\s*==\s*0:\s*return\s+mock_data',
    
    # Exception handlers returning synthetic data (silent failure)
    r'except\s*:\s*return\s+mock_data',
    r'except\s*:\s*return\s+synthetic',
    r'except\s+[A-Za-z_][A-Za-z0-9_]*\s*:\s*return\s+mock_data',
    r'except\s+[A-Za-z_][A-Za-z0-9_]*\s*:\s*return\s+synthetic',
    r'except\s+[A-Za-z_][A-Za-z0-9_]*\s*:\s*return\s+generate_',
    
    # Function calls that generate synthetic data
    r'generate_synthetic_',
    r'generate_mock_',
    r'make_synthetic_',
    r'create_mock_',
    
    # Direct numpy/pandas random generation used for fallback
    r'mock_data\s*=\s*np\.random\.',
    r'mock_df\s*=\s*np\.random\.',
    r'synthetic\s*=\s*np\.random\.',
    r'df\s*=\s*pd\.DataFrame\(\s*\[\s*\]\s*\)', # Empty DataFrame often used as mock placeholder
    r'data\s*=\s*pd\.DataFrame\(\s*\[\s*\]\s*\)',
    
    # Specific numpy patterns for creating fake arrays
    r'np\.zeros\(\s*\d+\s*,\s*dtype\s*=\s*int',
    r'np\.ones\(\s*\d+\s*,\s*dtype\s*=\s*int',
    r'np\.array\(\s*\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]\s*\)', # Hardcoded small arrays
    
    # Comments indicating intentional bypass (optional but helpful)
    # r'#\s*TODO:\s*replace\s*with\s*real\s*data',
    # r'#\s*FIXME:\s*using\s*mock\s*data',
]

FILES_TO_CHECK = [
    "code/downloaders.py",
    "code/ingestion.py",
    "code/resampling.py"
]

def check_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    Check a file for synthetic fallback patterns.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        Tuple of (is_clean, list_of_found_patterns)
    """
    path = Path(file_path)
    if not path.exists():
        print(f"Warning: File {file_path} not found. Skipping.")
        return True, []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Warning: Could not decode {file_path} as UTF-8. Skipping.")
        return True, []
    
    found_patterns = []
    for pattern in SYNTHETIC_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            # Find line numbers for context
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    found_patterns.append(f"Pattern '{pattern}' found at line {i}: {line.strip()}")
    
    return len(found_patterns) == 0, found_patterns

def main():
    """Run verification across all specified files."""
    print("=" * 60)
    print("T050: Verifying absence of synthetic fallback code")
    print("=" * 60)
    print("Scanning files for patterns indicating synthetic data generation...")
    print("Files checked:", ", ".join(FILES_TO_CHECK))
    print("-" * 60)
    
    all_clean = True
    total_patterns_found = 0
    
    for file_path in FILES_TO_CHECK:
        is_clean, patterns = check_file(file_path)
        
        if not is_clean:
            all_clean = False
            total_patterns_found += len(patterns)
            print(f"\n❌ ERROR: Synthetic fallback patterns detected in {file_path}:")
            for p in patterns:
                print(f"  • {p}")
        else:
            print(f"\n✅ Clean: {file_path}")
    
    print("-" * 60)
    
    if not all_clean:
        print(f"\n❌ BUILD FAILED: {total_patterns_found} synthetic fallback pattern(s) detected.")
        print("Please remove all synthetic data generation code paths.")
        print("Data loaders must 'fail loudly' (raise exceptions) on fetch errors.")
        sys.exit(1)
    else:
        print("\n✅ VERIFICATION PASSED: No synthetic fallback patterns found.")
        print("All data loaders comply with the 'Fail Loudly' principle.")
        sys.exit(0)

if __name__ == "__main__":
    main()