"""
T012c: Generate Non-Hard Subset.
Computes the complement of the Primary Hard Subset.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path

def filter_non_hard(input_path: str, hard_subset_path: str, output_path: str) -> str:
    """
    Filters the input dataset to keep only items NOT in the hard subset.
    """
    input_file = Path(input_path)
    hard_file = Path(hard_subset_path)
    output_file = Path(output_path)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not hard_file.exists():
        raise FileNotFoundError(f"Hard subset file not found: {hard_subset_path}")
    
    # Load hard subset IDs
    hard_ids: Set[str] = set()
    with open(hard_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                if 'instance_id' in item:
                    hard_ids.add(item['instance_id'])
    
    print(f"Loaded {len(hard_ids)} hard instance IDs.")
    
    # Filter input
    count = 0
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
         
         for line in infile:
             if not line.strip():
                 continue
             item = json.loads(line)
             if item.get('instance_id') not in hard_ids:
                 outfile.write(line)
                 count += 1
    
    print(f"Wrote {count} non-hard instances to {output_file}")
    return str(output_file)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Filter Non-Hard Instances")
    parser.add_argument("--input", type=str, help="Input JSONL path")
    parser.add_argument("--hard", type=str, help="Hard subset path")
    parser.add_argument("--output", type=str, help="Output JSONL path")
    args = parser.parse_args()
    
    input_path = args.input or get_path("raw", "swe_explore_with_gt.jsonl")
    hard_path = args.hard or get_path("curated", "hard_subset.jsonl")
    output_path = args.output or get_path("curated", "non_hard_subset.jsonl")
    
    try:
        filter_non_hard(input_path, hard_path, output_path)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
