"""
Simple runner script to verify pytest installation and directory structure.
Run with: python tests/test_runner.py
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("Verifying pytest framework and directory structure...")
    
    # Check directory structure
    root = Path(__file__).parent.parent
    required_dirs = [
        root / "tests",
        root / "tests" / "unit",
        root / "tests" / "integration"
    ]
    
    for d in required_dirs:
        if not d.exists():
            print(f"FAIL: Directory missing: {d}")
            return 1
        print(f"OK: Directory exists: {d}")

    # Check requirements
    req_file = root / "code" / "requirements.txt"
    if req_file.exists():
        content = req_file.read_text()
        if "pytest" not in content:
            print("FAIL: pytest not found in requirements.txt")
            return 1
        print("OK: pytest found in requirements.txt")
    else:
        print("FAIL: requirements.txt not found")
        return 1

    # Run a quick pytest discovery to verify setup
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("OK: Pytest collection successful")
            print(f"Found {result.stdout.count('test_')} test items")
            return 0
        else:
            print(f"FAIL: Pytest collection failed\n{result.stderr}")
            return 1
    except subprocess.TimeoutExpired:
        print("FAIL: Pytest collection timed out")
        return 1
    except Exception as e:
        print(f"FAIL: Error running pytest: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())