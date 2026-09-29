import os
from pathlib import Path
from utils.io import compute_file_checksum

def generate_checksums(data_dir: Path = Path("data")) -> Path:
    """
    Compute SHA-256 checksums for all files under ``data_dir`` (recursively)
    and write them to ``data_dir / "checksums.txt"``. Each line of the output
    file contains the relative path to the data file and its checksum,
    separated by whitespace.

    The function returns the path to the generated checksums file.
    """
    checksums_path = data_dir / "checksums.txt"

    # Ensure the data directory exists
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory '{data_dir}' does not exist.")

    with checksums_path.open("w") as f:
        for root, _, files in os.walk(data_dir):
            for name in files:
                file_path = Path(root) / name
                # Skip the checksums file itself to avoid recursion
                if file_path == checksums_path:
                    continue
                # Compute checksum
                checksum = compute_file_checksum(file_path)
                # Write relative path (POSIX style) and checksum
                rel_path = file_path.relative_to(data_dir).as_posix()
                f.write(f"{rel_path} {checksum}\n")
    return checksums_path
