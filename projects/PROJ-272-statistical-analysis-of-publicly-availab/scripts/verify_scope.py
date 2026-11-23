"""
T000: SPEC & PLAN VERIFICATION (AUTOMATED)

This script verifies that "DementiaBank" appears ONLY in exclusion contexts
in spec.md and plan.md, and NEVER in active data source lists or code paths.

Gate Logic:
- If "DementiaBank" is found as an active source -> exit 1, print error
- If "DementiaBank" is found only in exclusion contexts -> exit 0
- If "DementiaBank" is not found at all -> exit 0 (assuming default exclusion)
"""

import re
import sys
from pathlib import Path


# Exclusion patterns (case-insensitive)
EXCLUSION_PATTERNS = [
    r'exclud',
    r'not\s+used',
    r'remov',
    r'out\s+of\s+scope',
    r'not\s+part\s+of',
    r'excluded\s+from',
    r'do\s+not\s+use',
    r'ignore',
    r'omitted',
]

# Active source patterns (case-insensitive)
ACTIVE_SOURCE_PATTERNS = [
    r'use.*dementia',
    r'fetch.*dementia',
    r'load.*dementia',
    r'download.*dementia',
    r'import.*dementia',
    r'data\s+source.*dementia',
    r'source.*dementia',
    r'dataset.*dementia',
    r'dementia.*bank',
    r'include.*dementia',
    r'add.*dementia',
    r'process.*dementia',
]

def find_dementiabank_references(file_path: Path) -> list:
    """
    Find all occurrences of 'DementiaBank' in a file with context.
    Returns a list of tuples: (line_number, line_content, context_type)
    """
    references = []
    
    if not file_path.exists():
        return references
        
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return references
    
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        # Case-insensitive search for "DementiaBank" or "dementiabank"
        if re.search(r'dementiabank', line, re.IGNORECASE):
            references.append((i, line))
    
    return references

def classify_context(line: str) -> str:
    """
    Classify whether a line containing 'DementiaBank' is an exclusion or active usage.
    Returns: 'exclusion', 'active', or 'ambiguous'
    """
    line_lower = line.lower()
    
    # Check for exclusion context
    for pattern in EXCLUSION_PATTERNS:
        if re.search(pattern, line_lower):
            return 'exclusion'
    
    # Check for active source context
    for pattern in ACTIVE_SOURCE_PATTERNS:
        if re.search(pattern, line_lower):
            return 'active'
    
    return 'ambiguous'

def verify_file(file_path: Path) -> tuple:
    """
    Verify a single file for DementiaBank usage.
    Returns: (has_active_source, exclusion_count, references)
    """
    references = find_dementiabank_references(file_path)
    
    if not references:
        return (False, 0, [])
    
    has_active = False
    exclusion_count = 0
    
    for line_num, line_content in references:
        context = classify_context(line_content)
        if context == 'active':
            has_active = True
        elif context == 'exclusion':
            exclusion_count += 1
    
    return (has_active, exclusion_count, references)

def main():
    """Main verification logic."""
    project_root = Path(__file__).parent.parent
    spec_path = project_root / 'specs' / '001-statistical-cognitive-decline' / 'spec.md'
    plan_path = project_root / 'specs' / '001-statistical-cognitive-decline' / 'plan.md'
    
    # Also check tasks.md if it exists in the project root
    tasks_path = project_root / 'tasks.md'
    
    files_to_check = [spec_path, plan_path]
    if tasks_path.exists():
        files_to_check.append(tasks_path)
    
    total_active = 0
    total_exclusions = 0
    all_violations = []
    
    print("=== DementiaBank Scope Verification ===")
    print(f"Checking files: {[str(f.relative_to(project_root)) for f in files_to_check]}")
    print()
    
    for file_path in files_to_check:
        if not file_path.exists():
            print(f"Warning: {file_path} not found, skipping.")
            continue
        
        print(f"Checking: {file_path.name}")
        has_active, exclusion_count, references = verify_file(file_path)
        
        if has_active:
            total_active += 1
            for line_num, line_content in references:
                context = classify_context(line_content)
                if context == 'active':
                    all_violations.append({
                        'file': str(file_path.relative_to(project_root)),
                        'line': line_num,
                        'content': line_content.strip()
                    })
        
        total_exclusions += exclusion_count
        
        if references:
            print(f"  Found {len(references)} reference(s), {exclusion_count} in exclusion context(s)")
            for line_num, line_content in references:
                context = classify_context(line_content)
                print(f"    Line {line_num}: [{context}] {line_content.strip()[:80]}...")
        else:
            print(f"  No references found")
        print()
    
    # Final verdict
    if total_active > 0:
        print("ERROR: DementiaBank found as active source. Aborting.")
        print("\nViolations found:")
        for v in all_violations:
            print(f"  - {v['file']}:{v['line']}")
            print(f"    {v['content']}")
        sys.exit(1)
    else:
        if total_exclusions > 0:
            print("SUCCESS: DementiaBank found only in exclusion contexts.")
        else:
            print("SUCCESS: DementiaBank not found (default exclusion assumed).")
        print(f"Total exclusions found: {total_exclusions}")
        sys.exit(0)

if __name__ == '__main__':
    main()
