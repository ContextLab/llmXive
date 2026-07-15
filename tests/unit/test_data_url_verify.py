"""D9 — a data URL must prove RECORDS (not just sniff parseable) to verify.

Locks the fix to ``data_source_discovery._verify_data_url`` +
``dataset_resolver.sample_records``: a URL is verified only when a streamed
sample both sniffs as a dataset format AND parses into ``record_count > 0`` real
records with a real ``field_coverage``. A format-sniff-only "parsed" (the old
``record_count=0`` + ``field_coverage=1.0`` free pass) is REJECTED.

Real HTTP over an ephemeral localhost server (only ``requests``' network endpoint
is a real socket; all parsing/gate logic is exercised for real). Run with
``LLMXIVE_ALLOW_LOCALHOST=1``.
"""
from __future__ import annotations

import functools
import http.server
import socketserver
import threading

import pytest

from llmxive.librarian.data_source_discovery import _verify_data_url
from llmxive.librarian.dataset_resolver import sample_records


@pytest.fixture
def file_server(tmp_path):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield tmp_path, f"http://127.0.0.1:{port}"
    httpd.shutdown()


# --- sample_records: real record + field extraction ----------------------------


def test_sample_records_counts_csv_rows_and_fields(file_server):
    root, base = file_server
    (root / "d.csv").write_text("crossing_number,braid_index\n3,2\n4,3\n5,2\n")
    sr = sample_records(f"{base}/d.csv")
    assert sr.parsed is True
    assert sr.record_count == 3
    assert "crossing_number" in sr.fields and "braid_index" in sr.fields


def test_sample_records_counts_json_array(file_server):
    root, base = file_server
    (root / "d.json").write_text('[{"crossing_number": 3}, {"crossing_number": 4}]')
    sr = sample_records(f"{base}/d.json")
    assert sr.parsed is True and sr.record_count == 2
    assert sr.fields == ["crossing_number"]


def test_sample_records_counts_jsonl(file_server):
    root, base = file_server
    (root / "d.jsonl").write_text('{"a": 1, "b": 2}\n{"a": 3, "b": 4}\n{"a": 5, "b": 6}\n')
    sr = sample_records(f"{base}/d.jsonl")
    assert sr.parsed is True and sr.record_count == 3
    assert sr.fields == ["a", "b"]


def test_header_only_csv_yields_zero_records(file_server):
    # Sniffs as CSV (2 columns) but has NO data rows → not record-verifiable.
    root, base = file_server
    (root / "empty.csv").write_text("a,b\n")
    sr = sample_records(f"{base}/empty.csv")
    assert sr.record_count == 0
    assert sr.parsed is False  # 0 records => not a verified sample


# --- _verify_data_url: records + coverage gate ---------------------------------


def test_data_url_verified_with_records_and_coverage(file_server):
    root, base = file_server
    (root / "d.csv").write_text("crossing_number,braid_index\n3,2\n4,3\n")
    proposal = {"kind": "data_url", "ref": f"{base}/d.csv",
                "access_python": "import pandas as pd; pd.read_csv(url)"}
    vs = _verify_data_url(proposal, required_fields=["crossing number"])
    assert vs is not None
    assert vs.kind == "data_url"
    assert vs.record_count == 2  # real count, NOT 0
    assert vs.field_coverage >= 0.5  # real coverage from parsed header


def test_data_url_zero_records_rejected_even_without_required_fields(file_server):
    # This is the killed false-pass: no required_fields USED to grant coverage=1.0
    # on a record_count=0 sniff. Now a 0-record URL is rejected outright.
    root, base = file_server
    (root / "empty.csv").write_text("a,b\n")
    proposal = {"kind": "data_url", "ref": f"{base}/empty.csv", "access_python": "x"}
    assert _verify_data_url(proposal, required_fields=None) is None


def test_data_url_html_rejected(file_server):
    root, base = file_server
    (root / "page.html").write_text("<html><body>not a dataset</body></html>")
    proposal = {"kind": "data_url", "ref": f"{base}/page.html", "access_python": "x"}
    assert _verify_data_url(proposal, required_fields=None) is None


def test_data_url_wrong_schema_scores_low_coverage(file_server):
    root, base = file_server
    # Two columns (so it sniffs as CSV) but NEITHER matches the required schema.
    (root / "names.csv").write_text("id,name\n1,foo\n2,bar\n3,baz\n")
    proposal = {"kind": "data_url", "ref": f"{base}/names.csv", "access_python": "x"}
    vs = _verify_data_url(
        proposal, required_fields=["crossing number", "braid index", "volume"]
    )
    # It loads records, but none of the required columns are present → 0 coverage
    # (the caller's coverage gate then rejects it as the wrong dataset).
    assert vs is not None and vs.record_count == 3
    assert vs.field_coverage == 0.0


def test_non_http_ref_rejected():
    # A pip package name is not a data URL.
    assert _verify_data_url(
        {"kind": "data_url", "ref": "database-knotinfo", "access_python": "x"}
    ) is None
