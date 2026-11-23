import sys
import re
from pathlib import Path

REQUIRED_SC_009_TEXT = (
    "The report must explicitly state: 'Note: This study uses proxy metrics for cognitive load. "
    "Self-report measures (e.g., NASA-TLX) were not available.' "
)

def verify_spec_content(spec_path: str) -> bool:
    """
    Verify that spec.md contains the required SC-009 text.
    
    Args:
        spec_path: Path to the spec.md file.
        
    Returns:
        True if the required text is found, False otherwise.
    """
    path = Path(spec_path)
    if not path.exists():
        print(f"ERROR: Spec file not found at {spec_path}")
        return False

    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Could not read spec file: {e}")
        return False

    # Normalize whitespace for comparison (handle potential line breaks in the file)
    normalized_content = re.sub(r'\s+', ' ', content).strip()
    normalized_required = REQUIRED_SC_009_TEXT.strip()

    if normalized_required in normalized_content:
        print("SUCCESS: SC-009 requirement found in spec.md.")
        return True
    else:
        print("FAILURE: SC-009 requirement NOT found in spec.md.")
        print(f"Expected to find: {normalized_required}")
        return False

def main():
    """Main entry point for spec verification."""
    # Default path relative to project root
    spec_file = Path("specs/001-evaluating-the-impact-of-llm-based-code-completion/spec.md")
    
    # Allow override via command line
    if len(sys.argv) > 1:
        spec_file = Path(sys.argv[1])

    if not verify_spec_content(str(spec_file)):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
