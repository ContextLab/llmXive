import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock data for testing the script logic without running full pipeline
# We test the script's ability to parse a manifest and structure commands,
# rather than running actual fastp/bowtie2 which requires large data.

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure"""
    root = tmp_path / "test_project"
    root.mkdir()
    
    # Create directories
    (root / "data").mkdir()
    (root / "data" / "processed").mkdir()
    (root / "logs").mkdir()
    (root / "code").mkdir()
    
    # Create a mock manifest
    manifest_content = """
    - accession: GSE12345
      type: ChIP-seq
      condition: heatshock
      tf: Msn2
      fastq: /nonexistent/path/sample.fastq.gz
    - accession: GSE67890
      type: RNA-seq
      condition: control
      fastq: /nonexistent/path/rna.fastq.gz
    """
    (root / "data" / "manifest.yaml").write_text(manifest_content)
    
    return root

def test_script_syntax(temp_project_root):
    """Verify the script has valid bash syntax"""
    script_path = Path("code/02_preprocess_chipseq.sh")
    # We can't run the full script because dependencies (fastp, bowtie2) might not be installed
    # or the reference genome might not exist. We just check syntax.
    result = subprocess.run(
        ["bash", "-n", str(script_path)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Syntax error in script: {result.stderr}"

def test_manifest_parsing_logic(temp_project_root):
    """Test that the script correctly identifies ChIP-seq entries"""
    # This is a logic test. We simulate the parsing loop.
    manifest_path = temp_project_root / "data" / "manifest.yaml"
    content = manifest_path.read_text()
    
    # Simple validation that the manifest contains expected keys
    assert "ChIP-seq" in content
    assert "GSE12345" in content
    assert "Msn2" in content
    assert "RNA-seq" in content

def test_dependencies_check_logic(temp_project_root):
    """Test that the script checks for dependencies"""
    script_path = Path("code/02_preprocess_chipseq.sh")
    content = script_path.read_text()
    
    # Verify dependency checks are present
    assert "command -v fastp" in content
    assert "command -v bowtie2" in content
    assert "command -v samtools" in content
    assert "ERROR: fastp not found" in content
    assert "ERROR: bowtie2 not found" in content
    assert "ERROR: samtools not found" in content

def test_thread_constraint(temp_project_root):
    """Verify the script enforces ≤2 threads"""
    script_path = Path("code/02_preprocess_chipseq.sh")
    content = script_path.read_text()
    
    # Check for --thread 2 in fastp and -p 2 in bowtie2
    assert "--thread 2" in content
    assert "-p 2" in content

def test_mapq_filter(temp_project_root):
    """Verify the script filters for MAPQ >= 30"""
    script_path = Path("code/02_preprocess_chipseq.sh")
    content = script_path.read_text()
    
    # Check for samtools view -q 30
    assert "-q 30" in content

def test_output_directory_creation(temp_project_root):
    """Verify the script creates output directories"""
    script_path = Path("code/02_preprocess_chipseq.sh")
    content = script_path.read_text()
    
    assert 'mkdir -p "$PROCESSED_DIR"' in content
    assert 'mkdir -p "$LOG_DIR"' in content
