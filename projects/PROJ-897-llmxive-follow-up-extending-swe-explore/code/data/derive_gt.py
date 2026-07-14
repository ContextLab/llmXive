"""
Derive ground truth line numbers from solution patches.

This module parses the solution patches from the SWE-Explore benchmark dataset
to identify the specific line numbers in the original file that were modified
or added. These lines constitute the 'ground truth' for retrieval evaluation.

The output is a JSONL file where each record contains:
- issue_id: The unique identifier for the issue
- file_path: The path to the file being modified
- ground_truth_lines: A list of 1-based line numbers that represent the fix.
- original_hash: SHA256 hash of the original file content (for verification)
- patch_hash: SHA256 hash of the patch content (for versioning)
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project config
from config import get_config_summary
from utils.validation import validate_jsonl_against_schema, load_schema

# Attempt to import diff parsing library; fallback to manual parsing if needed
try:
    import unidiff
    HAS_UNIDIFF = True
except ImportError:
    HAS_UNIDIFF = False
    # Fallback: We will implement a basic patch parser if unidiff is missing
    # This ensures the script runs even if the dependency isn't strictly pinned yet
    # though T002 should have included it.
    pass


def compute_sha256(content: str) -> str:
    """Compute SHA256 hash of a string."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def parse_patch_basic(patch_text: str, original_lines: List[str]) -> List[int]:
    """
    Fallback parser for unified diffs if unidiff is not available.
    Parses + lines to determine 1-based line numbers in the original file.
    
    Note: This is a simplified parser. It assumes standard unified diff format.
    It maps added lines to the nearest original line context or calculates
    based on hunk headers.
    """
    if HAS_UNIDIFF:
        return [] # Should not happen if unidiff is available

    ground_truth_lines = set()
    lines = patch_text.splitlines()
    current_orig_line = 0
    in_hunk = False
    
    # Basic state machine to track original line numbers
    # This is fragile but sufficient for simple patches if unidiff fails
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('@@'):
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            try:
                parts = line.split()
                # Extract -old_start,old_count
                old_part = parts[1] # e.g., "-10,5"
                if ',' in old_part:
                    start_str, count_str = old_part.split(',')
                else:
                    start_str = old_part.lstrip('-')
                    count_str = "1" # Default count 1 if not specified
                
                current_orig_line = int(start_str) - 1 # 0-indexed
                in_hunk = True
            except (ValueError, IndexError):
                in_hunk = False
        elif in_hunk and line.startswith('+'):
            # This is an added line.
            # In a unified diff, added lines don't advance the original line counter.
            # However, they are associated with the context.
            # For "ground truth lines" (the fix), we usually want the lines
            # that were changed or added. If a line is added, it's part of the fix.
            # We map it to the original line it follows, or the next original line.
            # A common convention for "lines touched" includes the context line 
            # before the addition or the added line itself (mapped to new index).
            # Here, we will mark the line number in the ORIGINAL file where this
            # insertion happens. If inserted at line N, it's often considered 
            # modifying line N (replacing it) or inserting after N.
            # Let's capture the context line number (current_orig_line + 1).
            if current_orig_line < len(original_lines):
                ground_truth_lines.add(current_orig_line + 1) # 1-based
            # If we are at the end, we might add a new line number.
            # But strictly, ground_truth_lines usually refers to existing lines
            # that were touched or the specific lines of the fix.
            # For added lines, we'll record the line index where the insertion
            # logically occurred in the original file structure.
        elif in_hunk and line.startswith('-'):
            # Deleted line: definitely part of ground truth
            ground_truth_lines.add(current_orig_line + 1)
            current_orig_line += 1
        elif in_hunk and line.startswith(' '):
            # Context line: advance original counter
            current_orig_line += 1
        
        i += 1

    return sorted(list(ground_truth_lines))


def parse_patch_unidiff(patch_text: str, original_lines: List[str]) -> List[int]:
    """
    Parse a unified diff using the unidiff library to extract ground truth lines.
    
    Returns a sorted list of 1-based line numbers from the original file
    that were modified (added, removed, or changed).
    """
    if not HAS_UNIDIFF:
        return parse_patch_basic(patch_text, original_lines)

    try:
        patch = unidiff.PatchSet(patch_text)
    except unidiff.errors.PatchParseError:
        # If the patch is malformed, return empty or fallback
        return parse_patch_basic(patch_text, original_lines)

    ground_truth_lines = set()

    for patched_file in patch:
        # We expect one file per patch usually, but iterate just in case
        for hunk in patched_file:
            # Hunk header gives us the starting line in the original file
            # hunk.source_start is 1-based
            current_orig_line = hunk.source_start - 1
            
            for line in hunk:
                if line.line_type == '-':
                    # Deleted line: it is part of the ground truth
                    ground_truth_lines.add(current_orig_line + 1)
                    current_orig_line += 1
                elif line.line_type == '+':
                    # Added line: It is part of the fix.
                    # We associate it with the line in the original file 
                    # where the insertion occurred.
                    # If we are inserting at the very end, we might not have a
                    # corresponding original line index if current_orig_line >= len.
                    # However, usually, we want to know which lines in the 
                    # original file were "touched".
                    # For the purpose of "retrieving the fix", if an agent
                    # retrieves the line *before* the insertion, that's valid.
                    # We'll add the line number corresponding to the insertion point.
                    if current_orig_line < len(original_lines):
                        ground_truth_lines.add(current_orig_line + 1)
                    else:
                        # Insertion at end of file. Mark the last line or a virtual line?
                        # We'll mark the last existing line as the context.
                        if len(original_lines) > 0:
                            ground_truth_lines.add(len(original_lines))
                    # Added lines do not advance the original line counter
                elif line.line_type == '\\':
                    # Empty line at end of file marker, ignore
                    pass
                else:
                    # Context line (' ')
                    current_orig_line += 1
    
    return sorted(list(ground_truth_lines))


def derive_ground_truth(issue_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single issue record to extract ground truth lines.
    
    Args:
        issue_record: A dictionary from the JSONL dataset containing 'patch',
                      'file', 'original_file', etc.
                      
    Returns:
        A dictionary with issue_id, file_path, ground_truth_lines, and hashes,
        or None if parsing fails.
    """
    issue_id = issue_record.get('issue_id') or issue_record.get('id')
    if not issue_id:
        return None

    # Extract relevant fields
    patch_text = issue_record.get('patch', '')
    original_content = issue_record.get('original_file', '')
    file_path = issue_record.get('file', '')
    
    if not patch_text:
        # No patch provided, cannot derive ground truth
        return None

    # Split original content into lines for context
    original_lines = original_content.splitlines() if original_content else []

    # Parse the patch
    try:
        gt_lines = parse_patch_unidiff(patch_text, original_lines)
    except Exception as e:
        # Log error but don't crash the whole pipeline
        print(f"Warning: Failed to parse patch for {issue_id}: {e}", file=sys.stderr)
        return None

    if not gt_lines:
        # Patch might be empty or only whitespace changes?
        # We still return it but with empty lines if that's the reality
        pass

    # Compute hashes for versioning
    original_hash = compute_sha256(original_content)
    patch_hash = compute_sha256(patch_text)

    return {
        "issue_id": str(issue_id),
        "file_path": file_path,
        "ground_truth_lines": gt_lines,
        "original_hash": original_hash,
        "patch_hash": patch_hash,
        "line_count": len(gt_lines)
    }


def main():
    """
    Main entry point for the ground truth derivation script.
    
    Reads from data/raw/bench.final.public.jsonl (or the path in config)
    and writes to data/curated/ground_truth.jsonl
    """
    config = get_config_summary()
    raw_data_path = Path(config['paths']['raw']) / 'bench.final.public.jsonl'
    output_path = Path(config['paths']['curated']) / 'ground_truth.jsonl'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not raw_data_path.exists():
        print(f"Error: Raw dataset not found at {raw_data_path}. "
              f"Please run `code/data/download.py` first.", file=sys.stderr)
        sys.exit(1)

    print(f"Reading dataset from {raw_data_path}...")
    
    processed_count = 0
    error_count = 0
    results = []

    with open(raw_data_path, 'r', encoding='utf-8') as f_in:
        for line_num, line in enumerate(f_in, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON at line {line_num}, skipping.", file=sys.stderr)
                error_count += 1
                continue

            result = derive_ground_truth(record)
            if result:
                results.append(result)
                processed_count += 1
            else:
                error_count += 1

    # Write results
    print(f"Writing {processed_count} ground truth records to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f_out:
        for res in results:
            f_out.write(json.dumps(res) + '\n')

    print(f"Derivation complete.")
    print(f"  Total processed: {processed_count}")
    print(f"  Failed/Skipped: {error_count}")
    print(f"  Output: {output_path}")

    # Validate output against schema if available
    try:
        schema_path = Path(config['paths']['contracts']) / 'dataset_schema.yaml'
        if schema_path.exists():
            print(f"Validating output against schema {schema_path}...")
            # The schema might be for the input dataset, but we check if a
            # specific GT schema exists or just validate structure loosely.
            # For now, we assume the validation module can handle the new file
            # if we define the schema properly in T006.
            # If a specific ground_truth schema is not defined, we skip strict
            # validation here to avoid blocking, but log success.
            print("Validation skipped (schema for ground_truth not explicitly defined in contracts yet).")
    except Exception as e:
        print(f"Warning: Validation check failed: {e}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
