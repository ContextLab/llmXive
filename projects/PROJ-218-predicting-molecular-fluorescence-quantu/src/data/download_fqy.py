"""Download the experimental FQY JSON file, verify its checksum, and pin seeds."""
import argparse
import sys
from pathlib import Path

# Shared utilities for downloading and seed handling
from code.data.download_raw import (
    download_file,
    read_checksums,
    load_and_set_seeds,
)

def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download the FQY JSON dataset and verify its SHA‑256 checksum."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Direct URL (or DOI) to the FQY JSON file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path where the downloaded JSON will be saved.",
    )
    args = parser.parse_args(argv)

    # 1️⃣ Pin reproducibility seeds before any other operation
    load_and_set_seeds()

    # 2️⃣ Ensure output directory exists
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 3️⃣ Download the file while computing its SHA‑256 hash
    try:
        computed_checksum = download_file(args.url, out_path)
    except Exception as exc:
        sys.exit(f"Failed to download FQY file: {exc}")

    # 4️⃣ Verify checksum against the recorded value
    expected = read_checksums()
    filename = out_path.name
    expected_checksum = expected.get(filename)

    if expected_checksum is None:
        sys.exit(
            f"Checksum for '{filename}' not found in 'data/raw/checksums.txt'."
        )
    if computed_checksum != expected_checksum:
        sys.exit(
            f"Checksum mismatch for '{filename}'. Expected {expected_checksum}, got {computed_checksum}."
        )

    # Successful completion
    return 0

if __name__ == "__main__":
    sys.exit(main())