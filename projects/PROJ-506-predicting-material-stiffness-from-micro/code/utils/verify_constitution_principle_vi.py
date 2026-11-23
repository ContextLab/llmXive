"""
Verification script for Constitution Principle VI.
Checks that the constitution permits FFT-based numerical homogenization.
"""
import sys
from pathlib import Path

def verify_constitution_principle_vi():
    """
    Verify that Constitution Principle VI exists and permits FFT or numerical methods.
    
    Returns:
        bool: True if verification passes, False otherwise.
        
    Raises:
        AssertionError: If the principle is missing or does not permit the required method.
    """
    # Path to the constitution file relative to project root
    constitution_path = Path("projects/PROJ-506-predicting-material-stiffness-from-micro/docs/constitution.md")
    
    if not constitution_path.exists():
        raise FileNotFoundError(f"Constitution file not found at {constitution_path}")
    
    with open(constitution_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for keywords indicating permission for FFT-based numerical homogenization
    has_fft = 'FFT' in content
    has_numerical = 'numerical' in content.lower()
    
    if not (has_fft or has_numerical):
        raise AssertionError(
            "Principle VI missing permission for FFT-based numerical homogenization. "
            "The constitution must contain 'FFT' or 'numerical' to permit this method."
        )
    
    print("✓ Constitution Principle VI verified: FFT or numerical methods are permitted.")
    return True

def main():
    """Entry point for the verification script."""
    try:
        verify_constitution_principle_vi()
        sys.exit(0)
    except (FileNotFoundError, AssertionError) as e:
        print(f"✗ Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
