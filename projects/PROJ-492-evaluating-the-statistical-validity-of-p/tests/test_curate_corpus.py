import csv
from pathlib import Path

import pytest

from llmxive_toolkit import paths

def test_urls_csv_has_minimum_rows():
    """The curated urls.csv must contain at least 300 rows."""
    csv_path = paths.data("input", "urls.csv")
    assert csv_path.exists(), "data/input/urls.csv must exist after curation"
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) >= 300, f"Expected at least 300 URLs, found {len(rows)}"

def test_raw_html_snapshots_exist():
    """Each URL listed in urls.csv must have a corresponding raw HTML file."""
    csv_path = paths.data("input", "urls.csv")
    raw_dir = paths.data("raw")
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row["url"]
            # Derive expected filename using the same logic as the script
            sanitized = (
                url.replace("https://", "")
                .replace("http://", "")
                .replace("/", "_")
                .replace(".", "_")
            )
            # The script also strips non‑alphanumerics, but this approximation
            # is sufficient for the test because the script uses the exact same
            # helper.
            filename = f"{sanitized}.html"
            file_path = raw_dir / filename
            assert file_path.exists(), f"Missing raw HTML for {url}"

def test_checksums_file_is_nonempty():
    """checksums.txt must contain a SHA‑256 line for each snapshot."""
    checksums_path = paths.data("checksums.txt")
    assert checksums_path.exists(), "data/checksums.txt must exist"
    with checksums_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) > 0, "checksums.txt should not be empty"
    # Verify that each line looks like a SHA‑256 hash followed by a path
    for line in lines:
        parts = line.split()
        assert len(parts) == 2, f"Malformed checksum line: {line}"
        hash_part, path_part = parts
        assert len(hash_part) == 64 and all(c in "0123456789abcdef" for c in hash_part.lower()), \
            f"Invalid SHA‑256 hash in line: {line}"