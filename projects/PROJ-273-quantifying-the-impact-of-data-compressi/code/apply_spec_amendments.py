"""
apply_spec_amendments.py
------------------------

This script applies the amendments specified in the
``amendment_draft.md`` file to the project's main ``spec.md`` file.
It replaces the functional‑requirement and user‑story sections of
``spec.md`` with the exact text from the amendment draft, ensuring that
the resulting ``spec.md`` matches the draft verbatim.

The script is intended to be run as part of task **T004** in the
project pipeline:

    python code/apply_spec_amendments.py

After execution, ``spec.md`` will be overwritten with the contents of
``specs/001-compression-impact-gw-reconstruction/amendment_draft.md``.
If either file cannot be found, the script will raise an exception so
that the failure is loud and visible to the execution framework.

No command‑line arguments are required; the paths are hard‑coded relative
to the repository root to match the project layout described in the
specification.
"""

import pathlib
import sys
import hashlib

def compute_sha256(file_path: pathlib.Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def main() -> int:
    # Define the expected locations of the amendment draft and the spec file.
    repo_root = pathlib.Path(__file__).resolve().parents[1]  # project root
    amendment_path = repo_root / "specs" / "001-compression-impact-gw-reconstruction" / "amendment_draft.md"
    spec_path = repo_root / "spec.md"

    # Verify that both files exist.
    if not amendment_path.is_file():
        raise FileNotFoundError(f"Amendment draft not found at expected location: {amendment_path}")
    if not spec_path.is_file():
        raise FileNotFoundError(f"Specification file not found at expected location: {spec_path}")

    # Read the amendment draft.
    amendment_content = amendment_path.read_text(encoding="utf-8")

    # Overwrite spec.md with the amendment content.
    spec_path.write_text(amendment_content, encoding="utf-8")

    # Compute and display SHA‑256 checksums for provenance.
    amendment_checksum = compute_sha256(amendment_path)
    spec_checksum = compute_sha256(spec_path)

    print(f"Amendment draft SHA‑256: {amendment_checksum}")
    print(f"Updated spec.md SHA‑256: {spec_checksum}")

    # Successful completion.
    return 0

if __name__ == "__main__":
    sys.exit(main())
