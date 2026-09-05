import sys
from pathlib import Path

def verify_constitution() -> bool:
    """
    Verify that constitution.md Principle VI explicitly states:
    "The system shall use FFT-based numerical homogenization."
    and mentions validity range of analytical bounds.
    
    Returns True if conditions are met, False otherwise.
    """
    constitution_path = Path("specs/001-predict-stiffness-cnn/constitution.md")
    
    if not constitution_path.exists():
        print(f"ERROR: {constitution_path} does not exist.")
        return False
    
    try:
        content = constitution_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Could not read {constitution_path}: {e}")
        return False
    
    # Check for FFT-based numerical homogenization
    if "FFT-based numerical homogenization" not in content:
        print("ERROR: Constitution does not contain 'FFT-based numerical homogenization'.")
        return False
    
    # Check for validity range mention
    if "validity range" not in content.lower():
        print("ERROR: Constitution does not mention 'validity range' of analytical bounds.")
        return False
    
    print("VERIFIED: Constitution Principle VI contains required text.")
    return True

def main():
    success = verify_constitution()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()