"""
Derive ground truth from SWE-bench solution patches.
Uses streaming to process large datasets without OOM.
"""
import json
import hashlib
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, DATA_RAW, DATA_CURATED

def compute_sha256(text: str) -> str:
    """Compute SHA256 hash of a string."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def parse_patch_basic(patch: str) -> List[str]:
    """
    Basic parser to extract changed lines from a patch.
    Returns a list of added lines (starting with '+').
    """
    if not patch or not isinstance(patch, str):
        return []
    
    lines = []
    for line in patch.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            stripped = line[1:]
            if stripped and not stripped.startswith(' '):
                lines.append(stripped)
    return lines

def parse_patch_unidiff(patch: str) -> List[str]:
    """
    More robust unidiff parser to extract added lines.
    Handles standard diff format.
    """
    if not patch or not isinstance(patch, str):
        return []
    
    lines = []
    in_hunk = False
    
    for line in patch.split('\n'):
        if line.startswith('@@'):
            in_hunk = True
            continue
        if line.startswith('diff --git') or line.startswith('index '):
            in_hunk = False
            continue
        if in_hunk and line.startswith('+') and not line.startswith('+++'):
            content = line[1:]
            # Skip whitespace-only additions
            if content.strip():
                lines.append(content)
    
    return lines

def derive_ground_truth(record: Dict[str, Any]) -> Tuple[List[str], str]:
    """
    Extract ground truth lines from a single record.
    
    Args:
        record: A single dataset record containing 'patch' or 'solution'.
                
    Returns:
        Tuple of (ground_truth_lines, patch_hash)
    """
    patch = record.get('patch') or record.get('solution') or record.get('model_patch')
    
    if not patch:
        return [], compute_sha256("")
    
    patch_hash = compute_sha256(patch)
    
    # Try unidiff first, fall back to basic
    lines = parse_patch_unidiff(patch)
    if not lines:
        lines = parse_patch_basic(patch)
    
    return lines, patch_hash

def stream_derive_gt(input_file: Path, output_file: Optional[Path] = None) -> Path:
    """
    Stream through input file, derive ground truth, and write to output.
    
    Args:
        input_file: Path to input JSONL file.
        output_file: Path to output JSONL file. Defaults to data/curated/swe_explore_with_gt.jsonl.
        
    Returns:
        Path to output file.
    """
    if output_file is None:
        output_file = DATA_CURATED / "swe_explore_with_gt.jsonl"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
         
         for line in infile:
             line = line.strip()
             if not line:
                 continue
             
             try:
                 record = json.loads(line)
                 gt_lines, patch_hash = derive_ground_truth(record)
                 
                 # Add ground truth to record
                 record['ground_truth_lines'] = gt_lines
                 record['patch_hash'] = patch_hash
                 record['gt_line_count'] = len(gt_lines)
                 
                 outfile.write(json.dumps(record, ensure_ascii=False) + '\n')
                 count += 1
                 
                 if count % 1000 == 0:
                     print(f"  Processed {count} records...")
             except json.JSONDecodeError as e:
                 print(f"Warning: Skipping invalid JSON line: {e}")
                 continue
             except Exception as e:
                 print(f"Warning: Error processing record: {e}")
                 continue
    
    print(f"Derived ground truth for {count} records.")
    print(f"Output saved to: {output_file}")
    return output_file

def main():
    """Entry point for the derive GT script."""
    print("Starting ground truth derivation...")
    
    input_file = DATA_RAW / "swe_explore_raw.jsonl"
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        print("Please run download.py first.")
        sys.exit(1)
    
    try:
        output_path = stream_derive_gt(input_file)
        print(f"Ground truth derivation complete.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
