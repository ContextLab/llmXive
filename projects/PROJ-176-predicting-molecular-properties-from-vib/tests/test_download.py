"""
Simple integration test for the download script (T003).
Verifies that the expected raw files are created and that the checksum
JSON contains a status of ``ok``.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths

def test_download_creates_files(tmp_path, monkeypatch):
    # Monkey‑patch the project root so that the script writes into a temporary area.
    # This avoids polluting the repository during the test run.
    from code import main as cli_main

    # Adjust environment so that the script thinks it's running from the project root.
    monkeypatch.chdir(tmp_path)

    # Run the download command via the CLI entry point.
    # The CLI expects no arguments for the download sub‑command.
    cli_main.setup_cli().parse_args(["download"])

    # Import and invoke the download main directly (the CLI wrapper calls it).
    from data.download import main as download_main
    download_main()

    # Expected paths
    qm9_path = Path("data/raw/qm9.parquet")
    ir_path = Path("data/raw/ir_spectra.parquet")
    checksums_path = paths.results("checksums.json")
    alignment_report = Path("data/processed/alignment_report.json")

    # Verify files exist
    assert qm9_path.is_file(), "QM9 parquet file was not created"
    assert ir_path.is_file(), "IR spectra parquet file was not created"
    assert checksums_path.is_file(), "Checksums JSON was not created"
    assert alignment_report.is_file(), "Alignment report JSON was not created"

    # Verify checksum JSON content
    with open(checksums_path) as f:
        data = json.load(f)
    assert data.get("status") == "ok", "Checksum status is not ok"
    assert "qm9.parquet" in data["files"], "QM9 checksum missing"
    assert "ir_spectra.parquet" in data["files"], "IR spectra checksum missing"