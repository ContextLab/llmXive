"""Generate SHA‑256 checksums for all files under the ``data`` directory.

The script writes a Markdown table to ``docs/reproducibility/checksums.md``.
It is deliberately lightweight – it does not attempt to be incremental;
it simply recomputes the checksums each time it is run.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

# Directories
DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
DOCS_ROOT = Path(__file__).resolve().parents[2] / "docs" / "reproducibility"

OUTPUT_MD = DOCS_ROOT / "checksums.md"


def sha256_of_file(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_checksums() -> str:
    """Create a markdown table with ``relative_path`` and ``sha256`` columns."""
    lines = [
        "# Checksums for data files",
        "",
        "| Relative Path | SHA‑256 |",
        "|---------------|----------|",
    ]
    for file_path in sorted(DATA_ROOT.rglob("*")):
        if file_path.is_file():
            rel = file_path.relative_to(DATA_ROOT)
            checksum = sha256_of_file(file_path)
            lines.append(f"| {rel} | `{checksum}` |")
    return "\n".join(lines) + "\n"


def main() -> None:
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    markdown = generate_checksums()
    OUTPUT_MD.write_text(markdown, encoding="utf-8")
    print(f"Wrote checksums to {OUTPUT_MD}")


if __name__ == "__main__":
    main()
