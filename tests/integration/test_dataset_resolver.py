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
