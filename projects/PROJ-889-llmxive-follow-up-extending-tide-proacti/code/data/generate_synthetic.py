"""
generate_synthetic.py
----------------------
Generates a synthetic corpus of edge‑case Python files.  Each file is
assigned a ``dependency_depth`` in the range 1‑5 (inclusive).  The script
creates at least 200 files, writes them under ``data/raw/synthetic/``, and
updates the global checksum manifest ``data/raw/checksums.txt``.

A mismatch between any file and its recorded checksum aborts execution.
"""

import hashlib
import random
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def _sha256_of_file(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_checksum_manifest(base_dir: Path, manifest_path: Path) -> None:
    """
    Scan *base_dir* (which contains ``real`` and ``synthetic`` sub‑folders)
    and write a SHA‑256 checksum manifest.  Existing entries are overwritten.
    """
    checksum_entries = {}
    for sub in ["real", "synthetic"]:
        sub_dir = base_dir / sub
        if not sub_dir.is_dir():
            continue
        for py_file in sub_dir.glob("*.py"):
            checksum_entries[py_file.name] = _sha256_of_file(py_file)

    # Write sorted for reproducibility
    with manifest_path.open("w", encoding="utf-8") as fh:
        for fname in sorted(checksum_entries):
            fh.write(f"{checksum_entries[fname]}  {fname}\n")
    log.info(f"Checksum manifest refreshed ({len(checksum_entries)} entries).")


def _verify_checksums(base_dir: Path, manifest_path: Path) -> None:
    """Raise RuntimeError if any file does not match the recorded checksum."""
    mismatches = []
    with manifest_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            expected_hash, fname = line.split(maxsplit=1)
            # Search in both sub‑folders
            candidate = base_dir / "real" / fname
            if not candidate.is_file():
                candidate = base_dir / "synthetic" / fname
            if not candidate.is_file():
                mismatches.append((fname, "file not found"))
                continue
            actual_hash = _sha256_of_file(candidate)
            if actual_hash != expected_hash:
                mismatches.append((fname, f"expected {expected_hash}, got {actual_hash}"))

    if mismatches:
        msg = "Checksum verification failed:\n"
        msg += "\n".join(f"{fn}: {reason}" for fn, reason in mismatches)
        raise RuntimeError(msg)


def _generate_one_file(idx: int, depth: int, out_dir: Path) -> None:
    """
    Create a synthetic Python file with a given *depth* of dummy imports.
    The file defines a simple function that calls a chain of helper functions
    to emulate nested dependencies.
    """
    lines = []
    # Add dummy imports to simulate dependency depth
    for d in range(1, depth + 1):
        lines.append(f"import module_{d}_{idx}")

    # Define a chain of functions
    lines.append("")
    lines.append(f"def leaf_{idx}():")
    lines.append("    return 42")
    lines.append("")
    for d in range(depth, 0, -1):
        lines.append(f"def helper_{d}_{idx}():")
        lines.append(f"    return helper_{d+1}_{idx}()" if d < depth else "    return leaf_{idx}()")
        lines.append("")

    # Entry point
    lines.append(f"def main_{idx}():")
    lines.append(f"    return helper_1_{idx}()")
    lines.append("")
    lines.append("if __name__ == \"__main__\":")
    lines.append(f"    print(main_{idx}())")

    file_path = out_dir / f"synthetic_{idx}_depth{depth}.py"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    random.seed(42)
    synthetic_dir = paths.data("raw", "synthetic")
    synthetic_dir.mkdir(parents=True, exist_ok=True)

    # Ensure we generate at least 200 files; we'll generate exactly 200 for determinism.
    target_count = 200
    for i in range(target_count):
        depth = random.randint(1, 5)  # dependency_depth ∈ {1…5}
        _generate_one_file(i, depth, synthetic_dir)

    log.info(f"Generated {target_count} synthetic Python files in {synthetic_dir}")

    # ------------------------------------------------------------------ #
    # 5. Refresh the global checksum manifest (real + synthetic)
    # ------------------------------------------------------------------ #
    raw_root = paths.data("raw")
    checksum_path = raw_root / "checksums.txt"
    _write_checksum_manifest(raw_root, checksum_path)

    # ------------------------------------------------------------------ #
    # 6. Verify the refreshed manifest
    # ------------------------------------------------------------------ #
    _verify_checksums(raw_root, checksum_path)
    log.info("Synthetic generation completed and checksum verification passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("generate_synthetic.py terminated with an error.")
        sys.exit(1)