"""
Ground Truth Derivation Module.

This module parses solution patches from the SWE-Explore dataset to derive
the exact line numbers (ground_truth_lines) that constitute the fix.
It supports both full loading and streaming to prevent OOM errors on
constrained-memory runners, as required by Spec SC-005.
"""

import json
import hashlib
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

from config import get_path, get_config_summary
from utils.hash_artifacts import compute_sha256


def compute_sha256(text: str) -> str:
    """Compute SHA256 hash of a string."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def parse_patch_basic(patch: str) -> List[Tuple[str, int, int]]:
    """
    Parse a unified diff patch to extract changed lines.
    
    Returns a list of tuples: (file_path, start_line, end_line)
    This is a simplified parser that looks for @@ -start,count @@ headers
    and counts + lines to estimate the fixed region.
    """
    changes = []
    lines = patch.split('\n')
    current_file = None
    current_start = 0
    current_count = 0
    
    # Regex to match hunk header: @@ -old_start,old_count +new_start,new_count @@
    hunk_pattern = re.compile(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@')
    
    for line in lines:
        if line.startswith('diff --git'):
            # Extract file path from: diff --git a/path/to/file b/path/to/file
            parts = line.split(' ')
            if len(parts) >= 3:
                # Handle both a/ and b/ prefixes
                file_path = parts[2]
                if file_path.startswith('b/'):
                    current_file = file_path[2:]
                else:
                    current_file = file_path
        
        elif line.startswith('---') or line.startswith('+++'):
            # File headers, ignore or update current_file if not set
            if current_file is None and line.startswith('+++'):
                file_part = line.split(' ', 1)[1] if ' ' in line else line
                if file_part.startswith('b/'):
                    current_file = file_part[2:]
                
        elif line.startswith('@@'):
            match = hunk_pattern.match(line)
            if match:
                # We use the new start line (group 2) as the reference for added lines
                # In many cases, the fix starts here or shortly after
                current_start = int(match.group(2))
                # Estimate count based on hunk context, default to 1 if not found
                # A robust parser would count lines until next @@
                current_count = 1 
                
        elif line.startswith('+') and not line.startswith('+++'):
            # Added line - this is part of the ground truth
            # We track the range of added lines
            if current_file and current_start > 0:
                # For simplicity in this basic parser, we assume the hunk
                # covers the added lines. A more complex parser would track
                # the exact line numbers.
                # Here we record the start of the addition.
                changes.append((current_file, current_start, current_start))
                current_start += 1
                
    return changes


def parse_patch_unidiff(patch: str) -> List[Tuple[str, int, int]]:
    """
    Parse a unified diff using a more robust line-counting approach.
    
    Returns a list of tuples: (file_path, start_line, end_line)
    representing the range of lines in the patch that are additions.
    """
    changes = []
    lines = patch.split('\n')
    current_file = None
    current_new_start = 0
    added_lines = []
    
    hunk_pattern = re.compile(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@')
    
    for line in lines:
        if line.startswith('diff --git'):
            parts = line.split(' ')
            if len(parts) >= 3:
                file_path = parts[2]
                current_file = file_path[2:] if file_path.startswith('b/') else file_path
                current_new_start = 0
                added_lines = []
                
        elif line.startswith('+++'):
            # Fallback to update file name if diff header was missed
            if current_file is None:
                file_part = line.split(' ', 1)[1] if ' ' in line else line
                current_file = file_part[2:] if file_part.startswith('b/') else file_part
                
        elif line.startswith('@@'):
            match = hunk_pattern.match(line)
            if match:
                # Start of a new hunk
                # Save previous hunk if it had additions
                if added_lines and current_file:
                    start = min(added_lines)
                    end = max(added_lines)
                    changes.append((current_file, start, end))
                    
                current_new_start = int(match.group(2))
                added_lines = []
                
        elif line.startswith('+') and not line.startswith('+++'):
            # This is an added line
            if current_new_start > 0:
                added_lines.append(current_new_start)
                current_new_start += 1
                
    # Don't forget the last hunk
    if added_lines and current_file:
        start = min(added_lines)
        end = max(added_lines)
        changes.append((current_file, start, end))
        
    return changes


def derive_ground_truth(issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive ground truth lines from the solution patch of an issue.
    
    Args:
        issue: A dictionary containing issue data, including 'solution' or 'patch'.
        
    Returns:
        A dictionary with 'ground_truth_lines' (list of line numbers) and metadata.
    """
    patch = issue.get('solution', '') or issue.get('patch', '')
    issue_id = issue.get('issue_id', 'unknown')
    
    if not patch:
        return {
            'issue_id': issue_id,
            'ground_truth_lines': [],
            'files': [],
            'status': 'no_patch'
        }
        
    # Use the more robust parser
    changes = parse_patch_unidiff(patch)
    
    # Flatten to a list of line numbers (assuming single file for simplicity in this context,
    # or aggregating across files if needed. The spec implies line-level coverage,
    # so we need to know which lines in the target file are fixed.
    # For now, we return the ranges. The coverage metric will need to resolve this.
    # We assume the issue refers to a specific file in the repo context.
    
    # If the issue has a 'file_path' or similar, we filter.
    # If not, we return all changes.
    
    ground_truth_lines = []
    files = set()
    
    for file_path, start, end in changes:
        files.add(file_path)
        # Generate line numbers for the range
        # Note: In a real scenario, we might need to handle context lines.
        # Here we assume the patch lines are the ground truth.
        for i in range(start, end + 1):
            ground_truth_lines.append(i)
            
    return {
        'issue_id': issue_id,
        'ground_truth_lines': sorted(list(set(ground_truth_lines))),
        'files': list(files),
        'status': 'success',
        'patch_hash': compute_sha256(patch)
    }


def stream_derive_gt(
    input_path: Path, 
    output_path: Path, 
    chunk_size: int = 100
) -> Iterator[int]:
    """
    Stream the derivation of ground truth to avoid loading the entire dataset into memory.
    
    This function reads the input JSONL file in chunks, derives ground truth for each
    issue, and writes the results to the output JSONL file. It yields the number of
    processed issues.
    
    Args:
        input_path: Path to the input JSONL file (e.g., bench.final.public.jsonl).
        output_path: Path to the output JSONL file.
        chunk_size: Number of issues to process in a batch.
        
    Yields:
        The total count of processed issues after each chunk.
    """
    processed_count = 0
    buffer = []
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Open output file for writing
    with open(output_path, 'w', encoding='utf-8') as out_f:
        with open(input_path, 'r', encoding='utf-8') as in_f:
            for line_num, line in enumerate(in_f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    issue = json.loads(line)
                except json.JSONDecodeError:
                    # Log warning but continue
                    sys.stderr.write(f"Warning: Skipping invalid JSON at line {line_num}\n")
                    continue
                    
                gt_data = derive_ground_truth(issue)
                buffer.append(gt_data)
                processed_count += 1
                
                if len(buffer) >= chunk_size:
                    for item in buffer:
                        out_f.write(json.dumps(item) + '\n')
                    buffer = []
                    yield processed_count
                    
            # Write remaining items
            if buffer:
                for item in buffer:
                    out_f.write(json.dumps(item) + '\n')
                yield processed_count


def main():
    """Main entry point for the ground truth derivation script."""
    config = get_config_summary()
    input_path = get_path('data', 'raw', 'bench.final.public.jsonl')
    output_path = get_path('data', 'curated', 'ground_truth_derived.jsonl')
    
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file not found: {input_path}\n")
        sys.exit(1)
        
    print(f"Starting ground truth derivation from {input_path}")
    print(f"Output will be written to {output_path}")
    
    count = 0
    try:
        for count in stream_derive_gt(input_path, output_path):
            # Optional: progress logging could be added here
            pass
            
        print(f"Successfully derived ground truth for {count} issues.")
        print(f"Output written to: {output_path}")
        
    except Exception as e:
        sys.stderr.write(f"Error during derivation: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()