"""
Verification script for T002v: Verify Constitution Principle VI.

Inspects constitution.md to confirm Principle VI explicitly permits 
FFT-based numerical homogenization and documents the validity range 
of analytical bounds.
"""
import sys
from pathlib import Path
import re

def verify_constitution(constitution_path: Path) -> bool:
    """
    Verify that the constitution permits FFT-based homogenization.
    
    Args:
        constitution_path: Path to the constitution.md file.
        
    Returns:
        True if verification passes, False otherwise.
    """
    if not constitution_path.exists():
        print(f"ERROR: constitution.md not found at {constitution_path}")
        return False

    content = constitution_path.read_text(encoding='utf-8')
    
    # Look for Principle VI section
    principle_vi_pattern = r'Principle\s*VI.*?(?=Principle\s*VII|$)'
    principle_match = re.search(principle_vi_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if not principle_match:
        print("FAIL: Principle VI section not found in constitution.md")
        return False
        
    principle_content = principle_match.group()
    
    # Check for FFT-based homogenization permission
    has_fft = "FFT" in principle_content or "Fast Fourier Transform" in principle_content
    has_homogenization = "homogenization" in principle_content.lower() or "homogenisation" in principle_content.lower()
    
    # Check for validity range of analytical bounds
    has_bounds = "bound" in principle_content.lower() or "range" in principle_content.lower()
    has_validity = "valid" in principle_content.lower() or "limit" in principle_content.lower()
    
    success = True
    
    if not (has_fft and has_homogenization):
        print("FAIL: Principle VI does not explicitly permit FFT-based numerical homogenization")
        success = False
    else:
        print("PASS: Principle VI permits FFT-based numerical homogenization")
        
    if not (has_bounds and has_validity):
        print("FAIL: Principle VI does not document the validity range of analytical bounds")
        success = False
    else:
        print("PASS: Principle VI documents the validity range of analytical bounds")
        
    return success

def main() -> int:
    """Main entry point for the verification script."""
    # Look for constitution.md in common locations
    possible_paths = [
        Path("specs/001-predict-stiffness-cnn/constitution.md"),
        Path("constitution.md"),
        Path("docs/constitution.md"),
    ]
    
    constitution_path = None
    for p in possible_paths:
        if p.exists():
            constitution_path = p
            break
    
    if constitution_path is None:
        print("ERROR: Could not find constitution.md in any expected location")
        return 1
        
    print(f"Verifying constitution at: {constitution_path}")
    if verify_constitution(constitution_path):
        print("\nT002v VERIFICATION: PASSED")
        return 0
    else:
        print("\nT002v VERIFICATION: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())