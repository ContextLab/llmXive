"""
Unit tests for the citation verification step (T047).
The tests ensure that the helper functions behave as expected on a small
controlled fixture. Real HTTP requests are performed only for a known
reachable URL (https://httpbin.org/status/200) and a deliberately
unreachable URL (https://example.invalid/does-not-exist). The latter is
expected to be reported as ``unreachable``.
"""

import pathlib

from code.verify_citations import (
    extract_citations,
    verify_citation,
    write_citation_log,
    verify_all_citations,
)


def test_extract_citations(tmp_path: pathlib.Path):
    # Create a temporary file containing a mixture of URLs
    content = (
        "Here is a good link: https://httpbin.org/status/200\\n"
        "And a bad one: https://example.invalid/does-not-exist\\n"
        "An arXiv reference: arxiv.org/abs/2101.00001\\n"
    )
    file_path = tmp_path / "sample.md"
    file_path.write_text(content, encoding="utf-8")

    citations = extract_citations(file_path)
    assert "https://httpbin.org/status/200" in citations
    assert "https://example.invalid/does-not-exist" in citations
    assert "https://arxiv.org/abs/2101.00001" in citations
    assert len(citations) == 3


def test_verify_citation_reachable():
    result = verify_citation("https://httpbin.org/status/200", timeout=5)
    assert result["status"] == "reachable"
    assert result["http_code"] == 200


def test_verify_citation_unreachable():
    result = verify_citation("https://example.invalid/does-not-exist", timeout=5)
    assert result["status"] == "unreachable"
    assert result["http_code"] is None


def test_write_citation_log(tmp_path: pathlib.Path):
    # Minimal report structure
    report = {
        "https://httpbin.org/status/200": {"url": "https://httpbin.org/status/200", "status": "reachable", "http_code": 200},
        "https://example.invalid/does-not-exist": {
            "url": "https://example.invalid/does-not-exist",
            "status": "unreachable",
            "http_code": None,
        },
    }
    output_file = tmp_path / "citation_log.yaml"
    write_citation_log(report, output_path=output_file)

    # Verify the file exists and contains the expected keys
    assert output_file.is_file()
    loaded = pathlib.Path(output_file).read_text(encoding="utf-8")
    assert "generated_at:" in loaded
    assert "citations:" in loaded
    assert "https://httpbin.org/status/200" in loaded
    assert "unreachable" in loaded


def test_verify_all_citations_integration(tmp_path: pathlib.Path):
    # Create two temporary files with citations
    f1 = tmp_path / "a.md"
    f1.write_text("Link: https://httpbin.org/status/200", encoding="utf-8")
    f2 = tmp_path / "b.md"
    f2.write_text("Bad link: https://example.invalid/does-not-exist", encoding="utf-8")

    report = verify_all_citations(root=tmp_path)
    assert "https://httpbin.org/status/200" in report
    assert "https://example.invalid/does-not-exist" in report
    # The reachable one must be marked as such
    assert report["https://httpbin.org/status/200"]["status"] == "reachable"
    # The bad one must be unreachable
    assert report["https://example.invalid/does-not-exist"]["status"] == "unreachable"