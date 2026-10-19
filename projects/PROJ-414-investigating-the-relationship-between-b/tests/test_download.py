"""Tests for the verified parquet download (T001)."""
import json

import pyarrow.parquet as pq
from llmxive_toolkit import paths

SHARD = "test-00000-of-00016.parquet"


def _raw():
    p = paths.data("raw", SHARD)
    assert p.is_file() and p.stat().st_size > 0, f"raw shard missing/empty: {p}"
    return p


def _inventory():
    p = paths.data("raw", "column_inventory.json")
    assert p.is_file(), "column_inventory.json not found"
    return json.loads(p.read_text())


def test_parquet_loads_with_pyarrow():
    pf = pq.ParquetFile(_raw())
    assert pf.metadata.num_rows > 0
    assert len(pf.schema_arrow.names) > 0


def test_checksums_file_matches_sha256():
    c = json.loads(paths.data("checksums.json").read_text())
    assert SHARD in c and len(c[SHARD]) == 64
    inv = _inventory()
    assert inv["source"]["sha256"] == c[SHARD]


def test_inventory_reflects_actual_schema():
    inv = _inventory()
    pf = pq.ParquetFile(_raw())
    assert inv["columns"] == list(pf.schema_arrow.names)
    for field, status in inv["expected_fields"].items():
        assert isinstance(status["present"], bool)
        if status["present"]:
            assert status["matched_column"] in inv["columns"]


def test_available_subject_count_matches_parquet():
    inv = _inventory()
    n = inv["available_subject_count"]
    assert isinstance(n, int) and n >= 0
    subj_col = inv["subject_column"]
    if subj_col is None:
        assert n == 0
        return
    assert n > 0, "subject column exists but count is not positive"
    pf = pq.ParquetFile(_raw())
    seen = set()
    for rg in range(pf.num_row_groups):
        tbl = pf.read_row_group(rg, columns=[subj_col])
        seen.update(tbl.column(subj_col).to_pylist())
    seen.discard(None)
    assert n == len(seen), f"inventory {n} != pyarrow distinct {len(seen)}"