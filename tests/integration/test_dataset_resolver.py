import functools
import http.server
import io
import os
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


def test_sniff_format_detects_xyz(file_server):
    # XYZ molecular geometry: atom-count line, comment line, then "<El> x y z".
    # QM9 is natively .xyz, so this must be sniffable (FIX 1).
    from llmxive.librarian.dataset_resolver import sniff_format
    root, base = file_server
    (root / "mol.xyz").write_text(
        "3\nwater\n"
        "O  0.0000  0.0000  0.0000\n"
        "H  0.7570  0.5860  0.0000\n"
        "H -0.7570  0.5860  0.0000\n"
    )
    rep = sniff_format(f"{base}/mol.xyz")
    assert rep.parsed is True
    assert rep.format == "xyz"
    assert rep.downloaded_bytes > 0


def test_sniff_format_detects_sdf(file_server):
    # SDF/MOL: V2000 connection-table marker + "$$$$" record delimiter (FIX 1).
    from llmxive.librarian.dataset_resolver import sniff_format
    root, base = file_server
    (root / "mol.sdf").write_text(
        "methane\n"
        "  -OEChem-01010000003D\n"
        "\n"
        "  5  4  0     0  0  0  0  0  0999 V2000\n"
        "    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
        "    0.6300    0.6300    0.6300 H   0  0  0  0  0  0  0  0  0  0  0  0\n"
        "M  END\n"
        "$$$$\n"
    )
    rep = sniff_format(f"{base}/mol.sdf")
    assert rep.parsed is True
    assert rep.format == "sdf"
    assert rep.downloaded_bytes > 0


def test_verify_candidate_reachable_csv(file_server):
    from llmxive.librarian.dataset_resolver import verify_candidate
    from llmxive.librarian.dataset_sources import DatasetCandidate
    root, base = file_server
    (root / "d.csv").write_text("x,y\n1,2\n")
    c = DatasetCandidate("D", f"{base}/d.csv", "D", "figshare")
    v = verify_candidate(c)
    assert v is not None and v.format == "csv"


def test_verify_candidate_404_returns_none(file_server):
    from llmxive.librarian.dataset_resolver import verify_candidate
    from llmxive.librarian.dataset_sources import DatasetCandidate
    _root, base = file_server
    c = DatasetCandidate("D", f"{base}/missing.csv", "D", "figshare")
    assert verify_candidate(c) is None


def test_extract_dataset_intents_finds_doi_and_name():
    from llmxive.librarian.dataset_resolver import extract_dataset_intents
    spec = ("## FR\n- **FR-001**: download the QM9 dataset "
            "(DOI: 10.1038/sdata.2014.22) with integrity verification\n")
    intents = extract_dataset_intents(spec)
    assert "10.1038/sdata.2014.22" in intents          # DOI captured
    assert any("qm9" in i.lower() for i in intents)      # named dataset captured


@pytest.mark.skipif(
    not os.environ.get("LLMXIVE_REAL_TESTS"),
    reason="Real network call to zenodo/figshare — set LLMXIVE_REAL_TESTS=1 to run; "
    "gated so the deterministic offline gate is network-free (was flaking on "
    "zenodo read-timeouts).",
)
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


def test_resolve_datasets_candidates_tried_granularity(file_server, monkeypatch):
    """FIX 2: candidates_tried distinguishes unreachable (404) vs wrong_format
    (reachable HTML) vs verified, with precise per-candidate status+reason."""
    import llmxive.librarian.dataset_resolver as dr
    from llmxive.librarian.dataset_sources import DatasetCandidate

    root, base = file_server
    (root / "good.csv").write_text("a,b\n1,2\n3,4\n")
    (root / "page.html").write_text("<html><body>not a dataset</body></html>")

    cands = [
        DatasetCandidate(" DS", f"{base}/missing.csv", "missing", "figshare"),
        DatasetCandidate("DS", f"{base}/page.html", "html page", "zenodo"),
        DatasetCandidate("DS", f"{base}/good.csv", "good", "huggingface"),
    ]
    monkeypatch.setattr(dr, "_gather_candidates", lambda intent: cands)
    # Force the intent extractor to yield exactly one intent.
    monkeypatch.setattr(dr, "extract_dataset_intents", lambda spec: ["DS"])

    result = dr.resolve_datasets(
        "the DS dataset", project_dir=root, repo_root=root, top_n=3,
    )
    tried = result.datasets[0].candidates_tried
    by_status = {t["status"] for t in tried}
    assert "unreachable" in by_status, tried
    assert "wrong_format" in by_status, tried
    assert "verified" in by_status, tried
    # The 404 candidate is recorded as unreachable.
    miss = next(t for t in tried if t["url"].endswith("missing.csv"))
    assert miss["status"] == "unreachable" and miss.get("reason")
    # The reachable-but-HTML candidate is recorded as wrong_format.
    html = next(t for t in tried if t["url"].endswith("page.html"))
    assert html["status"] == "wrong_format" and html.get("reason")
    # The CSV candidate is verified, and verified-selection still works.
    assert result.datasets[0].status == "verified"
    assert result.datasets[0].candidates[0]["url"].endswith("good.csv")


def test_resolve_datasets_is_a_candidate_proposer_no_dead_manifest(file_server, monkeypatch):
    """D7: ``resolve_datasets`` is a candidate PROPOSER only — it returns a
    ``ResolvedDatasets`` for in-process consumption (``render_planner_block``) and
    must NOT persist the dead write-only ``resolved_datasets.yaml`` manifest.

    Guards against re-introducing ``write_manifest`` (removed) or any resolver-side
    manifest write.
    """
    import llmxive.librarian.dataset_resolver as dr
    from llmxive.librarian.dataset_sources import DatasetCandidate

    # ``write_manifest`` is gone entirely.
    assert not hasattr(dr, "write_manifest")

    root, base = file_server
    (root / "good.csv").write_text("a,b\n1,2\n3,4\n")
    monkeypatch.setattr(
        dr, "_gather_candidates",
        lambda intent: [DatasetCandidate("DS", f"{base}/good.csv", "good", "huggingface")],
    )
    monkeypatch.setattr(dr, "extract_dataset_intents", lambda spec: ["DS"])

    proj = root / "projects" / "PROJ-X"
    proj.mkdir(parents=True)
    rd = dr.resolve_datasets("the DS dataset", project_dir=proj, repo_root=root, top_n=3)

    # The return value still drives the planner block (candidate proposer)...
    assert rd.datasets[0].status == "verified"
    assert dr.render_planner_block(rd)
    # ... but NO dead manifest was written to disk.
    assert not (proj / ".specify" / "memory" / "resolved_datasets.yaml").exists()


def test_unresolved_intents_lists(tmp_path):
    from llmxive.librarian.dataset_resolver import (
        ResolvedDatasets,
        ResolvedIntent,
        unresolved_intents,
    )
    rd = ResolvedDatasets(datasets=[
        ResolvedIntent("QM9", "verified", candidates=[{"url": "u"}], candidates_tried=[]),
        ResolvedIntent("BogusSet", "unresolved", candidates=[], candidates_tried=[]),
    ])
    assert unresolved_intents(rd) == ["BogusSet"]


def test_verify_candidate_stores_stable_url_not_redirect_target():
    """Regression (PROJ-262): a URL that redirects to a short-lived target (HF
    resolve URL -> presigned cas-bridge URL with X-Amz-Expires) MUST store the
    STABLE original URL, not the expiring redirect target (which 403s once the
    signature expires). The sniff may use the redirect target; the stored url
    must be the durable one."""
    import http.server
    import socketserver
    import threading

    from llmxive.librarian.dataset_resolver import verify_candidate
    from llmxive.librarian.dataset_sources import DatasetCandidate

    class _H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):  # silence
            pass

        def _route(self):
            if self.path == "/redir":
                self.send_response(302)
                self.send_header("Location", "/data.csv")
                self.end_headers()
            elif self.path == "/data.csv":
                body = b"a,b,c\n1,2,3\n4,5,6\n"
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command == "GET":
                    self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        do_HEAD = _route
        do_GET = _route

    httpd = socketserver.TCPServer(("127.0.0.1", 0), _H)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{port}"
        c = DatasetCandidate("D", f"{base}/redir", "D", "huggingface", hf_id="x/y")
        v = verify_candidate(c)
        assert v is not None, "redirect-to-csv candidate should verify"
        assert v.url == f"{base}/redir", f"stored redirect target, not stable url: {v.url}"
        assert v.format == "csv"
    finally:
        httpd.shutdown()
