"""
Verify that the current Python environment is version 3.11.x.
This script is part of task T002 initialization.
"""
import sys

def main():
    version_info = sys.version_info
    major = version_info.major
    minor = version_info.minor

    print(f"Detected Python version: {major}.{minor}.{version_info.micro}")

    if major == 3 and minor == 11:
        print("SUCCESS: Python 3.11.x is active.")
        return 0
    else:
        print(f"ERROR: Expected Python 3.11.x, but found {major}.{minor}.x")
        print("Please activate a Python 3.11 virtual environment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())