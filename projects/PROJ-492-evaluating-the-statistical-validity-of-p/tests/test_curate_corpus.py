import subprocess
import sys
from pathlib import Path

def test_curate_corpus_runs_successfully():
    """
    Verify that the curate_corpus script exits with status 0 and
    produces the required artefacts.
    """
    # Run the module as a script
    result = subprocess.run(
        [sys.executable, "-m", "code.src.audit.curate_corpus"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Check that the URLs CSV exists and has at least TARGET_COUNT rows
    urls_csv = Path("data/input/urls.csv")
    assert urls_csv.is_file(), "urls.csv was not created"

    with urls_csv.open() as f:
        lines = f.readlines()
    # Header + at least TARGET_COUNT rows
    assert len(lines) >= 301, f"Expected at least 300 URLs, got {len(lines)-1}"

    # Verify that raw HTML files were written
    raw_dir = Path("data/raw")
    assert raw_dir.is_dir(), "data/raw directory missing"
    html_files = list(raw_dir.glob("*.html"))
    assert len(html_files) >= 300, f"Expected >=300 HTML files, found {len(html_files)}"

    # Verify checksums file
    checksums = Path("data/checksums.txt")
    assert checksums.is_file(), "checksums.txt missing"
    with checksums.open() as f:
        checksum_lines = f.readlines()
    assert len(checksum_lines) >= 300, "Checksums file does not contain entries for all HTML files"