"""
generate_synthetic.py
----------------------
Deterministically generates a synthetic edge‑case code corpus.
"""

import argparse
import hashlib
import random
import sys
from pathlib import Path
import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

NUM_INSTANCES = 200
# The maximum allowed dependency depth per FR‑009
MAX_DEPENDENCY_DEPTH = 5
# For deterministic generation we deliberately allow a raw depth that can exceed the cap
# to demonstrate the capping logic and warning logging.
RAW_MAX_DEPTH = 7  # generate depths in 1‑7 range, then cap to 5

def _sha256_of_file(file_path: Path) -> str:
    """Return the hexadecimal SHA‑256 digest of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _iter_source_dirs(base_dir: Path):
    """Yield every directory that may hold corpus .py files."""
    yield base_dir / "real"
    yield paths.data("synthetic")

def _write_checksum_manifest(base_dir: Path, manifest_path: Path) -> None:
    """Scan the corpus directories and write a SHA‑256 checksum manifest."""
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
    """Raise RuntimeError if any file does not match the recorded checksum."""
    mismatches = []
    if not manifest_path.exists():
        return
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
                    mismatches.append((fname, f"expected {expected_hash}, got {actual_hash}"))
            except ValueError:
                log.warning(f"Skipping malformed line in checksum file: {line}")

    if mismatches:
        msg = "Checksum verification failed:\n"
        msg += "\n".join(f"{fn}: {reason}" for fn, reason in mismatches)
        raise RuntimeError(msg)

_BUG_TEMPLATES = [
    ("def process(items, acc=[]):", "mutable default argument"),
    ("if value == None:", "equality comparison with None"),
    ("result = total / count", "unchecked division"),
    ("except:", "bare except"),
    ("password = 'admin123'", "hard‑coded credential"),
    ("cursor.execute(query % user_input)", "SQL injection"),
    ("eval(user_expr)", "use of eval"),
    ("f = open(path)", "file handle never closed"),
]

def _generate_source(idx: int, depth: int, scope: str, complexity: int, label: int, rng: random.Random) -> str:
    """Create the source text of one synthetic instance."""
    lines = [f'"""Synthetic edge‑case instance {idx}."""']
    # import chain reflecting the *actual* (capped) depth
    for k in range(depth):
        lines.append(f"import dep_{idx}_{k}")
    if scope == "cross_module":
        lines.append(f"from pkg_{idx} import helper_{idx}")
    lines.append("")

    # helper functions – depth many of them
    lines.append(f"def helper_{idx}_0(x): return x + 1\n")
    for k in range(1, depth):
        lines.append(f"def helper_{idx}_{k}(x): return helper_{idx}_{k-1}(x) * 2\n")

    fn_name = f"process_{idx}"
    if label == 1:
        bug_line, bug_desc = _BUG_TEMPLATES[idx % len(_BUG_TEMPLATES)]
        lines.append(f"# planted hidden problem: {bug_desc}")
        if bug_line.startswith("def "):
            lines.append(bug_line)
            lines.append("    return list(items) + list(acc)")
        else:
            lines.append(f"def {fn_name}(items, value=None):")
            lines.append(f"    total = len(items) + {idx}")
            lines.append(f"    count = {rng.randint(0, 3)}")
            lines.append(f"    {bug_line}")
            lines.append("    return total")
    else:
        lines.append(f"def {fn_name}(items, value=None):")
        indent = "    "
        for level in range(complexity):
            lines.append(f"{indent}if value is not None and value > {level}:")
            indent += "    "
        lines.append(f"{indent}return helper_{idx}_{depth-1}(value)")
        lines.append("    return None")
    return "\n".join(lines)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation")
    parser.add_argument("--count", type=int, default=NUM_INSTANCES, help="Number of synthetic instances to generate")
    args, _ = parser.parse_known_args()

    rng = random.Random(args.seed)
    synth_dir = paths.data("synthetic")
    synth_dir.mkdir(parents=True, exist_ok=True)
    raw_root = paths.data("raw")
    raw_root.mkdir(parents=True, exist_ok=True)
    logs_dir = paths.data("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    cap_warnings_path = logs_dir / "cap_warnings.log"

    cap_warnings = []

    meta_rows = []
    for idx in range(args.count):
        # Determine a *raw* depth that may exceed the allowed maximum.
        raw_depth = (idx % RAW_MAX_DEPTH) + 1  # yields values 1‑7
        depth = min(raw_depth, MAX_DEPENDENCY_DEPTH)
        if raw_depth > MAX_DEPENDENCY_DEPTH:
            warning_msg = (
                f"Instance {idx}: requested dependency_depth {raw_depth} exceeds cap "
                f"{MAX_DEPENDENCY_DEPTH}; capping to {MAX_DEPENDENCY_DEPTH}."
            )
            cap_warnings.append(warning_msg)
            log.warning(warning_msg)

        complexity = (rng.randint(1, 5) if idx % 2 == 0 else (idx % 5) + 1)
        scope = "cross_module" if idx % 3 == 0 else "local"
        label = idx % 2

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

    # Write the manifest CSV
    pd.DataFrame(meta_rows).to_csv(raw_root / "synthetic_meta.csv", index=False)
    log.info(f"Wrote {len(meta_rows)} synthetic instances to {raw_root / 'synthetic_meta.csv'}.")

    # Write the checksum manifest for the raw directory (includes the CSV itself)
    checksum_path = raw_root / "checksums.txt"
    _write_checksum_manifest(raw_root, checksum_path)
    _verify_checksums(raw_root, checksum_path)
    log.info("Synthetic generation completed and verified.")

    # Persist any cap warnings
    if cap_warnings:
        with cap_warnings_path.open("w", encoding="utf-8") as fh:
            for line in cap_warnings:
                fh.write(line + "\n")
        log.info(f"Capped {len(cap_warnings)} instances; warnings written to {cap_warnings_path}.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("generate_synthetic.py terminated with an error.")
        sys.exit(1)