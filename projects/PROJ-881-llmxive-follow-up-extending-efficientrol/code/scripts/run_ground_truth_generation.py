import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run the ground truth path generation script."""
    script_path = project_root / "scripts" / "generate_ground_truth_paths.py"

    if not script_path.exists():
        print(f"ERROR: Script not found at {script_path}")
        sys.exit(1)

    print(f"Running ground truth generation script: {script_path}")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=False,
        text=True
    )

    if result.returncode != 0:
        print(f"ERROR: Ground truth generation failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    print("Ground truth generation completed successfully.")


if __name__ == "__main__":
    main()
