"""
verify_clips.py

Computes SHA‑256 checksums for each clip file in a given directory and records
the dataset source information (URL and version ID) in ``research.md``.
The script is idempotent – running it again will update the checksum manifest
and ensure the metadata block is present in ``research.md``.
"""

import argparse
import json
from pathlib import Path
from typing import Dict

from src.lib.utils import compute_file_checksum

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _collect_checksums(clips_dir: Path) -> Dict[str, str]:
    """
    Walk ``clips_dir`` (non‑recursively) and compute SHA‑256 checksums for each
    file. Returns a mapping of relative file names to their checksum strings.
    """
    checksums: Dict[str, str] = {}
    for item in clips_dir.iterdir():
        if item.is_file():
            rel_name = item.name
            checksums[rel_name] = compute_file_checksum(item)
    return checksums


def _write_checksum_manifest(checksums: Dict[str, str], out_path: Path) -> None:
    """
    Write the checksum dictionary to ``out_path`` as pretty‑printed JSON.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)


def _ensure_dataset_metadata(
    research_md: Path, dataset_url: str, version_id: str
) -> None:
    """
    Append (or update) a simple metadata block to ``research_md`` containing
    the dataset URL and version ID. If the block already exists, it will be
    replaced with the new values.
    """
    header = "## Dataset Information"
    url_line = f"- dataset_url: {dataset_url}"
    version_line = f"- version_id: {version_id}"
    block = "\n".join([header, url_line, version_line])

    if not research_md.exists():
        research_md.parent.mkdir(parents=True, exist_ok=True)
        research_md.write_text(block + "\n", encoding="utf-8")
        return

    content = research_md.read_text(encoding="utf-8")
    if header in content:
        # Replace existing block
        parts = content.split(header, maxsplit=1)
        before = parts[0].rstrip()
        after = parts[1]
        # Remove any following lines that start with '- '
        after_lines = after.splitlines()
        # Keep lines after the two metadata lines (or until a non‑metadata line)
        keep_from = 0
        for i, line in enumerate(after_lines):
            if not line.startswith("- "):
                keep_from = i
                break
        new_content = (
            f"{before}\n{block}\n" + "\n".join(after_lines[keep_from:]).lstrip()
        )
        research_md.write_text(new_content, encoding="utf-8")
    else:
        # Simply append the block
        with research_md.open("a", encoding="utf-8") as f:
            f.write("\n" + block + "\n")


# ---------------------------------------------------------------------------
# Core verification function
# ---------------------------------------------------------------------------

def verify_clips(
    clips_dir: Path,
    checksum_output: Path,
    research_md: Path,
    dataset_url: str,
    version_id: str,
) -> None:
    """
    Compute checksums for all clips in ``clips_dir`` and write the manifest to
    ``checksum_output``. Record ``dataset_url`` and ``version_id`` in the
    ``research_md`` file.
    """
    if not clips_dir.is_dir():
        raise FileNotFoundError(f"Clips directory not found: {clips_dir}")

    # 1. Compute checksums
    checksums = _collect_checksums(clips_dir)

    # 2. Persist manifest
    _write_checksum_manifest(checksums, checksum_output)

    # 3. Record dataset metadata
    _ensure_dataset_metadata(research_md, dataset_url, version_id)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify clip files by computing SHA‑256 checksums and "
        "recording dataset provenance."
    )
    parser.add_argument(
        "--clips-dir",
        type=Path,
        default=Path("data/stimuli/clips"),
        help="Directory containing the downloaded clip files.",
    )
    parser.add_argument(
        "--checksum-output",
        type=Path,
        default=Path("data/processed/clips_checksums.json"),
        help="Path to write the JSON checksum manifest.",
    )
    parser.add_argument(
        "--research-md",
        type=Path,
        default=Path("research.md"),
        help="Path to the project research markdown file.",
    )
    parser.add_argument(
        "--dataset-url",
        type=str,
        required=True,
        help="URL of the source dataset (e.g., HuggingFace hub URL).",
    )
    parser.add_argument(
        "--version-id",
        type=str,
        required=True,
        help="Version identifier of the dataset (e.g., commit hash).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    verify_clips(
        clips_dir=args.clips_dir,
        checksum_output=args.checksum_output,
        research_md=args.research_md,
        dataset_url=args.dataset_url,
        version_id=args.version_id,
    )


if __name__ == "__main__":
    main()
