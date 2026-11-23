import pytest
import tempfile
from pathlib import Path
import json

from code.scan import parse_fimo_output, FimoParseError

@pytest.fixture
def sample_fimo_tsv(tmp_path):
    """Create a sample FIMO TSV file for testing."""
    content = """# motif_id\tmotif_alt_id\tsequence_name\tstart\tstop\tstrand\tscore\tp-value\tq-value\tmatched_sequence
MA0001.1\tMA0001.1\tchr1\t100\t115\t+\t12.5\t0.00005\t0.0001\tACGTACGTACGTACG
MA0002.2\tMA0002.2\tchr1\t200\t220\t-\t15.0\t0.00003\t0.00008\tGCTAGCTAGCTAGCT
MA0001.1\tMA0001.1\tchr2\t300\t315\t+\t10.0\t0.00010\t0.00020\tTACGTACGTACGTAC
"""
    fimo_file = tmp_path / "fimo.tsv"
    fimo_file.write_text(content)
    return fimo_file

@pytest.fixture
def malformed_fimo_tsv(tmp_path):
    """Create a malformed FIMO TSV file for testing."""
    content = """# motif_id\tmotif_alt_id\tsequence_name\tstart\tstop\tstrand\tscore\tp-value\tq-value\tmatched_sequence
MA0001.1\tMA0001.1\tchr1\t100\t115\t+\t12.5\t0.00005\t0.0001
"""
    fimo_file = tmp_path / "fimo_malformed.tsv"
    fimo_file.write_text(content)
    return fimo_file

def test_parse_fimo_output(sample_fimo_tsv):
    """Test parsing of valid FIMO output."""
    matches = parse_fimo_output(sample_fimo_tsv)

    assert len(matches) == 3
    assert matches[0]['motif_id'] == 'MA0001.1'
    assert matches[0]['sequence_name'] == 'chr1'
    assert matches[0]['start'] == 100
    assert matches[0]['stop'] == 115
    assert matches[0]['strand'] == '+'
    assert abs(matches[0]['p_value'] - 0.00005) < 1e-10
    assert abs(matches[0]['q_value'] - 0.0001) < 1e-10
    assert matches[0]['matched_sequence'] == 'ACGTACGTACGTACG'

def test_parse_fimo_output_malformed_lines(malformed_fimo_tsv, caplog):
    """Test that malformed lines are skipped with a warning."""
    with caplog.at_level('WARNING'):
        matches = parse_fimo_output(malformed_tsv)

    # Should skip the malformed line and return empty or partial results
    # Based on current implementation, it logs a warning and skips
    assert len(matches) == 0  # Only header and one malformed line

def test_parse_fimo_output_nonexistent_file():
    """Test parsing of non-existent file."""
    with pytest.raises(FileNotFoundError):
        parse_fimo_output(Path("/nonexistent/path/fimo.tsv"))