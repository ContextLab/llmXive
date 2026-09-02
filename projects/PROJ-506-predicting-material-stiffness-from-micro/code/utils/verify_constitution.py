"""
Verification script for T002v: Verify Constitution Principle VI.
"""
import sys
import re
from pathlib import Path

def verify_constitution() -> bool:
    """
    Inspect constitution.md for Principle VI regarding FFT-based homogenization.
    """
    const_path = Path("specs/001-predict-stiffness-cnn/constitution.md")

    if not const_path.exists():
        print(f"ERROR: {const_path} does not exist.")
        return False

    content = const_path.read_text()

    # Check for Principle VI
    principle_vi_pattern = r"Principle VI.*FFT.*homogenization|FFT.*homogenization.*Principle VI"
    if not re.search(principle_vi_pattern, content, re.IGNORECASE | re.DOTALL):
        print("FAILURE: Principle VI not found or does not mention FFT-based homogenization.")
        return False

    # Check for validity range of analytical bounds
    bounds_pattern = r"Validity.*Bounds|Voigt.*Reuss.*Hill"
    if not re.search(bounds_pattern, content, re.IGNORECASE | re.DOTALL):
        print("FAILURE: Validity range of analytical bounds not documented.")
        return False

    print("SUCCESS: Constitution Principle VI is verified.")
    return True

def main():
    success = verify_constitution()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
