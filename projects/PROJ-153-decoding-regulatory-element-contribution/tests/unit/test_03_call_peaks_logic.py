"""
Unit tests for the logic of 03_call_peaks.sh
Since the implementation is a shell script calling MACS2, 
these tests validate the expected behavior of the script 
by mocking the environment and checking the generated summary logic.
"""
import os
import tempfile
import subprocess
import shutil
import pytest
from pathlib import Path

# We cannot easily unit test the shell script logic without mocking MACS2.
# Instead, we verify the script structure and the expected output format
# by creating a mock environment where MACS2 is a dummy script.

@pytest.fixture
def mock_macos_env(tmp_path):
    """Create a temporary environment with mock data and a dummy macs2 script."""
    # Setup directories
    input_dir = tmp_path / "data" / "processed"
    output_dir = tmp_path / "data" / "processed" / "peaks"
    input_dir.mkdir(parents=True)
    
    # Create a mock sample directory
    sample_dir = input_dir / "sample_01"
    sample_dir.mkdir()
    
    # Create a fake BAM file
    bam_file = sample_dir / "sample_01_aligned.bam"
    bam_file.write_text("FAKE_BAM_CONTENT")
    
    # Create a dummy macs2 script that generates valid narrowPeak files
    # based on the arguments passed
    macs2_script = tmp_path / "macs2_mock"
    macs2_script.write_text("""#!/bin/bash
    # Mock macs2 script
    # Arguments: -n <prefix> -f BAM -g <genome> --qvalue <qval> -n <name> ...
    # We need to parse the -n argument to find the prefix and output directory
    
    # Simple parsing: find -n and the next arg
    PREFIX=""
    OUTDIR=""
    QVAL=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n)
                PREFIX="$2"
                shift 2
                ;;
            --outdir)
                OUTDIR="$2"
                shift 2
                ;;
            --qvalue)
                QVAL="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    if [ -z "$PREFIX" ] || [ -z "$OUTDIR" ]; then
        echo "Missing required args" >&2
        exit 1
    fi
    
    # Create a fake narrowPeak file
    # Format: chrom start end name score strand signal pvalue qvalue summit
    peak_file="${OUTDIR}/${PREFIX}_peaks.narrowPeak"
    echo "chr1 100 200 peak1 1000 + 10 1e-10 ${QVAL} 50" > "$peak_file"
    echo "chr1 300 400 peak2 1000 + 10 1e-10 ${QVAL} 50" >> "$peak_file"
    echo "chr1 500 600 peak3 1000 + 10 1e-10 ${QVAL} 50" >> "$peak_file"
    
    # Create a fake broadPeak if needed (not used in this task but good to have)
    # echo "chr1 100 200 peak1 1000 + 10 1e-10 ${QVAL} 50" > "${OUTDIR}/${PREFIX}_broadPeaks.broadPeak"
    
    exit 0
    """)
    macs2_script.chmod(0o755)
    
    return {
        "tmp_path": tmp_path,
        "input_dir": input_dir,
        "output_dir": output_dir,
        "macs2_script": macs2_script,
        "summary_file": output_dir / "peak_counts_summary.tsv"
    }

def test_call_peaks_script_runs(mock_macos_env):
    """Test that the script runs and produces the expected summary file."""
    script_path = Path("code/03_call_peaks.sh")
    
    # We need to copy the script to the temp dir or run it with modified PATH
    # For simplicity, we run the script from the repo root but point input/output to temp
    # However, the script has hardcoded paths. 
    # To properly test, we will copy the script to the temp dir and modify paths or use env vars.
    # The script uses relative paths "data/processed". 
    # We will change the working directory to the temp dir.
    
    # Copy script to temp dir
    temp_script = mock_macos_env["tmp_path"] / "03_call_peaks.sh"
    shutil.copy(script_path, temp_script)
    
    # Modify the script to use the temp paths? 
    # Actually, easier: Change CWD to temp_path and modify the script to look in current dir
    # But the script uses "data/processed". 
    # Let's create the structure in temp_path
    
    # The script expects: data/processed/<sample>/...
    # We have created: tmp_path/data/processed/...
    # So we just need to run the script from tmp_path
    
    # We also need to mock macs2. We can add the temp dir to PATH
    env = os.environ.copy()
    env["PATH"] = f"{mock_macos_env['tmp_path']}:{env['PATH']}"
    env["MACS2"] = str(mock_macos_env["macs2_script"])
    
    # The script calls 'macs2'. We need to ensure our mock is found.
    # Rename our mock to 'macs2'
    mock_name = mock_macos_env["tmp_path"] / "macs2"
    shutil.move(str(mock_macos_env["macs2_script"]), str(mock_name))
    mock_name.chmod(0o755)
    
    # Run the script
    result = subprocess.run(
        ["bash", str(temp_script)],
        cwd=str(mock_macos_env["tmp_path"]),
        capture_output=True,
        text=True,
        env=env
    )
    
    # Check exit code
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check output file exists
    summary_file = mock_macos_env["summary_file"]
    assert summary_file.exists(), "Summary file not generated"
    
    # Check content
    content = summary_file.read_text()
    lines = content.strip().split("\n")
    
    # Header
    assert lines[0] == "sample_id\tfdr_threshold\tpeak_count"
    
    # Data rows (3 FDR thresholds)
    data_lines = lines[1:]
    assert len(data_lines) == 3, f"Expected 3 rows, got {len(data_lines)}"
    
    for line in data_lines:
        parts = line.split("\t")
        assert len(parts) == 3
        assert parts[0] == "sample_01"
        assert parts[1] in ["0.01", "0.05", "0.10"]
        # Our mock generated 3 peaks
        assert parts[2] == "3"

def test_script_handles_missing_bam(mock_macos_env):
    """Test that the script exits with error if no BAM files are found."""
    # Remove the BAM file
    bam_file = mock_macos_env["input_dir"] / "sample_01" / "sample_01_aligned.bam"
    if bam_file.exists():
        bam_file.unlink()
    
    script_path = Path("code/03_call_peaks.sh")
    temp_script = mock_macos_env["tmp_path"] / "03_call_peaks.sh"
    shutil.copy(script_path, temp_script)
    
    env = os.environ.copy()
    env["PATH"] = f"{mock_macos_env['tmp_path']}:{env['PATH']}"
    
    result = subprocess.run(
        ["bash", str(temp_script)],
        cwd=str(mock_macos_env["tmp_path"]),
        capture_output=True,
        text=True,
        env=env
    )
    
    # Should fail
    assert result.returncode != 0
    assert "No BAM files found" in result.stdout or "No BAM files found" in result.stderr