"""
T010 Implementation: Retrieve and parse MPEA experimental uncertainty metadata.

This script extracts the target experimental uncertainty (<= 50 MPa) from the
project's specification documentation and saves it as a JSON metadata file
for downstream tasks (specifically SC-002 and T046).

Source: specs/001-predicting-the-yield-strength-of-bcc-all/spec.md
Target Output: data/processed/experimental_uncertainty_metadata.json
"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_dirs

def parse_uncertainty_from_spec(spec_path: Path) -> Dict[str, Any]:
    """
    Reads the spec.md file and extracts the experimental uncertainty target.
    
    Looks for patterns like "target: <= 50 MPa", "uncertainty <= 50 MPa",
    or "experimental uncertainty ... 50 MPa".
    """
    if not spec_path.exists():
        raise FileNotFoundError(f"Specification file not found: {spec_path}")
    
    content = spec_path.read_text(encoding="utf-8")
    
    # Pattern 1: Explicit "target: <= 50 MPa" style found in task description
    # Pattern 2: General "uncertainty ... 50 MPa"
    patterns = [
        r"target:\s*<=\s*(\d+)\s*MPa",
        r"uncertainty\s*(?:target)?\s*(?:<=)?\s*(\d+)\s*MPa",
        r"experimental\s+uncertainty.*?(\d+)\s*MPa",
    ]
    
    value = None
    source_context = ""
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            value = int(match.group(1))
            # Extract a snippet for context
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            source_context = content[start:end].replace('\n', ' ')
            break
    
    if value is None:
        # Fallback: Default to 50 MPa if the specific task description text 
        # (which is the source of truth for this project) implies it, 
        # but strictly we should fail if we can't find it to be safe.
        # However, the task description explicitly says "target: <= 50 MPa".
        # We will assume the standard scientific consensus for this specific project
        # if the regex fails on the raw file content, but log a warning.
        # For this implementation, we assume the spec contains the text.
        # If not found, we raise an error to prevent silent failure.
        raise ValueError(
            "Could not parse experimental uncertainty target from spec. "
            "Expected pattern like 'target: <= 50 MPa' not found."
        )
    
    return {
        "source_file": str(spec_path.relative_to(project_root)),
        "target_uncertainty_mpa": value,
        "constraint": f"<= {value} MPa",
        "extraction_context": source_context.strip(),
        "parsed_successfully": True
    }

def main():
    # Define paths
    spec_path = project_root / "specs" / "001-predicting-the-yield-strength-of-bcc-all" / "spec.md"
    
    # Ensure output directory exists
    ensure_dirs()
    output_path = project_root / "data" / "processed" / "experimental_uncertainty_metadata.json"
    
    print(f"Reading specification from: {spec_path}")
    
    try:
        metadata = parse_uncertainty_from_spec(spec_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("The project specification file is missing. Cannot proceed with uncertainty metadata extraction.")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}")
        print("Could not extract the uncertainty value. Please verify the spec.md content.")
        sys.exit(1)
    
    # Write metadata to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Successfully extracted uncertainty metadata.")
    print(f"Target Uncertainty: {metadata['target_uncertainty_mpa']} MPa")
    print(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()
