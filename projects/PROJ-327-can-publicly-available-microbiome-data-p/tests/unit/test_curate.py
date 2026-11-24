import pandas as pd
import pytest

from code.curate import run_dada2, main
from llmxive_toolkit import paths

def test_asv_table_schema(tmp_path, monkeypatch):
    """
    Run the curate step on a tiny synthetic FASTQ pair and verify that
    the resulting CSV has the required schema (integer counts, columns
    prefixed with ``asv_``).  The test uses the real fallback implementation,
    so it works even when the R environment is missing.
    """
    # Create a minimal FASTQ file (forward only) with two reads.
    fastq_dir = tmp_path / "fastq"
    fastq_dir.mkdir()
    fwd = fastq_dir / "SRR000001_1.fastq.gz"
    rev = fastq_dir / "SRR000001_2.fastq.gz"

    # Simple 4‑line FASTQ records (sequence = "AAAA")
    content = (
        "@seq1\nAAAA\n+\n!!!!\n"
        "@seq2\nCCCC\n+\n!!!!\n"
    ).encode()
    import gzip
    with gzip.open(fwd, "wb") as fh:
        fh.write(content)
    with gzip.open(rev, "wb") as fh:
        fh.write(content)

    # Monkey‑patch the paths helper so that curate looks at our temp dir.
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / Path(*parts))

    output_path = tmp_path / "asv_table.csv"
    run_dada2(tmp_path / "fastq", output_path)

    df = pd.read_csv(output_path, index_col="sample_id")
    # All column names must start with 'asv_'
    for col in df.columns:
        assert col.startswith("asv_")
        # Values must be non‑negative integers
        assert pd.api.types.is_integer_dtype(df[col])
        assert (df[col] >= 0).all()

def test_main_creates_file(tmp_path, monkeypatch):
    """
    Ensure that the CLI entry point writes to the default location.
    """
    fastq_dir = tmp_path / "raw" / "sra_fastq"
    fastq_dir.mkdir(parents=True)
    # Re‑use the same tiny FASTQ pair as above.
    fwd = fastq_dir / "SRR000001_1.fastq.gz"
    rev = fastq_dir / "SRR000001_2.fastq.gz"
    content = (
        "@seq1\nAAAA\n+\n!!!!\n"
        "@seq2\nCCCC\n+\n!!!!\n"
    ).encode()
    import gzip
    with gzip.open(fwd, "wb") as fh:
        fh.write(content)
    with gzip.open(rev, "wb") as fh:
        fh.write(content)

    # Patch paths.data to point inside tmp_path.
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / Path(*parts))

    # Run the module's main function.
    main()

    out_path = tmp_path / "processed" / "asv_table.csv"
    assert out_path.is_file()