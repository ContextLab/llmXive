"""
Verification script for T004v: Verify Spec Resolution.

Checks that the spec.md file contains:
1. '128x128 pixels' (resolution requirement from FR-001)
2. 'US-1' (reference to User Story 1)

This script implements the verification logic described in tasks.md for T004v.
"""
import sys
from pathlib import Path

def verify_spec_resolution(spec_path: Path) -> bool:
    """
    Verify that the spec file contains required resolution and US-1 reference.
    
    Args:
        spec_path: Path to the spec.md file
        
    Returns:
        True if both requirements are met, False otherwise
        
    Raises:
        FileNotFoundError: If the spec file does not exist
    """
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
    
    content = spec_path.read_text()
    
    # Check for resolution requirement (FR-001)
    has_resolution = '128x128 pixels' in content
    
    # Check for US-1 reference
    has_us1 = 'US-1' in content
    
    if not has_resolution:
        print("ERROR: FR-001 resolution requirement ('128x128 pixels') not found in spec")
        return False
        
    if not has_us1:
        print("ERROR: User Story 1 reference ('US-1') not found in spec")
        return False
        
    print("SUCCESS: Spec verification passed")
    print(f"  - Found resolution requirement: '128x128 pixels'")
    print(f"  - Found User Story reference: 'US-1'")
    return True

def main():
    """Main entry point for verification."""
    # Determine project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    spec_path = project_root / "specs" / "001-predict-stiffness-cnn" / "spec.md"
    
    try:
        success = verify_spec_resolution(spec_path)
        sys.exit(0 if success else 1)
    except FileNotFoundError as e:
        print(f"VERIFICATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"VERIFICATION ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()