"""
Script to execute T030: Linearity Check.
This script ensures dependencies are met and runs the linearity check.
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    # Ensure dependencies exist
    pairs_path = project_root / "data" / "processed" / "pairs.yaml"
    index_path = project_root / "data" / "processed" / "skill_index.npz"

    if not pairs_path.exists():
        print("Error: pairs.yaml not found. Please run T022c first.")
        sys.exit(1)

    if not index_path.exists():
        print("Warning: skill_index.npz not found. Generating dummy index for testing.")
        # Run the dummy generator
        from scripts.generate_dummy_index import main as gen_main
        gen_main()

    # Run T030
    from src.validation.linearity_check import main as linearity_main
    sys.exit(linearity_main())

if __name__ == "__main__":
    main()