"""T001b: Record SHA-256 checksums for every NIfTI file in data/raw.

Scans ``data/raw`` for ``*.nii.gz`` / ``*.nii`` files, computes each
file's SHA-256 using the loader's streaming ``compute_sha256``, writes
``data/raw/checksums.json``, and then re-verifies every recorded
checksum against a fresh recomputation (fails loudly on mismatch).
"""
import json
import sys
from pathlib import Path

from llmxive_toolkit import paths

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_loader import compute_sha256, verify_nifti_integrity

NIFTI_SUFFIXES = (".nii", ".nii.gz")


def find_nifti_files(raw_dir: Path):
    """Return all NIfTI files under raw_dir, sorted for determinism."""
    files = [p for p in sorted(raw_dir.rglob("*"))
             if p.is_file() and p.name.endswith(NIFTI_SUFFIXES)]
    return files


def record_checksums(raw_dir: Path, output_path: Path) -> dict:
    files = find_nifti_files(raw_dir)
    if not files:
        raise SystemExit(
            "ERROR: no NIfTI files found under data/raw; "
            "run `python code/data_loader.py --output data/raw` first."
        )
    entries = {}
    for path in files:
        verify_nifti_integrity(path)  # size > 0 and opens with nibabel
        rel = path.relative_to(raw_dir.parent)
        entries[str(rel)] = compute_sha256(path)
        print(f"checksummed {rel}")
    doc = {"algorithm": "sha256", "files": entries}
    output_path.write_text(json.dumps(doc, indent=2) + "\n")
    return doc


def verify_checksums(raw_dir: Path, output_path: Path) -> int:
    doc = json.loads(output_path.read_text())
    assert doc.get("algorithm") == "sha256"
    checked = 0
    for rel, recorded in doc["files"].items():
        path = raw_dir.parent / rel
        if not path.exists():
            raise SystemExit(f"ERROR: checksummed file missing: {rel}")
        actual = compute_sha256(path)
        if actual != recorded:
            raise SystemExit(
                f"ERROR: checksum mismatch for {rel}: "
                f"recorded {recorded}, recomputed {actual}"
            )
        checked += 1
    return checked


def main() -> int:
    raw_dir = paths.data("raw")
    output_path = raw_dir / "checksums.json"
    doc = record_checksums(raw_dir, output_path)
    n = verify_checksums(raw_dir, output_path)
    print(f"Wrote {output_path} with {len(doc['files'])} sha256 entries; "
          f"verified {n}/{n} checksums match recomputation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())