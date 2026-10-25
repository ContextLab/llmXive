import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.parametrize("num", [5, 10])
def test_curate_verified_source(num, tmp_path):
    """
    Run the curation script in synthetic verification mode to ensure
    that the CLI works and that the expected files are produced.
    This avoids the need for Internet access during CI while still
    exercising the script logic.
    """
    out_dir = tmp_path / "data"
    # Use the ``--verify-only`` flag to force synthetic generation.
    cmd = [
        sys.executable,
        "-m",
        "src.curators.curate_failed_figures",
        "--num",
        str(num),
        "--output-dir",
        str(out_dir),
        "--verify-only",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected directories and files
    figures_dir = out_dir / "figures"
    gt_dir = out_dir / "ground_truth"
    checksum_file = out_dir / "checksums.txt"

    # Check that the correct number of files were created.
    assert figures_dir.is_dir()
    assert gt_dir.is_dir()
    assert checksum_file.is_file()

    figure_files = list(figures_dir.glob("figure_*.png"))
    gt_files = list(gt_dir.glob("ground_truth_*.json"))
    assert len(figure_files) == num
    assert len(gt_files) == num

    # Verify that each JSON file contains a ``vector`` key.
    for gt_path in gt_files:
        data = gt_path.read_text(encoding="utf-8")
        assert '"vector":' in data