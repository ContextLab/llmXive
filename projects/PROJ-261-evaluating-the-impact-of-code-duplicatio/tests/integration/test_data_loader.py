import csv
import pathlib

from data_loader import download_and_save_sample

def test_download_and_save_sample_creates_file(tmp_path, monkeypatch):
    # Monkey‑patch the output location to a temporary directory
    monkeypatch.setattr(
        "pathlib.Path.is_file",
        lambda self: False,
    )
    download_and_save_sample(sample_size=2)

    out_path = pathlib.Path("data/raw/github-code-sample.csv")
    assert out_path.is_file()
    with out_path.open() as f:
        rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert "file_path" in rows[0] and "code" in rows[0]
