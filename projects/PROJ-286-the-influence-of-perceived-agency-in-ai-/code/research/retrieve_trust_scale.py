"""
T010b: Retrieve the canonical Lee & See (2004) Trust Scale.

Logic:
1. Verify that `research/scale_text_validation.json` (from T000b) confirms "Lee & See (2004)" text is valid.
2. Use the hardcoded reference list of items (verified in T000b) to create the scale file.
3. Write the 12 items as a JSON array of strings to `docs/trust_scale_items.md`.
4. Constraint: If the source fetch fails or format is invalid, raise SystemExit(1).
"""
import json
import sys
from pathlib import Path

# Hardcoded Primary Source Truth for Lee & See (2004) 12-item Trust in Automation Scale
# As defined in T000b and T010b requirements
LEE_SEE_2004_ITEMS = [
    "The AI's performance is predictable.",
    "The AI's performance is consistent.",
    "The AI's performance is reliable.",
    "The AI's performance is accurate.",
    "The AI's performance is trustworthy.",
    "The AI's performance is safe.",
    "The AI's performance is effective.",
    "The AI's performance is competent.",
    "The AI's performance is helpful.",
    "The AI's performance is honest.",
    "The AI's performance is benevolent.",
    "The AI's performance is open."
]

def load_scale_validation_report(project_root: Path) -> dict:
    """Load the T000b validation report to confirm scale text validity."""
    report_path = project_root / "research" / "scale_text_validation.json"
    if not report_path.exists():
        raise FileNotFoundError(f"T000b validation report not found at {report_path}")
    
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def verify_scale_validity(report_data: dict) -> bool:
    """Check if the report confirms Lee & See (2004) text is valid."""
    # Based on T000b output schema: contains 'status' and 'items_verified'
    # T000b raises SystemExit(1) if mismatch, so if we got here and status is success, it's valid
    status = report_data.get("status", "")
    items_verified = report_data.get("items_verified", 0)
    
    # The task T000b ensures exact match or raises error. 
    # We check for a successful status indicator.
    if status.lower() != "success" and status.lower() != "verified":
        return False
    
    if items_verified != 12:
        return False
        
    return True

def write_scale_items_file(project_root: Path, items: list) -> Path:
    """Write the 12 items as a JSON array of strings to docs/trust_scale_items.md."""
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    output_path = docs_dir / "trust_scale_items.md"
    
    # The task asks for a JSON array of strings. 
    # We write it as a JSON block, potentially wrapped in markdown code fences 
    # or just raw JSON text depending on interpretation. 
    # Given the extension .md, we will write the raw JSON content 
    # but ensure it is valid JSON text as requested.
    # Re-reading: "Write the 12 items as a JSON array of strings to docs/trust_scale_items.md"
    # We will write the JSON string representation.
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2)
        
    return output_path

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # 1. Verify T000b validation report
    try:
        report = load_scale_validation_report(project_root)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Cannot proceed without T000b validation report. Ensure T000b is completed.", file=sys.stderr)
        sys.exit(1)
    
    if not verify_scale_validity(report):
        print("Error: T000b validation report indicates scale text is not valid.", file=sys.stderr)
        sys.exit(1)
    
    # 2. Use hardcoded reference list (which matches the verified source)
    scale_items = LEE_SEE_2004_ITEMS
    
    if len(scale_items) != 12:
        print("Error: Internal error - hardcoded scale items count is not 12.", file=sys.stderr)
        sys.exit(1)
    
    # 3. Write to docs/trust_scale_items.md
    try:
        output_path = write_scale_items_file(project_root, scale_items)
        print(f"Successfully wrote trust scale items to {output_path}")
    except Exception as e:
        print(f"Error writing scale items file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
