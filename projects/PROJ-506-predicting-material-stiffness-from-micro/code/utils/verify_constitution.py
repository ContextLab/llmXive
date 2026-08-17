import sys
from pathlib import Path
import re

def verify_constitution() -> bool:
    """
    Verify that constitution.md Principle VI has been updated to permit
    FFT-based numerical homogenization.
    
    Returns:
        bool: True if the principle is updated, False otherwise.
    """
    constitution_path = Path("constitution.md")
    
    if not constitution_path.exists():
        print(f"ERROR: constitution.md not found at {constitution_path}")
        return False
    
    content = constitution_path.read_text()
    
    # Look for Principle VI and check for FFT-based permission
    pattern = r"Principle\s+VI.*?FFT.*?numerical.*?homogenization"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        print("✓ PASS: Principle VI explicitly permits FFT-based numerical homogenization.")
        return True
    else:
        print("✗ FAIL: Principle VI does NOT explicitly permit FFT-based numerical homogenization.")
        return False

def main():
    print("Verifying constitution.md Principle VI update...")
    success = verify_constitution()
    
    if success:
        print("\n✅ Constitution amendment verified.")
        sys.exit(0)
    else:
        print("\n❌ Constitution amendment verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()