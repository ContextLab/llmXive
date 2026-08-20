"""
Runner script for T035 Final Artifact Verification.
Executes the verification logic defined in verification.final_artifact_verification.
"""
import sys
from pathlib import Path

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from verification.final_artifact_verification import main

if __name__ == "__main__":
    sys.exit(main())
