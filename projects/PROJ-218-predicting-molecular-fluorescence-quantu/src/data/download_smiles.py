"""Download the SMILES parquet file, verify its checksum, and ensure seeds are pinned."""
import argparse
import sys
from pathlib import Path

# Import the shared utilities for downloading and seed handling
from code.data.download_raw import (
    download_file,
    read_checksums,
    load_and_set_seeds,
)

def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download the SMILES dataset and verify its SHA‑256 checksum."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Direct URL to the SMILES parquet file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path where the downloaded file will be saved.",
    )
    args = parser.parse_args(argv)

    # 1️⃣ Pin reproducibility seeds before any other work
    load_and_set_seeds()

    # 2️⃣ Ensure the destination directory exists
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 3️⃣ Perform the download while computing its SHA‑256 hash
    try:
        computed_checksum = download_file(args.url, out_path)
    except Exception as exc:
        sys.exit(f"Failed to download SMILES file: {exc}")

    # 4️⃣ Load the expected checksums and verify
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
