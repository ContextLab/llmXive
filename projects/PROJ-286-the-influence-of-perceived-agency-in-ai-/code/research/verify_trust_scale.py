"""
Verify the trust scale items in docs/trust_scale_items.md against the validated citation.
This script ensures the items match the source instrument before the experiment runs.

Dependencies:
- docs/trust_scale_items.md (JSON array of 12 items)
- research/validation_report.json (output of T000)

Output:
- research/trust_scale_verification_report.md
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Any, Dict

# Expected items based on Lee & See (2004) as defined in T007e
# These must match the items in docs/trust_scale_items.md exactly
EXPECTED_ITEMS: List[str] = [
    "I trust this system",
    "I feel confident in this system",
    "I believe this system is reliable",
    "I feel this system is competent",
    "I feel this system is predictable",
    "I feel this system is safe",
    "I feel this system is honest",
    "I feel this system is benevolent",
    "I feel this system is capable",
    "I feel this system is useful",
    "I feel this system is accurate",
    "I feel this system is effective"
]

def load_trust_scale_items(file_path: Path) -> List[str]:
    """Load and parse the JSON array from the markdown file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Trust scale file not found: {file_path}")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Extract JSON block from markdown
    json_start = content.find('```json')
    if json_start == -1:
        # Try without 'json' tag
        json_start = content.find('```')
    
    if json_start == -1:
        raise ValueError(f"Could not find JSON block start in {file_path}")
    
    # Find the end of the JSON block
    json_end = content.find('```', json_start + 3)
    if json_end == -1:
        raise ValueError(f"Could not find JSON block end in {file_path}")
    
    json_str = content[json_start + 3:json_end].strip()
    
    # If we had '```json', skip that extra word
    if content[json_start:json_start+7] == '```json':
        json_str = content[json_start + 7:json_end].strip()
    
    try:
        items = json.loads(json_str)
        if not isinstance(items, list):
            raise ValueError("Trust scale items must be a JSON array")
        return items
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in trust scale file: {e}")

def load_validation_report(file_path: Path) -> Dict[str, Any]:
    """Load the citation validation report."""
    if not file_path.exists():
        raise FileNotFoundError(f"Validation report not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, list):
        return {"citations": data}
    elif isinstance(data, dict):
        return data
    else:
        raise ValueError(f"Unexpected validation report format: {type(data)}")

def verify_items(items: List[str], validation_report: Dict[str, Any]) -> Tuple[bool, str, List[Tuple[int, str, str]]]:
    """
    Verify that the loaded items match the expected items.
    Returns (is_verified: bool, message: str, mismatches: List[Tuple[index, expected, actual]])
    """
    mismatches: List[Tuple[int, str, str]] = []
    
    if len(items) != len(EXPECTED_ITEMS):
        return False, f"Item count mismatch: expected {len(EXPECTED_ITEMS)}, got {len(items)}", mismatches
    
    for i, (expected, actual) in enumerate(zip(EXPECTED_ITEMS, items)):
        if expected != actual:
            mismatches.append((i + 1, expected, actual))
    
    if mismatches:
        msg_parts = []
        for idx, exp, act in mismatches:
            msg_parts.append(f"Item {idx}: expected '{exp}', got '{act}'")
        return False, "; ".join(msg_parts), mismatches
    
    # Check that the citation in the validation report is valid
    # The report should be a list of citation objects with 'status' key
    citations = validation_report.get("citations", validation_report)
    if isinstance(citations, list):
        valid_citations = [c for c in citations if c.get('status') == 'valid']
        if not valid_citations:
            return False, "No valid citations found in validation report", mismatches
    else:
        # If it's a dict, check if it has a valid status
        if validation_report.get('status') != 'valid':
            return False, "Validation report does not indicate valid citation", mismatches
    
    return True, "All items verified successfully", mismatches

def main():
    parser = argparse.ArgumentParser(
        description='Verify trust scale items against validated citation'
    )
    parser.add_argument(
        '--items-file', 
        type=Path, 
        default=Path('docs/trust_scale_items.md'),
        help='Path to trust scale items file'
    )
    parser.add_argument(
        '--validation-report', 
        type=Path, 
        default=Path('research/validation_report.json'),
        help='Path to citation validation report'
    )
    parser.add_argument(
        '--output', 
        type=Path, 
        default=Path('research/trust_scale_verification_report.md'),
        help='Path to output verification report'
    )
    args = parser.parse_args()

    try:
        # Load items and validation report
        items = load_trust_scale_items(args.items_file)
        validation_report = load_validation_report(args.validation_report)
        
        # Verify items
        is_verified, message, mismatches = verify_items(items, validation_report)
        
        # Write verification report
        output_dir = args.output.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write("# Trust Scale Verification Report\n\n")
            f.write(f"**Status**: {'VERIFIED' if is_verified else 'FAILED'}\n\n")
            f.write(f"**Message**: {message}\n\n")
            f.write(f"**Items Count**: {len(items)}\n\n")
            
            # Count valid citations
            citations = validation_report.get("citations", validation_report)
            if isinstance(citations, list):
                valid_count = len([c for c in citations if c.get('status') == 'valid'])
            else:
                valid_count = 1 if validation_report.get('status') == 'valid' else 0
            f.write(f"**Valid Citations**: {valid_count}\n\n")
            
            if not is_verified:
                f.write("### Failed Items\n")
                for idx, exp, act in mismatches:
                    f.write(f"- Item {idx}: Expected '{exp}', got '{act}'\n")
                f.write("\n**Action Required**: Fix the trust scale items in `docs/trust_scale_items.md` to match the expected items from Lee & See (2004).\n")
            
            f.write("\n---\n")
            f.write("### Expected Items (Lee & See, 2004)\n")
            for i, item in enumerate(EXPECTED_ITEMS, 1):
                f.write(f"{i}. {item}\n")
        
        # Exit with error code if verification failed
        if not is_verified:
            print(f"VERIFICATION FAILED: {message}")
            sys.exit(1)
        
        print(f"VERIFICATION PASSED: {message}")
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"VERIFICATION ERROR: {str(e)}")
        # Write error report
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write("# Trust Scale Verification Report\n\n")
            f.write(f"**Status**: FAILED\n\n")
            f.write(f"**Error**: {str(e)}\n\n")
        sys.exit(1)
    except Exception as e:
        print(f"VERIFICATION ERROR: {str(e)}")
        # Write error report
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write("# Trust Scale Verification Report\n\n")
            f.write(f"**Status**: FAILED\n\n")
            f.write(f"**Error**: {str(e)}\n\n")
        sys.exit(1)

if __name__ == '__main__':
    main()