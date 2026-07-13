import csv
import pathlib

from data_loader import download_and_save_sample

def test_download_and_save_sample_creates_file(tmp_path, monkeypatch):
    """
    Integration test that validates:
    * The function can be called with a keyword argument.
    * The CSV file is created at the expected location.
    * The file contains the requested number of rows and the required columns.
    """
    # Force the Path.is_file check to always return False so that the
    # function does not think the file already exists.
    monkeypatch.setattr(
        pathlib.Path,
        "is_file",
        lambda self: False,
    )

    # Use a very small sample size to keep the test fast.
    download_and_save_sample(sample_size=2)

    out_path = pathlib.Path("data/raw/github-code-sample.csv")
    assert out_path.is_file(), f"Expected output file {out_path} to exist"

    with out_path.open() as f:
        rows = list(csv.DictReader(f))
        assert len(rows) == 2, "CSV should contain exactly 2 rows"
        assert "file_path" in rows[0] and "code" in rows[0], "Missing required columns"