"""
Data-directory scaffolding and CHECKSUMS manifest utility (T004).

Creates data/raw/, data/processed/, data/results/ and writes a
data/CHECKSUMS manifest containing SHA-256 checksums of every real
file currently present under data/ (excluding the manifest itself).
Re-runnable: the manifest is regenerated from the files on disk, so
it always reflects the actual data contents (no fabricated entries).
"""
import hashlib
from pathlib import Path

from llmxive_toolkit import paths

DATA_SUBDIRS = ["raw", "processed", "results"]


def ensure_data_directories() -> None:
    """Create data/raw, data/processed, data/results if missing."""
    for sub in DATA_SUBDIRS:
        d = paths.data(sub)
        if not d.is_dir():
            d.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def write_checksums_manifest() -> Path:
    """Write data/CHECKSUMS listing SHA-256 of all real files under data/."""
    data_root = paths.data()
    manifest = data_root / "CHECKSUMS"
    lines = []
    for path in sorted(p for p in data_root.rglob("*") if p.is_file()):
        if path == manifest:
            continue
        rel = path.relative_to(data_root).as_posix()
        lines.append(f"{sha256_file(path)}  {rel}")
    manifest.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return manifest


def main() -> None:
    ensure_data_directories()
    manifest = write_checksums_manifest()
    n = len(manifest.read_text(encoding="utf-8").splitlines())
    print(f"data directories ensured; CHECKSUMS manifest written at {manifest} ({n} entries)")


if __name__ == "__main__":
    main()
