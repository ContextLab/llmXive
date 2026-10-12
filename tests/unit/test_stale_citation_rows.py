"""A failed citation blocks acceptance only while the document still cites it."""
from datetime import UTC, datetime
from pathlib import Path

from llmxive.agents.advancement import _citations_still_cited, _has_blocking_citations
from llmxive.types import Citation, CitationKind, VerificationStatus

ARTIFACT = "projects/PROJ-9999-totient-canary/specs/001-totient-canary/quickstart.md"
PLACEHOLDER = "https://github.com/your-org/PROJ-9999-totient-canary.git"


def _row(value: str, status: VerificationStatus) -> Citation:
    return Citation(
        cite_id="c-001", artifact_path=ARTIFACT, artifact_hash="1" * 64,
        kind=CitationKind.URL, value=value, verification_status=status,
        verified_against_url=value, verified_at=datetime(2026, 10, 11, 21, 18, tzinfo=UTC),
    )


def _write(root: Path, text: str) -> None:
    path = root / ARTIFACT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_a_failed_citation_still_in_the_document_blocks(tmp_path):
    _write(tmp_path, f"1. Clone it:\n   git clone {PLACEHOLDER}\n")
    for status in (VerificationStatus.MISMATCH, VerificationStatus.UNREACHABLE):
        rows = _citations_still_cited([_row(PLACEHOLDER, status)], repo_root=tmp_path)
        assert _has_blocking_citations(rows)


def test_a_failed_citation_removed_from_the_document_does_not(tmp_path):
    _write(tmp_path, "1. Clone it:\n   git clone \n")
    rows = _citations_still_cited(
        [_row(PLACEHOLDER, VerificationStatus.MISMATCH),
         _row("https://arxiv.org/abs/2105.12850", VerificationStatus.PENDING)],
        repo_root=tmp_path)
    assert [c.value for c in rows] == ["https://arxiv.org/abs/2105.12850"]
    assert not _has_blocking_citations(rows)


def test_a_failed_citation_for_the_document_as_scanned_blocks(tmp_path):
    """The row's hash is the file's: nothing changed since the scan, so the row
    stands even if the scanner recorded the reference in another form."""
    import hashlib

    _write(tmp_path, "See the Fake Paper (example.invalid/fake).\n")
    row = _row("https://example.invalid/fake", VerificationStatus.MISMATCH).model_copy(
        update={"artifact_hash": hashlib.sha256((tmp_path / ARTIFACT).read_bytes()).hexdigest()})
    assert _has_blocking_citations(_citations_still_cited([row], repo_root=tmp_path))


def test_a_failed_citation_whose_document_is_gone_does_not(tmp_path):
    rows = _citations_still_cited([_row(PLACEHOLDER, VerificationStatus.UNREACHABLE)], repo_root=tmp_path)
    assert rows == []
