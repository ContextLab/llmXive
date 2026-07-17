"""
Derive Ground Truth from SWE-Explore solution patches.

This module parses the solution patches (unified diff format) from the
SWE-Explore benchmark dataset to extract the specific lines of code
that constitute the 'ground truth' fix for each issue.

It produces a JSONL file where each record contains:
- issue_id
- file_path
- ground_truth_lines (list of line numbers, 1-indexed)
- original_hash (SHA256 of the file before patch)
- patch_hash (SHA256 of the patch content)
"""

import json
import hashlib
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_config_summary
from utils.hash_artifacts import compute_sha256


# --- Helper Functions ---

def compute_sha256(data: str) -> str:
    """Compute SHA256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def parse_patch_basic(patch_text: str) -> Tuple[Optional[str], List[int]]:
    """
    Parse a unified diff patch to identify the target file and modified line numbers.

    This is a robust, regex-based parser for standard unified diffs.
    It extracts:
    1. The target file path (from the `---` or `+++` header).
    2. The line numbers in the ORIGINAL file that are modified (added or changed).

    Args:
        patch_text: The raw unified diff string.

    Returns:
        Tuple of (file_path, list_of_modified_line_numbers).
        Returns (None, []) if the patch cannot be parsed.
    """
    if not patch_text or not isinstance(patch_text, str):
        return None, []

    lines = patch_text.splitlines()
    file_path = None
    modified_lines = []

    # Regex for file headers: --- a/path/to/file or +++ b/path/to/file
    # We look for the '+++ ' line to get the new file path (usually the target)
    # or the '--- ' line if '+++' is missing or standard.
    # Standard SWE-bench/SWE-Explore patches usually have:
    # --- a/...
    # +++ b/...
    
    current_hunk_start = 0
    current_hunk_len = 0
    current_file = None

    # Regex for hunk header: @@ -start,len +start,len @@
    hunk_regex = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')

    for i, line in enumerate(lines):
        # Detect file header
        if line.startswith('+++ '):
            # Extract path after +++ b/ or just +++
            path_part = line[4:].strip()
            # Remove common prefixes like 'b/' if present
            if path_part.startswith('b/'):
                path_part = path_part[2:]
            current_file = path_part
            file_path = current_file
            continue
        
        if line.startswith('--- '):
            # Fallback or source file, usually ignored for target path in diff
            continue

        # Detect hunk header
        if line.startswith('@@'):
            match = hunk_regex.match(line)
            if match:
                # original_start = int(match.group(1))
                # original_len = int(match.group(2)) if match.group(2) else 1
                # We don't strictly need these for the simple logic below,
                # but we need to track the current line number in the original file.
                pass
            continue

        # Parse hunk content
        if current_file and not line.startswith('@@') and not line.startswith('diff') and not line.startswith('index') and not line.startswith('---') and not line.startswith('+++'):
            # Determine if this line is a modification in the original file
            # Lines starting with '-' are deletions (exist in original)
            # Lines starting with '+' are additions (do not exist in original)
            # Lines starting with ' ' are context (exist in original)
            
            # We are interested in lines that are part of the *fix*.
            # In the context of "Ground Truth Lines", we usually want the lines
            # that were ADDED or CHANGED.
            # If a line is deleted, it's part of the patch, but the "fix" is often the replacement.
            # However, for coverage metrics, we often care about the lines that the agent
            # should have touched.
            
            # Let's capture lines that are ADDED (+) or CHANGED (context followed by - and +).
            # For a simple parser:
            # If line starts with '+', it's a new line.
            # If line starts with '-', it's a removed line.
            
            # We need to map these back to original line numbers.
            # This requires tracking the line counter.
            pass

    # --- Robust Line Number Calculation ---
    # We need to simulate the diff application to map '+' lines to original line numbers.
    # Actually, the requirement is "ground_truth_lines" which are the lines in the ORIGINAL file
    # that correspond to the changes.
    
    # Let's restart the parsing logic with a state machine for line numbers.
    original_line_counter = 0
    modified_line_numbers = []
    file_path = None
    
    # Reset for second pass logic
    in_hunk = False
    
    for line in lines:
        if line.startswith('+++ '):
            path_part = line[4:].strip()
            if path_part.startswith('b/'):
                path_part = path_part[2:]
            file_path = path_part
            in_hunk = False
            original_line_counter = 0 # Reset per file? Usually patches are per file.
            continue
        
        if line.startswith('--- '):
            continue

        if line.startswith('@@'):
            in_hunk = True
            match = hunk_regex.match(line)
            if match:
                original_line_counter = int(match.group(1))
            continue

        if in_hunk and file_path:
            if line.startswith('-'):
                # Deletion: This line existed in the original file.
                # It is part of the change set.
                modified_line_numbers.append(original_line_counter)
                original_line_counter += 1
            elif line.startswith('+'):
                # Addition: This line is new. It corresponds to the line *after* the last deletion/context
                # in the original file context? No, it doesn't exist in the original.
                # However, for "Ground Truth" of a fix, we often want the lines that were *changed*.
                # If we are measuring "lines retrieved", we usually mean the lines in the original file
                # that the agent identified as needing change.
                # If a line is added, it's not in the original.
                # But often, the "fix" is the replacement of a block.
                # Let's include the line number of the context line where the addition happens?
                # Or simply the line number of the *next* line in the original file?
                # Standard practice: The "ground truth lines" for an addition are often considered
                # the line number where the insertion happens (i.e., the line number of the context
                # line before it, or the line number of the next context line).
                # Let's assume we want the lines in the original file that are *affected*.
                # A deletion affects line N. An addition affects line N (the insertion point).
                # Let's track the current original line number.
                # If we see a '+', we haven't consumed an original line yet.
                # So the addition happens at the current original_line_counter (or the one after context).
                # Let's just track the lines that are DELETED or CHANGED.
                # For a pure addition, it's tricky.
                # Let's stick to: lines that are removed (---) or changed (context -> -/+).
                # If the patch is purely additions, we might need to infer.
                # But for SWE-bench, patches usually involve changes.
                # Let's include the line number of the context line immediately preceding the '+' if any.
                # Actually, the simplest robust definition for "lines to check" is the lines that are
                # DIFFERENT.
                # Let's record the original line number for deletions.
                # For additions, we can record the line number of the *next* context line or the current one.
                # Let's just record the line number of the context line before the addition if it exists.
                # If it's the very first line, maybe 1?
                # To be safe and consistent with "lines in original file", we only record lines that existed.
                # So '+' lines don't get a line number in the original file.
                # BUT, the task says "generate ground_truth_lines lists".
                # If the fix is purely adding a line, the "ground truth" is the location.
                # Let's assume the "ground truth" is the set of lines in the original file that are
                # either removed or are the context for an addition.
                # Let's just capture the `original_line_counter` for deletions.
                # For additions, we will capture the `original_line_counter` (which points to the next line).
                pass
            elif line.startswith(' '):
                # Context: Advance counter
                original_line_counter += 1
            elif line.startswith('\\'):
                # No newline at end of file marker
                continue

    # Refinement: The standard "ground truth" for SWE-bench is the set of lines in the original file
    # that are modified (deleted) or the lines immediately following a deletion where an addition occurs.
    # Let's implement a slightly more robust tracking:
    # We want the set of line numbers in the ORIGINAL file that are touched.
    # Touched = Deleted OR is the line immediately preceding an Addition (if the addition is not at the very start).
    
    # Let's re-parse with a focus on "touched original lines".
    touched_lines = set()
    current_file = None
    orig_line = 0
    in_hunk = False
    
    # We need to know the hunk start to reset orig_line?
    # Yes, @@ -start,len +start,len @@
    
    for line in lines:
        if line.startswith('+++ '):
            path_part = line[4:].strip()
            if path_part.startswith('b/'):
                path_part = path_part[2:]
            current_file = path_part
            orig_line = 0
            in_hunk = False
            continue
        
        if line.startswith('--- '):
            continue

        if line.startswith('@@'):
            in_hunk = True
            match = hunk_regex.match(line)
            if match:
                orig_line = int(match.group(1))
            continue

        if in_hunk and current_file:
            if line.startswith('-'):
                # This line is being removed. It is definitely a "ground truth line".
                touched_lines.add(orig_line)
                orig_line += 1
            elif line.startswith('+'):
                # This line is being added.
                # It is inserted *after* the current orig_line (which is the line after the last context/deletion).
                # So the "location" in the original file is effectively the line number `orig_line`
                # (if we consider 1-based indexing and insertion before the line at `orig_line`).
                # Or if we consider insertion after the previous line.
                # Let's assume the "ground truth" includes the line number where the change happens.
                # If we add a line after line 5, the "location" is 5.
                # If we add a line at the start (orig_line=1), the location is 1?
                # Let's add `orig_line` if it's valid (>=1).
                if orig_line >= 1:
                    touched_lines.add(orig_line)
                # Note: We do NOT increment orig_line for '+' lines.
            elif line.startswith(' '):
                # Context
                orig_line += 1
            elif line.startswith('\\'):
                continue

    if not current_file:
        return None, []
        
    # Sort and return
    return current_file, sorted(list(touched_lines))


def parse_patch_unidiff(patch_text: str) -> Tuple[Optional[str], List[int]]:
    """
    Parse using a more strict unidiff approach if needed.
    Currently delegates to parse_patch_basic which handles standard unidiff.
    """
    return parse_patch_basic(patch_text)


def derive_ground_truth(input_path: Path, output_path: Path) -> None:
    """
    Main function to derive ground truth from the benchmark dataset.
    
    Reads the benchmark JSONL, parses the 'solution' or 'patch' field,
    extracts the modified lines, and writes the result to a new JSONL file.
    
    Args:
        input_path: Path to the input benchmark JSONL (e.g., bench.final.public.jsonl)
        output_path: Path to write the ground truth JSONL
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input benchmark file not found: {input_path}")

    results = []
    errors = []

    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                issue_id = record.get('issue_id') or record.get('id')
                patch_content = record.get('solution') or record.get('patch')
                
                if not issue_id:
                    errors.append(f"Line {line_num}: Missing issue_id")
                    continue
                
                if not patch_content:
                    # Some records might not have a patch (e.g., unresolved)
                    # We skip them or record empty ground truth?
                    # Let's skip for now, or record with empty list.
                    # For a "hard subset" derivation, we likely only care about solved instances.
                    continue

                # Compute hashes
                patch_hash = compute_sha256(patch_content)
                
                # Parse patch
                file_path, gt_lines = parse_patch_unidiff(patch_content)
                
                if not file_path:
                    errors.append(f"Line {line_num}: Failed to parse patch for issue {issue_id}")
                    # We might still want to record the issue with empty GT?
                    # Let's skip to avoid noise, or record with empty GT.
                    # For now, record with empty GT to maintain count.
                    gt_record = {
                        "issue_id": issue_id,
                        "file_path": None,
                        "ground_truth_lines": [],
                        "patch_hash": patch_hash,
                        "original_hash": None, # We don't have original code here
                        "status": "parse_failed"
                    }
                    results.append(gt_record)
                    continue

                # Note: We don't have the original file content to compute original_hash
                # unless the dataset includes it. The SWE-bench dataset usually has
                # 'repo', 'instance_id', 'base_commit', but not the full file content in the JSONL.
                # We will leave original_hash as null or compute it if available in record.
                original_hash = record.get('base_commit') # Placeholder if file content not present
                
                gt_record = {
                    "issue_id": issue_id,
                    "file_path": file_path,
                    "ground_truth_lines": gt_lines,
                    "patch_hash": patch_hash,
                    "original_hash": original_hash,
                    "status": "ok"
                }
                results.append(gt_record)

            except json.JSONDecodeError:
                errors.append(f"Line {line_num}: Invalid JSON")
            except Exception as e:
                errors.append(f"Line {line_num}: Error processing issue {record.get('issue_id', 'unknown')}: {str(e)}")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in results:
            f.write(json.dumps(record) + '\n')

    # Log summary
    total = len(results)
    success = sum(1 for r in results if r.get('status') == 'ok')
    failed = total - success
    
    print(f"Derive GT Summary:")
    print(f"  Total records processed: {total}")
    print(f"  Successfully parsed: {success}")
    print(f"  Failed/Parsed with errors: {failed}")
    
    if errors:
        print(f"  Errors encountered: {len(errors)}")
        # Print first 5 errors
        for err in errors[:5]:
            print(f"    - {err}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more")

    if not results:
        print("WARNING: No records were written to the output file.")


def main():
    """Entry point for the derive_gt script."""
    config = get_config_summary()
    
    # Define paths based on config or defaults
    # T012 downloads to data/raw/bench.final.public.jsonl
    input_file = Path(config.get('data_raw_dir', 'data/raw')) / 'bench.final.public.jsonl'
    output_file = Path(config.get('data_curated_dir', 'data/curated')) / 'ground_truth.jsonl'
    
    print(f"Starting ground truth derivation...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    try:
        derive_ground_truth(input_file, output_file)
        print("Ground truth derivation completed successfully.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure the benchmark dataset has been downloaded (T012) before running this task.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during derivation: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()