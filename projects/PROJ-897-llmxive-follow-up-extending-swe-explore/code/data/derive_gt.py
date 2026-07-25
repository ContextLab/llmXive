"""
T011: Ground Truth Derivation with Streaming.
Parses solution patches to generate ground_truth_lines lists.
Uses streaming to process the raw dataset in chunks.
"""
import json
import hashlib
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path

def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def parse_patch_basic(patch: str) -> List[str]:
    """
    Basic patch parser to extract added lines.
    Heuristic: Lines starting with '+' (excluding '+++') are additions.
    """
    added_lines = []
    if not patch:
        return added_lines
    
    for line in patch.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:]) # Remove the '+'
    return added_lines

def parse_patch_unidiff(patch: str) -> List[str]:
    """
    More robust unidiff parser (basic implementation).
    """
    added_lines = []
    if not patch:
        return added_lines
    
    # Simple state machine for unified diff
    # In a real scenario, use `patch` library, but for dependency minimization:
    in_hunk = False
    for line in patch.split('\n'):
        if line.startswith('@@'):
            in_hunk = True
            continue
        if in_hunk:
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])
            elif line.startswith('-') or line.startswith(' '):
                continue
            elif line.startswith('---') or line.startswith('+++'):
                continue
    return added_lines

def derive_ground_truth(item: Dict[str, Any]) -> Tuple[List[str], str]:
    """
    Derives ground truth lines from the solution patch.
    Returns (lines, patch_hash).
    """
    patch = item.get('patch', '')
    if not patch:
        # Fallback or empty
        return [], compute_sha256("")
    
    # Try unidiff first, fallback to basic
    lines = parse_patch_unidiff(patch)
    if not lines:
        lines = parse_patch_basic(patch)
    
    return lines, compute_sha256(patch)

def stream_derive_gt(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Streams the input JSONL, derives ground truth, and writes to output.
    """
    if output_path is None:
        output_path = get_path("raw", "swe_explore_with_gt.jsonl")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    count = 0
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
         
         for line in infile:
             if not line.strip():
                 continue
             try:
                 item = json.loads(line)
                 gt_lines, patch_hash = derive_ground_truth(item)
                 
                 item['ground_truth_lines'] = gt_lines
                 item['patch_hash'] = patch_hash
                 item['ground_truth_count'] = len(gt_lines)
                 
                 outfile.write(json.dumps(item) + "\n")
                 count += 1
                 
                 if count % 100 == 0:
                     print(f"Processed {count} items...")
             except json.JSONDecodeError as e:
                 print(f"Warning: Skipping invalid JSON line: {e}")
                 continue
             except Exception as e:
                 print(f"Error processing item: {e}")
                 raise
    
    print(f"Derived ground truth for {count} items. Output: {output_file}")
    return str(output_file)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Derive Ground Truth")
    parser.add_argument("--input", type=str, help="Input JSONL path")
    parser.add_argument("--output", type=str, help="Output JSONL path")
    args = parser.parse_args()
    
    input_path = args.input or get_path("raw", "swe_explore_raw.jsonl")
    output_path = args.output or get_path("raw", "swe_explore_with_gt.jsonl")
    
    try:
        stream_derive_gt(input_path, output_path)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
