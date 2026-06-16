"""
SHA-256 Checksum Generation Module for Knot Complexity Analysis Project.

This module generates SHA-256 checksums for all data files in the project,
fulfilling FR-007 reproducibility requirements for data integrity verification.

Usage:
    python -m code.reproducibility.checksums

Output:
    - data/checksums.json: JSON file with checksum records
    - docs/reproducibility/checksums.md: Human-readable checksum documentation
"""

import hashlib
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from reproducibility.logs import log_operation, get_logger


@dataclass
class ChecksumEntry:
    """Represents a single checksum record for a data file."""
    file_path: str
    file_name: str
    file_size_bytes: int
    sha256_hash: str
    algorithm: str = "SHA-256"
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ChecksumRecord:
    """Complete checksum record with metadata."""
    entries: List[ChecksumEntry]
    total_files: int
    total_size_bytes: int
    generated_at: str
    project_root: str

    def to_dict(self) -> Dict:
        return {
            "checksums": [asdict(e) for e in self.entries],
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "generated_at": self.generated_at,
            "project_root": self.project_root,
            "algorithm": "SHA-256"
        }


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks for memory efficiency with large files
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size


def find_data_files(data_dir: Path) -> List[Path]:
    """
    Find all data files in the data directory.

    Includes files with extensions: .json, .csv, .txt, .md, .png, .yaml, .yml

    Args:
        data_dir: Path to the data directory

    Returns:
        List of file paths
    """
    data_files = []
    extensions = {".json", ".csv", ".txt", ".md", ".png", ".yaml", ".yml", ".parquet"}

    if not data_dir.exists():
        return data_files

    for ext in extensions:
        data_files.extend(data_dir.rglob(f"*{ext}"))

    return sorted(data_files)


def record_checksums(data_dir: Path, project_root: Path) -> ChecksumRecord:
    """
    Compute and record checksums for all data files.

    Args:
        data_dir: Path to the data directory
        project_root: Path to the project root

    Returns:
        ChecksumRecord with all checksum entries
    """
    logger = get_logger()
    logger.info(f"Computing checksums for data directory: {data_dir}")

    data_files = find_data_files(data_dir)
    entries = []
    total_size = 0

    for file_path in data_files:
        try:
            file_size = get_file_size(file_path)
            file_hash = compute_sha256(file_path)

            entry = ChecksumEntry(
                file_path=str(file_path.relative_to(project_root)),
                file_name=file_path.name,
                file_size_bytes=file_size,
                sha256_hash=file_hash
            )
            entries.append(entry)
            total_size += file_size

            logger.info(f"Checksum computed: {file_path.name} ({file_size} bytes)")

        except Exception as e:
            logger.warning(f"Failed to compute checksum for {file_path}: {e}")

    return ChecksumRecord(
        entries=entries,
        total_files=len(entries),
        total_size_bytes=total_size,
        generated_at=datetime.now(timezone.utc).isoformat(),
        project_root=str(project_root)
    )


def write_checksums_json(record: ChecksumRecord, output_path: Path) -> None:
    """
    Write checksum record to JSON file.

    Args:
        record: ChecksumRecord to write
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(record.to_dict(), f, indent=2)


def write_checksums_csv(record: ChecksumRecord, output_path: Path) -> None:
    """
    Write checksum record to CSV file.

    Args:
        record: ChecksumRecord to write
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "file_name", "file_size_bytes", "sha256_hash", "algorithm", "generated_at"])
        for entry in record.entries:
            writer.writerow([
                entry.file_path,
                entry.file_name,
                entry.file_size_bytes,
                entry.sha256_hash,
                entry.algorithm,
                entry.generated_at
            ])


def write_checksums_documentation(record: ChecksumRecord, output_path: Path) -> None:
    """
    Write human-readable checksum documentation in Markdown format.

    Args:
        record: ChecksumRecord to document
        output_path: Path to output Markdown file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Data File Checksums",
        "",
        f"**Generated:** {record.generated_at}",
        f"**Total Files:** {record.total_files}",
        f"**Total Size:** {record.total_size_bytes:,} bytes",
        f"**Algorithm:** SHA-256",
        "",
        "## Checksum Table",
        "",
        "| File Path | File Name | Size (bytes) | SHA-256 Hash |",
        "|-----------|-----------|--------------|--------------|"
    ]

    for entry in record.entries:
        lines.append(
            f"| {entry.file_path} | {entry.file_name} | {entry.file_size_bytes:,} | `{entry.sha256_hash}` |"
        )

    lines.extend([
        "",
        "## Verification Instructions",
        "",
        "To verify data integrity, compute the SHA-256 hash of each file and compare against the values above:",
        "",
        "```bash",
        "# Linux/Mac",
        "sha256sum <file_path>",
        "",
        "# Windows PowerShell",
        "Get-FileHash <file_path> -Algorithm SHA256",
        "```",
        "",
        "## Purpose",
        "",
        "These checksums are generated per FR-007 reproducibility requirements to ensure",
        "data integrity throughout the analysis pipeline. Any modification to the data files",
        "will result in a different hash value, indicating potential data corruption or unauthorized changes.",
        "",
        "## Files Included",
        ""
    ])

    # Group files by directory
    files_by_dir: Dict[str, List[str]] = {}
    for entry in record.entries:
        dir_name = str(Path(entry.file_path).parent)
        if dir_name not in files_by_dir:
            files_by_dir[dir_name] = []
        files_by_dir[dir_name].append(entry.file_name)

    for dir_name, files in sorted(files_by_dir.items()):
        lines.append(f"- **{dir_name}/**")
        for fname in sorted(files):
            lines.append(f"  - {fname}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    """
    Main entry point for checksum generation.

    Returns:
        0 on success, 1 on failure
    """
    logger = get_logger()
    logger.info("Starting checksum generation for data files")

    try:
        # Determine project root and data directory
        project_root = Path(__file__).parent.parent.parent.parent
        data_dir = project_root / "data"

        logger.info(f"Project root: {project_root}")
        logger.info(f"Data directory: {data_dir}")

        # Check if data directory exists
        if not data_dir.exists():
            logger.error(f"Data directory does not exist: {data_dir}")
            return 1

        # Record checksums
        record = record_checksums(data_dir, project_root)

        if record.total_files == 0:
            logger.warning("No data files found to checksum")
            # Still create empty documentation
            output_json = data_dir / "checksums.json"
            output_csv = data_dir / "checksums.csv"
            output_md = project_root / "docs" / "reproducibility" / "checksums.md"
            write_checksums_json(record, output_json)
            write_checksums_csv(record, output_csv)
            write_checksums_documentation(record, output_md)
            logger.info("Empty checksum record created")
            return 0

        # Write outputs
        output_json = data_dir / "checksums.json"
        output_csv = data_dir / "checksums.csv"
        output_md = project_root / "docs" / "reproducibility" / "checksums.md"

        write_checksums_json(record, output_json)
        write_checksums_csv(record, output_csv)
        write_checksums_documentation(record, output_md)

        logger.info(f"Checksums recorded for {record.total_files} files")
        logger.info(f"JSON output: {output_json}")
        logger.info(f"CSV output: {output_csv}")
        logger.info(f"Documentation: {output_md}")

        # Log operation
        log_operation(
            operation="checksum_generation",
            input_file=str(data_dir),
            output_file=str(output_json),
            parameters={"total_files": record.total_files, "algorithm": "SHA-256"},
            status="success"
        )

        return 0

    except Exception as e:
        logger.error(f"Checksum generation failed: {e}")
        log_operation(
            operation="checksum_generation",
            input_file=str(data_dir),
            output_file="",
            parameters={},
            status="failed",
            error=str(e)
        )
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
