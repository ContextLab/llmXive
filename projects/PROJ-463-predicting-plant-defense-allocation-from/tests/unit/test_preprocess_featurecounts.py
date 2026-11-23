import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.preprocess_featurecounts import (
    check_featurecounts_available,
    run_featurecounts,
    calculate_tpm,
    create_manifest_entry_tpm,
    compute_sha256
)

@patch('subprocess.run')
def test_check_featurecounts_available(mock_run):
    """Test checking if featureCounts is available."""
    mock_run.return_value = MagicMock(returncode=0, stdout="featureCounts v2.0.1")
    assert check_featurecounts_available() is True
    
    mock_run.return_value = MagicMock(returncode=1, stderr="Error")
    assert check_featurecounts_available() is False
    
    mock_run.side_effect = FileNotFoundError()
    assert check_featurecounts_available() is False

def test_run_featurecounts_missing_input(tmp_path):
    """Test run_featurecounts with missing BAM file."""
    result = run_featurecounts(
        bam_file=tmp_path / "nonexistent.bam",
        gtf_file=tmp_path / "annotation.gtf",
        output_dir=tmp_path,
        accession_id="test_001"
    )
    assert result is None

def test_calculate_tpm_with_sample_data(tmp_path):
    """Test TPM calculation with sample data."""
    # Create a mock counts file
    counts_content = """\
    #geneid\tchr\tstart\tend\tstrand\tlength\tstatus\tsample1
    GeneA\tchr1\t100\t200\t+\t100\tAssigned\t100
    GeneB\tchr2\t300\t400\t-\t200\tAssigned\t200
    GeneC\tchr3\t500\t600\t+\t50\tAssigned\t50
    """
    counts_file = tmp_path / "counts.txt"
    counts_file.write_text(counts_content)

    tpm_file = calculate_tpm(
        counts_file=counts_file,
        output_dir=tmp_path,
        accession_id="test_001"
    )

    assert tpm_file is not None
    assert tpm_file.exists()
    
    # Verify content
    import pandas as pd
    df = pd.read_csv(tpm_file)
    assert 'Geneid' in df.columns
    assert 'sample1_TPM' in df.columns
    assert len(df) == 3

def test_create_manifest_entry_tpm(tmp_path):
    """Test manifest entry creation."""
    tpm_file = tmp_path / "test_tpm.csv"
    tpm_file.write_text("Geneid,sample1_TPM\nGeneA,1000.0")
    
    entry = create_manifest_entry_tpm(
        file_path=tpm_file,
        accession_id="test_001",
        source_bam=tmp_path / "test.bam",
        source_gtf=tmp_path / "gtf.gtf"
    )
    
    assert entry['accession_id'] == "test_001"
    assert 'checksum' in entry
    assert entry['source_type'] == "featurecounts"
    assert 'created_at' in entry

@patch('subprocess.run')
def test_main_synthetic_mode(mock_run, tmp_path):
    """Test main function in synthetic mode."""
    # Mock arguments
    sys.argv = [
        'test_preprocess_featurecounts.py',
        '--bam-dir', str(tmp_path),
        '--gtf', str(tmp_path / 'gtf.gtf'),
        '--output-dir', str(tmp_path / 'out'),
        '--mode', 'synthetic'
    ]
    
    # Should exit early without running featureCounts
    with patch('src.data.preprocess_featurecounts.logger') as mock_logger:
        from src.data.preprocess_featurecounts import main
        main()
        # Verify it logged synthetic mode
        mock_logger.info.assert_any_call("Synthetic mode active. Skipping featureCounts execution.")
        mock_run.assert_not_called()