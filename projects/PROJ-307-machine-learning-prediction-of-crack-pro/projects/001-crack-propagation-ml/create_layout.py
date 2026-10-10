"""Create the required top‑level directory layout for the feature.

This script is idempotent: running it multiple times will not raise errors.
It creates the following sub‑folders inside the feature directory:

    code/
    data/
    tests/
    specs/
    contracts/

Execution produces a short confirmation message.
"""
import sys
from pathlib import Path

def main() -> None:
    # The script resides in the feature root directory:
    # projects/001-crack-propagation-ml/
    feature_root = Path(__file__).parent.resolve()

    subdirs = ["code", "data", "tests", "specs", "contracts"]
    for sub in subdirs:
        dir_path = feature_root / sub
        dir_path.mkdir(parents=True, exist_ok=True)

    print(f"Created directory layout under: {feature_root}", file=sys.stdout)

if __name__ == "__main__":
    main()