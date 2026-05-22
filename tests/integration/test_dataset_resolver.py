import functools
import http.server
import io
import socketserver
import threading
import zipfile

import pytest


@pytest.fixture
def file_server(tmp_path):
    # Serve tmp_path over real HTTP on an ephemeral port.
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield tmp_path, f"http://127.0.0.1:{port}"
    httpd.shutdown()


def test_sniff_format_detects_csv(file_server):
    from llmxive.librarian.dataset_resolver import sniff_format
    root, base = file_server
    (root / "data.csv").write_text("a,b,c\n1,2,3\n4,5,6\n")
    rep = sniff_format(f"{base}/data.csv")
    assert rep.parsed is True
    assert rep.format == "csv"
    assert rep.downloaded_bytes > 0


def test_sniff_format_detects_zip(file_server):
    from llmxive.librarian.dataset_resolver import sniff_format
    root, base = file_server
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("inner.txt", "hello")
    (root / "data.zip").write_bytes(buf.getvalue())
    rep = sniff_format(f"{base}/data.zip")
    assert rep.parsed is True and rep.format == "zip"


def test_sniff_format_rejects_html_as_unparseable(file_server):
    from llmxive.librarian.dataset_resolver import sniff_format
    root, base = file_server
    (root / "page.html").write_text("<html><body>not a dataset</body></html>")
    rep = sniff_format(f"{base}/page.html")
    assert rep.parsed is False


def test_verify_candidate_reachable_csv(file_server):
    from llmxive.librarian.dataset_sources import DatasetCandidate
    from llmxive.librarian.dataset_resolver import verify_candidate
    root, base = file_server
    (root / "d.csv").write_text("x,y\n1,2\n")
    c = DatasetCandidate("D", f"{base}/d.csv", "D", "figshare")
    v = verify_candidate(c)
    assert v is not None and v.format == "csv"


def test_verify_candidate_404_returns_none(file_server):
    from llmxive.librarian.dataset_sources import DatasetCandidate
    from llmxive.librarian.dataset_resolver import verify_candidate
    root, base = file_server
    c = DatasetCandidate("D", f"{base}/missing.csv", "D", "figshare")
    assert verify_candidate(c) is None


def test_extract_dataset_intents_finds_doi_and_name():
    from llmxive.librarian.dataset_resolver import extract_dataset_intents
    spec = ("## FR\n- **FR-001**: download the QM9 dataset "
            "(DOI: 10.1038/sdata.2014.22) with integrity verification\n")
    intents = extract_dataset_intents(spec)
    assert "10.1038/sdata.2014.22" in intents          # DOI captured
    assert any("qm9" in i.lower() for i in intents)      # named dataset captured


def test_resolve_datasets_real_qm9(tmp_path):
    """Real-call: QM9 must resolve to >=1 verified candidate across the sources."""
    from llmxive.librarian.dataset_resolver import resolve_datasets
    spec = "- **FR-001**: download the QM9 dataset (DOI: 10.1038/sdata.2014.22)\n"
    result = resolve_datasets(spec, project_dir=tmp_path, repo_root=tmp_path, top_n=3)
    verified = [d for d in result.datasets if d.status == "verified"]
    assert verified, f"QM9 did not resolve; tried: {result.datasets}"
    top = verified[0]
    assert 1 <= len(top.candidates) <= 3
    assert top.candidates[0]["url"].startswith("http")


def test_write_manifest_roundtrip(tmp_path):
    import yaml
    from llmxive.librarian.dataset_resolver import (
        ResolvedDatasets, ResolvedIntent, write_manifest,
    )
    rd = ResolvedDatasets(datasets=[
        ResolvedIntent("QM9", "verified",
                       candidates=[{"url": "https://x/y", "source": "huggingface",
                                    "format": "parquet", "relevance": 0.9,
                                    "sample_check": {"downloaded_bytes": 10, "parsed": True}}],
                       candidates_tried=[]),
    ])
    path = write_manifest(rd, project_dir=tmp_path)
    doc = yaml.safe_load(path.read_text())
    assert doc["datasets"][0]["intent"] == "QM9"
    assert doc["datasets"][0]["candidates"][0]["url"] == "https://x/y"


def test_unresolved_intents_lists(tmp_path):
    from llmxive.librarian.dataset_resolver import ResolvedDatasets, ResolvedIntent, unresolved_intents
    rd = ResolvedDatasets(datasets=[
        ResolvedIntent("QM9", "verified", candidates=[{"url": "u"}], candidates_tried=[]),
        ResolvedIntent("BogusSet", "unresolved", candidates=[], candidates_tried=[]),
    ])
    assert unresolved_intents(rd) == ["BogusSet"]
