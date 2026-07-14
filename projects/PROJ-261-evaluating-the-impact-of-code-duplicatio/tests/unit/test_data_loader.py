import csv
from pathlib import Path

import pytest

from data_loader import download_and_save_sample

def test_download_and_save_sample_writes_csv(tmp_path: Path):
    out_path = tmp_path / "github-code-sample.csv"
    rc = download_and_save_sample(sample_size=5, path=out_path)
    assert rc == 0
    with out_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 5
    assert "content" in rows[0]