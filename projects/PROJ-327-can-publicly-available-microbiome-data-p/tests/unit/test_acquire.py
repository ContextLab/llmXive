import sys
from pathlib import Path

import pytest

from code.acquire import download_sra_fastq, _read_checksum_file

def test_download_sra_fastq_creates_files(tmp_path: Path):
    """
    Verify that a real public SRA accession is downloaded and that a
    checksum entry is recorded.
    """
    out_dir = tmp_path / "fastq"
    # Use a tiny test accession known to be publicly available.
    accession = ["SRR390728"]
    download_sra_fastq(accession, out_dir)

    # Expect both forward and reverse reads.
    for read_num in (1, 2):
        expected_file = out_dir / f"{accession[0]}_{read_num}.fastq.gz"
        assert expected_file.is_file()

    # Verify that the checksum manifest now contains two entries.
    checksums = _read_checksum_file()
    assert f"{accession[0]}_1.fastq.gz" in checksums
    assert f"{accession[0]}_2.fastq.gz" in checksums

def test_download_sra_fastq_missing_accession_raises():
    """
    If an invalid accession is supplied the function should raise the
    FR‑008 RuntimeError.
    """
    out_dir = Path("does_not_matter")
    with pytest.raises(RuntimeError, match="Metabolomics data unavailable – aborting per FR-008"):
        download_sra_fastq(["INVALID_ACCESSION"], out_dir)
