import json
import hashlib
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

from config import get_path, DATA_RAW, DATA_CURATED

def compute_sha256(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def parse_patch_basic(patch: str) -> List[Tuple[int, str]]:
    """
    Basic patch parser to extract added lines.
    This is a simplified version; real implementation would handle unified diffs properly.
    """
    added_lines = []
    for line in patch.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append((len(added_lines) + 1, line[1:]))
    return added_lines

def parse_patch_unidiff(patch: str) -> List[Tuple[int, str]]:
    """
    More robust unidiff parser.
    """
    added_lines = []
    current_line_num = 0
    for line in patch.split('\n'):
        if line.startswith('@@'):
            # Extract line number from @@ -x,y +a,b @@
            match = re.search(r'\+(\d+)', line)
            if match:
                current_line_num = int(match.group(1))
        elif line.startswith('+') and not line.startswith('+++'):
            added_lines.append((current_line_num, line[1:]))
            current_line_num += 1
    return added_lines

def derive_ground_truth(input_file: Path, output_file: Path) -> None:
    """
    Parses solution patches from the input JSONL and derives ground truth lines.
    Writes to output JSONL.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    with open(output_file, 'w', encoding='utf-8') as out_f:
        with open(input_file, 'r', encoding='utf-8') as in_f:
            for line in in_f:
                try:
                    record = json.loads(line)
                    # Assume 'solution' or 'patch' field exists
                    patch = record.get('solution', record.get('patch', ''))
                    
                    if patch:
                        # Try unidiff first, fallback to basic
                        try:
                            gt_lines = parse_patch_unidiff(patch)
                        except Exception:
                            gt_lines = parse_patch_basic(patch)
                        
                        record['ground_truth_lines'] = gt_lines
                        record['ground_truth_hash'] = compute_sha256(str(gt_lines))
                    else:
                        record['ground_truth_lines'] = []
                        record['ground_truth_hash'] = ""
                    
                    out_f.write(json.dumps(record) + '\n')
                    count += 1
                except json.JSONDecodeError:
                    continue
    
    print(f"Derived ground truth for {count} records.")

def stream_derive_gt(input_file: Path, output_file: Path) -> Iterator[Dict]:
    """
    Streaming version of derive_ground_truth for memory efficiency.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as in_f:
        for line in in_f:
            try:
                record = json.loads(line)
                patch = record.get('solution', record.get('patch', ''))
                if patch:
                    try:
                        gt_lines = parse_patch_unidiff(patch)
                    except Exception:
                        gt_lines = parse_patch_basic(patch)
                    record['ground_truth_lines'] = gt_lines
                yield record
            except json.JSONDecodeError:
                continue

def main():
    input_file = DATA_RAW / "bench.final.public.jsonl"
    output_file = DATA_CURATED / "ground_truth.jsonl"
    
    try:
        derive_ground_truth(input_file, output_file)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
