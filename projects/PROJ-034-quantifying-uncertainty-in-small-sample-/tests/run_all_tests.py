"""
Test runner for T038: Run pytest on all unit and integration tests.
This script executes pytest programmatically to ensure all tests pass.
"""
import sys
import subprocess

def main():
    """
    Runs pytest on all unit and integration tests.
    Returns 0 if all tests pass, 1 otherwise.
    """
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit",
        "tests/integration",
        "-v",
        "--tb=short",
        "--maxfail=5"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {result.returncode} test(s) failed.")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
