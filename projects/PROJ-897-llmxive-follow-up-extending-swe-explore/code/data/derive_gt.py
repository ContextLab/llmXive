import json
import hashlib
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

from config import get_path, DATA_RAW, DATA_CURATED


def compute_sha256(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def parse_patch_basic(patch: str) -> Optional[Tuple[List[int], List[int]]]:
    """
    Parse a unified diff patch to extract added and removed line numbers.
    Returns (added_lines, removed_lines) or None if parsing fails.
    """
    if not patch or not isinstance(patch, str):
        return None

    added_lines = []
    removed_lines = []

    # Simple heuristic: look for hunk headers and +/- lines
    # This is a basic parser; a robust one would use `difflib` or `patch` library
    lines = patch.split('\n')
    current_added_start = None
    current_removed_start = None

    for line in lines:
        if line.startswith('@@'):
            # Parse hunk header: @@ -r_start,r_len +a_start,a_len @@
            # Example: @@ -100,10 +200,15 @@
            match = re.search(r'\+ (\d+)(?:,(\d+))?', line)
            if match:
                current_added_start = int(match.group(1))
            match = re.search(r'- (\d+)(?:,(\d+))?', line)
            if match:
                current_removed_start = int(match.group(1))
            continue

        if line.startswith('+') and not line.startswith('+++'):
            if current_added_start is not None:
                added_lines.append(current_added_start)
                current_added_start += 1
        elif line.startswith('-') and not line.startswith('---'):
            if current_removed_start is not None:
                removed_lines.append(current_removed_start)
                current_removed_start += 1

    if not added_lines and not removed_lines:
        return None

    return (added_lines, removed_lines)


def parse_patch_unidiff(patch: str) -> Optional[Tuple[List[int], List[int]]]:
    """
    Alternative parser using regex for more robust hunk parsing.
    Returns (added_lines, removed_lines) or None.
    """
    if not patch:
        return None

    added_lines = []
    removed_lines = []

    # Regex to find hunk headers: @@ -old_start,old_len +new_start,new_len @@
    hunk_header_pattern = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')
    added_line_pattern = re.compile(r'^\+')
    removed_line_pattern = re.compile(r'^-')

    current_added_idx = None

    for line in patch.split('\n'):
        header_match = hunk_header_pattern.match(line)
        if header_match:
            current_added_idx = int(header_match.group(1))
            continue

        if current_added_idx is not None:
            if added_line_pattern.match(line) and not line.startswith('+++'):
                added_lines.append(current_added_idx)
                current_added_idx += 1
            elif removed_line_pattern.match(line) and not line.startswith('---'):
                # Removed lines don't increment the added index
                pass
            elif not line.startswith(' ') and not line.startswith('@@'):
                # Context line or other, reset if it looks like a new hunk or end
                # For simplicity, we assume continuous hunks for this basic parser
                pass

    if not added_lines:
        return None

    return (added_lines, [])


def derive_ground_truth(issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive ground truth information from an issue record.
    Extracts relevant lines from the solution patch.
    """
    patch = issue.get('solution', '') or issue.get('patch', '')
    if not patch:
        # If no patch, we might not have ground truth
        return {
            'issue_id': issue.get('issue_id', 'unknown'),
            'ground_truth_lines': [],
            'has_ground_truth': False,
            'parse_error': 'No solution patch found'
        }

    result = parse_patch_unidiff(patch)
    if result is None:
        result = parse_patch_basic(patch)

    if result is None:
        return {
            'issue_id': issue.get('issue_id', 'unknown'),
            'ground_truth_lines': [],
            'has_ground_truth': False,
            'parse_error': 'Failed to parse patch'
        }

    added_lines, removed_lines = result

    return {
        'issue_id': issue.get('issue_id', 'unknown'),
        'ground_truth_lines': sorted(list(set(added_lines))),
        'has_ground_truth': True,
        'added_count': len(added_lines),
        'removed_count': len(removed_lines)
    }


def stream_derive_gt(
    input_path: Path,
    output_path: Path,
    batch_size: int = 1000
) -> Iterator[Dict[str, Any]]:
    """
    Stream through input JSONL, derive ground truth, and write to output.
    Yields processed records.
    """
    processed_count = 0
    buffer = []

    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue

            try:
                issue = json.loads(line)
            except json.JSONDecodeError as e:
                # Log error but continue processing
                sys.stderr.write(f"Warning: Failed to parse line {line_num}: {e}\n")
                continue

            gt_data = derive_ground_truth(issue)
            gt_data['source_line'] = line_num
            
            # Merge original issue data with derived data
            record = {**issue, **gt_data}
            
            buffer.append(record)
            processed_count += 1

            if len(buffer) >= batch_size:
                for rec in buffer:
                    outfile.write(json.dumps(rec) + '\n')
                buffer = []

        # Write remaining records
        if buffer:
            for rec in buffer:
                outfile.write(json.dumps(rec) + '\n')

        yield {
            'total_processed': processed_count,
            'output_file': str(output_path)
        }


def main():
    """Main entry point for ground truth derivation."""
    input_file = get_path(DATA_RAW, 'bench.final.public.jsonl')
    output_file = get_path(DATA_RAW, 'swe_explore_with_gt.jsonl')

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}. "
            "Run T010 (download.py) first to fetch the dataset."
        )

    print(f"Starting ground truth derivation...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")

    result = None
    for result in stream_derive_gt(input_file, output_file):
        pass

    if result:
        print(f"Completed. Processed {result['total_processed']} records.")
        print(f"Output written to: {result['output_file']}")
    else:
        print("No records were processed.")
        sys.exit(1)


if __name__ == '__main__':
    main()
