"""
Unit tests for null region definition logic (T009a).
Tests the shell script execution and output validation.
"""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path

# Helper to create mock files
def create_mock_files(tmp_path):
    """Create necessary mock input files for the script."""
    # Create mock genome size file
    genome_file = tmp_path / "yeast_s288c.genome"
    genome_file.write_text("chrI\t230000\nchrII\t810000\nchrIII\t316000\n")

    # Create mock gene annotation file (BED format)
    # chrI: 1000-2000, chrII: 50000-51000
    genes_file = tmp_path / "genes.bed"
    genes_file.write_text(
        "chrI\t1000\t2000\tGENE1\n"
        "chrII\t50000\t51000\tGENE2\n"
    )

    return genome_file, genes_file

def test_null_region_script_execution(tmp_path):
    """Test that the script runs and produces output."""
    genome_file, genes_file = create_mock_files(tmp_path)
    output_file = tmp_path / "null_regions.bed"

    # Construct environment variables
    env = os.environ.copy()
    env["GENOME_SIZE_FILE"] = str(genome_file)
    env["GENE_ANNOTATION_FILE"] = str(genes_file)
    env["OUTPUT_FILE"] = str(output_file)

    # Run the script
    script_path = Path("code/06a_define_null_regions.sh")
    # We need to copy the script to tmp_path or run it with full path
    # For this test, we assume the script is in the project root
    result = subprocess.run(
        ["bash", str(script_path)],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True
    )

    # The script expects data/processed/ directory relative to cwd
    # We need to adjust the script or the test setup to handle relative paths correctly
    # For now, let's assume the script runs from the project root
    # and we create the necessary directory structure in tmp_path
    
    # Create the expected directory structure relative to tmp_path
    (tmp_path / "data" / "reference").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    
    # Move files to expected locations
    (tmp_path / "data" / "reference" / "yeast_s288c.genome").write_text(genome_file.read_text())
    (tmp_path / "data" / "processed" / "genes.bed").write_text(genes_file.read_text())
    
    # Update env to use relative paths from tmp_path
    env["GENOME_SIZE_FILE"] = "data/reference/yeast_s288c.genome"
    env["GENE_ANNOTATION_FILE"] = "data/processed/genes.bed"
    env["OUTPUT_FILE"] = "data/processed/null_regions.bed"

    result = subprocess.run(
        ["bash", str(script_path)],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True
    )

    # Check exit code
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Check output file exists
    assert output_file.exists(), "Output file was not created"

    # Check output is not empty (should have regions)
    content = output_file.read_text()
    assert len(content.strip()) > 0, "Output file is empty"

    # Verify BED format (at least 3 columns)
    for line in content.strip().split('\n'):
        if not line.startswith('#'):
            parts = line.split('\t')
            assert len(parts) >= 3, f"Invalid BED line: {line}"
            # Verify coordinates are numeric
            int(parts[1])
            int(parts[2])

def test_no_genes_file_error():
    """Test that script fails gracefully if genes file is missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        genome_file = tmp_path / "yeast_s288c.genome"
        genome_file.write_text("chrI\t230000\n")
        
        env = os.environ.copy()
        env["GENOME_SIZE_FILE"] = str(genome_file)
        env["GENE_ANNOTATION_FILE"] = str(tmp_path / "missing_genes.bed")
        env["OUTPUT_FILE"] = str(tmp_path / "null_regions.bed")

        result = subprocess.run(
            ["bash", "code/06a_define_null_regions.sh"],
            env=env,
            cwd=tmp_path,
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "ERROR" in result.stderr
        assert "not found" in result.stderr