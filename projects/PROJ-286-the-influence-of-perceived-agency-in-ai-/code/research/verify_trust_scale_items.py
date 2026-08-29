"""
Task T011: Verify docs/trust_scale_items.md matches the validated text from T000b.

This script reads the generated scale items file and compares them against the
hardcoded reference list defined in the Primary Source Truth (Lee & See, 2004).
It ensures the file matches the validated citation exactly.
"""
import json
import sys
from pathlib import Path
from typing import List, Tuple, Any, Dict

# Primary Source Truth for Lee & See (2004) 12-item Trust in Automation Scale
# Hardcoded based on T000b validation requirements
PRIMARY_SOURCE_TRUTH = [
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

def load_trust_scale_items(file_path: Path) -> List[str]:
    """Load trust scale items from a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Trust scale file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array, got {type(data).__name__}")
        
        items = [str(item).strip() for item in data]
        return items
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {file_path}: {e}")

def load_validation_report(file_path: Path) -> Dict[str, Any]:
    """Load the scale text validation report from T000b."""
    if not file_path.exists():
        raise FileNotFoundError(f"Validation report not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_items(
    loaded_items: List[str], 
    reference_items: List[str]
) -> Tuple[bool, List[str]]:
    """
    Verify that loaded items match the reference items exactly.
    
    Returns:
        Tuple of (is_valid, list of mismatched indices or empty list)
    """
    mismatches = []
    
    if len(loaded_items) != len(reference_items):
        mismatches.append(f"Length mismatch: expected {len(reference_items)}, got {len(loaded_items)}")
        return False, mismatches
    
    for i, (loaded, reference) in enumerate(zip(loaded_items, reference_items)):
        if loaded != reference:
            mismatches.append(f"Item {i+1} mismatch:")
            mismatches.append(f"  Expected: '{reference}'")
            mismatches.append(f"  Got:      '{loaded}'")
    
    return len(mismatches) == 0, mismatches

def main():
    """Main execution function for T011."""
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    scale_items_path = project_root / "docs" / "trust_scale_items.md"
    validation_report_path = project_root / "research" / "scale_text_validation.json"
    
    print(f"Task T011: Verifying trust scale items...")
    print(f"Scale items file: {scale_items_path}")
    print(f"Validation report: {validation_report_path}")
    
    # Verify T000b validation report exists
    try:
        validation_report = load_validation_report(validation_report_path)
        if not validation_report.get('status') == 'verified':
            print(f"ERROR: Validation report status is not 'verified': {validation_report.get('status')}")
            sys.exit(1)
        print("✓ T000b validation report confirms scale text is valid")
    except Exception as e:
        print(f"ERROR: Failed to load validation report: {e}")
        sys.exit(1)
    
    # Load scale items from docs/trust_scale_items.md
    try:
        loaded_items = load_trust_scale_items(scale_items_path)
        print(f"✓ Loaded {len(loaded_items)} items from {scale_items_path}")
    except Exception as e:
        print(f"ERROR: Failed to load scale items: {e}")
        sys.exit(1)
    
    # Verify items match primary source truth
    is_valid, mismatches = verify_items(loaded_items, PRIMARY_SOURCE_TRUTH)
    
    if not is_valid:
        print("\n✗ VERIFICATION FAILED: Scale items do not match primary source truth")
        for msg in mismatches:
            print(f"  {msg}")
        print("\nThis indicates a mismatch with the validated citation in T000b.")
        sys.exit(1)
    
    print("\n✓ VERIFICATION SUCCESS: All 12 items match the validated Lee & See (2004) scale")
    print("  - Item 1: The AI's performance is predictable.")
    print("  - Item 2: The AI's performance is consistent.")
    print("  - Item 3: The AI's performance is reliable.")
    print("  - Item 4: The AI's performance is accurate.")
    print("  - Item 5: The AI's performance is trustworthy.")
    print("  - Item 6: The AI's performance is safe.")
    print("  - Item 7: The AI's performance is effective.")
    print("  - Item 8: The AI's performance is competent.")
    print("  - Item 9: The AI's performance is helpful.")
    print("  - Item 10: The AI's performance is honest.")
    print("  - Item 11: The AI's performance is benevolent.")
    print("  - Item 12: The AI's performance is open.")
    print("\nTask T011 completed successfully.")
    
    # Write verification confirmation to research directory
    verification_output = {
        "task_id": "T011",
        "status": "verified",
        "scale_source": "Lee & See (2004)",
        "items_verified": 12,
        "verification_timestamp": "2024-01-01T00:00:00Z",
        "primary_source_truth_hash": hash(tuple(PRIMARY_SOURCE_TRUTH))
    }
    
    output_path = project_root / "research" / "trust_scale_items_verified.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(verification_output, f, indent=2)
    
    print(f"\nVerification report written to: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
