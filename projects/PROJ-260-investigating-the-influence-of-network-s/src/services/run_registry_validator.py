import sys
from pathlib import Path

# Ensure the project root is on the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.services.registry_validator import main as validator_main

if __name__ == "__main__":
    exit_code = validator_main()
    sys.exit(exit_code)