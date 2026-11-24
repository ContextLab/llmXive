"""
Wrapper script to run the feasibility check.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path for absolute imports
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

from code.data.feasibility import main as feasibility_main

def main():
    try:
        exit_code = feasibility_main()
        sys.exit(0)
    except Exception as e:
        print(f"Feasibility check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()