"""
Generate a SHA‑256 checksum for the project's ``requirements.txt`` file.
The checksum is written to ``requirements_checksum.txt`` at the project root.
This script is intended to be run after ``pip install -r requirements.txt`` as
part of the reproducibility verification step.
"""

import hashlib
from pathlib import Path


def main() -> None:
    # Resolve the project root (two levels up from this file)
    project_root = Path(__file__).resolve().parents[1]
    req_path = project_root / "requirements.txt"
    checksum_path = project_root / "requirements_checksum.txt"

    if not req_path.is_file():
        raise FileNotFoundError(f"requirements.txt not found at {req_path}")

    # Read the requirements file as bytes and compute SHA‑256
    data = req_path.read_bytes()
    sha256_hash = hashlib.sha256(data).hexdigest()

    # Write the checksum (hex string) to the output file
    checksum_path.write_text(sha256_hash + "\n")
    print(f"SHA‑256 checksum written to {checksum_path}")


if __name__ == "__main__":
    main()