"""
generate_synthetic.py
----------------------
Deterministically generates the synthetic edge-case code corpus.

For every instance the generator systematically varies the three intrinsic
properties studied in this project:

  * ``dependency_depth``   in {1, ..., 5}   (FR-009 cap: never exceeds 5)
  * ``semantic_scope``     local | cross_module
  * ``syntactic_complexity`` 1 (flat) .. 5 (deeply nested)

Roughly half of the instances contain a planted hidden problem (mutable
default argument, ``== None`` comparison, unchecked division, bare
except, etc.) so that ``ground_truth_label`` is balanced.

Outputs:
  * >= 200 ``.py`` files under ``data/synthetic/``
  * metadata CSV ``data/raw/synthetic_meta.csv``
  * refreshed + verified SHA-256 manifest ``data/raw/checksums.txt``

Usage:
    python -m src.data.generate_synthetic --seed 42
"""

import argparse
import hashlib
import random
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

NUM_INSTANCES = 200
MAX_DEPENDENCY_DEPTH = 5  # FR-009 cap


def _sha256_of_file(file_path: Path) -> str:
    """Return the hexadecimal SHA-256 digest of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_source_dirs(base_dir: Path):
    """Yield every directory that may hold corpus ``.py`` files."""
    yield base_dir / "real"
    yield base_dir / "synthetic"
    yield paths.data("synthetic")


def _write_checksum_manifest(base_dir: Path, manifest_path: Path) -> None:
    """
    Scan the corpus directories and write a SHA-256 checksum manifest.
    Existing entries are overwritten (the manifest is fully regenerated).
    """
    checksum_entries = {}
    for sub_dir in _iter_source_dirs(base_dir):
        if not sub_dir.is_dir():
            continue
        for py_file in sub_dir.glob("*.py"):
            checksum_entries[py_file.name] = _sha256_of_file(py_file)

    with manifest_path.open("w", encoding="utf-8") as fh:
        for fname in sorted(checksum_entries):
            fh.write(f"{checksum_entries[fname]}  {fname}\n")
    log.info(f"Checksum manifest refreshed ({len(checksum_entries)} entries).")


def _verify_checksums(base_dir: Path, manifest_path: Path) -> None:
    """Raise ``RuntimeError`` if any file does not match the recorded checksum."""
    mismatches = []
    with manifest_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                expected_hash, fname = line.split(maxsplit=1)
                candidate = None
                for sub_dir in _iter_source_dirs(base_dir):
                    maybe = sub_dir / fname
                    if maybe.is_file():
                        candidate = maybe
                        break
                if candidate is None:
                    mismatches.append((fname, "file not found"))
                    continue
                actual_hash = _sha256_of_file(candidate)
                if actual_hash != expected_hash:
                    mismatches.append(
                        (fname, f"expected {expected_hash}, got {actual_hash}")
                    )
            except ValueError:
                log.warning(f"Skipping malformed line in checksum file: {line}")

    if mismatches:
        msg = "Checksum verification failed:\n"
        msg += "\n".join(f"{fn}: {reason}" for fn, reason in mismatches)
        raise RuntimeError(msg)


# ------------------------------------------------------------------ #
# Deterministic source generation
# ------------------------------------------------------------------ #

_BUG_TEMPLATES = [
    # (bug line, short description)
    ("def process(items, acc=[]):", "mutable default argument"),
    ("if value == None:", "equality comparison with None"),
    ("result = total / count", "unchecked division (possible ZeroDivisionError)"),
    ("except:", "bare except swallows all errors"),
    ("password = 'admin123'", "hard-coded credential"),
    ("cursor.execute(query % user_input)", "string-formatted SQL (injection)"),
    ("eval(user_expr)", "use of eval on untrusted input"),
    ("f = open(path)", "file handle never closed"),
]


def _generate_source(idx: int, depth: int, scope: str, complexity: int,
                     label: int, rng: random.Random) -> str:
    """Create the source text of one synthetic instance (valid Python)."""
    lines = [f'"""Synthetic edge-case instance {idx} (generated, seed fixed)."""']

    # Dependency depth: a chain of dummy module imports.
    for k in range(depth):
        lines.append(f"import dep_{idx}_{k}")
    if scope == "cross_module":
        lines.append(f"from pkg_{idx} import helper_{idx}")
    lines.append("")

    # A helper chain whose length mirrors the dependency depth.
    lines.append(f"def helper_{idx}_0(x):")
    lines.append("    return x + 1")
    lines.append("")
    for k in range(1, depth):
        lines.append(f"def helper_{idx}_{k}(x):")
        lines.append(f"    return helper_{idx}_{k - 1}(x) * 2")
        lines.append("")

    # Main function: nesting proportional to syntactic complexity.
    fn_name = f"process_{idx}"
    if label == 1:
        bug_line, bug_desc = _BUG_TEMPLATES[idx % len(_BUG_TEMPLATES)]
        lines.append(f"# planted hidden problem: {bug_desc}")
        if bug_line.startswith("def "):
            lines.append(bug_line)
            lines.append("    value = None")
            lines.append("    if value == 0:")
            lines.append("        return []")
            lines.append("    return list(items) + list(acc)")
        else:
            lines.append(f"def {fn_name}(items, value=None):")
            lines.append(f"    total = len(items) + {idx}")
            lines.append(f"    count = {rng.randint(0, 3)}")
            lines.append(f"    {bug_line}")
            lines.append("        return None")
            lines.append("    return total")
    else:
        lines.append(f"def {fn_name}(items, value=None):")
        indent = "    "
        for level in range(complexity):
            lines.append(f"{indent}if value is not None and value > {level}:")
            indent += "    "
        lines.append(f"{indent}return helper_{idx}_{depth - 1}(value)")
        # close the nested blocks with a final fallback
        lines.append("    return None")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the synthetic edge-case corpus deterministically."
    )
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42).")
    parser.add_argument("--count", type=int, default=NUM_INSTANCES,
                        help="Number of synthetic instances to generate.")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    synth_dir = paths.data("synthetic")
    synth_dir.mkdir(parents=True, exist_ok=True)

    raw_root = paths.data("raw")
    raw_root.mkdir(parents=True, exist_ok=True)

    meta_rows = []
    for idx in range(args.count):
        depth = (idx % MAX_DEPENDENCY_DEPTH) + 1  # in {1,...,5}, FR-009 cap
        complexity = (rng.randint(1, 5) if idx % 2 == 0
                      else (idx % 5) + 1)
        scope = "cross_module" if idx % 3 == 0 else "local"
        label = idx % 2  # balanced ground-truth labels

        source = _generate_source(idx, depth, scope, complexity, label, rng)
        filename = f"synthetic_{idx}_depth{depth}.py"
        file_path = synth_dir / filename
        file_path.write_text(source, encoding="utf-8")

        meta_rows.append({
            "instance_id": idx,
            "origin": "synthetic",
            "filename": filename,
            "dependency_depth": depth,
            "semantic_scope": scope,
            "syntactic_complexity": complexity,
            "ground_truth_label": label,
            "sha256": _sha256_of_file(file_path),
        })

    import pandas as pd

    meta_path = raw_root / "synthetic_meta.csv"
    pd.DataFrame(meta_rows).to_csv(meta_path, index=False)
    log.info(
        f"Wrote {len(meta_rows)} synthetic instances to {synth_dir} and "
        f"metadata to {meta_path}"
    )

    # Sanity check: all depths within the FR-009 cap.
    bad = [r for r in meta_rows if not (1 <= r["dependency_depth"] <= 5)]
    if bad:
        raise RuntimeError(
            f"{len(bad)} synthetic instances violate the FR-009 "
            "dependency_depth cap (must be in {1..5})."
        )

    # Refresh + verify checksums (covers real and synthetic corpora).
    checksum_path = raw_root / "checksums.txt"
    _write_checksum_manifest(raw_root, checksum_path)
    _verify_checksums(raw_root, checksum_path)
    log.info("Synthetic generation completed; checksums verified.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("generate_synthetic.py terminated with an error.")
        sys.exit(1)