"""An arXiv id does not pin the bytes, so the intake digest is recorded.

``arxiv.org/pdf/<id>`` serves the CURRENT version. Measured 2026-10-10 against
a random sample of 12 of the repository's 226 ingested preprints, **5 now serve
different bytes** than the copy committed at intake (one went from 906,089 to
9,751,359 bytes). Our peer reviews were written against the committed bytes, so
a silent re-download would attach a review to a body it never read.

These tests use real files on disk and patch only the network boundary.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from llmxive.paper_reprocess import preprint_pdf

INTAKE_BYTES = b"%PDF-1.7\nthe body the reviews were written against\n%%EOF\n"
REVISED_BYTES = b"%PDF-1.7\na later version the authors posted\nwith more pages\n%%EOF\n"


def _project(tmp_path, *, record_digest, saved=None):
    pdf_dir = tmp_path / "paper" / "pdf"
    pdf_dir.mkdir(parents=True)
    metadata = {"arxiv_id": "2606.18216", "arxiv_url": "https://arxiv.org/abs/2606.18216"}
    if saved is not None:
        (pdf_dir / "original.pdf").write_bytes(saved)
    if record_digest:
        metadata["committed_pdf_digests"] = {
            "original.pdf": {
                "sha256": hashlib.sha256(INTAKE_BYTES).hexdigest(),
                "bytes": len(INTAKE_BYTES),
            }
        }
    return tmp_path, metadata


def test_record_pdf_digest_reads_the_real_file(tmp_path):
    target = tmp_path / "x.pdf"
    target.write_bytes(INTAKE_BYTES)
    assert preprint_pdf.record_pdf_digest(target) == {
        "sha256": hashlib.sha256(INTAKE_BYTES).hexdigest(),
        "bytes": len(INTAKE_BYTES),
    }


def test_a_saved_original_is_used_without_any_download(tmp_path, monkeypatch):
    pdir, metadata = _project(tmp_path, record_digest=True, saved=INTAKE_BYTES)
    monkeypatch.setattr(
        preprint_pdf, "_download_arxiv_pdf",
        lambda *a, **k: pytest.fail("a saved original must not be re-downloaded"),
    )
    assert preprint_pdf.resolve_original_pdf(pdir, metadata) == pdir / "paper/pdf/original.pdf"


def test_a_matching_redownload_raises_no_flag(tmp_path, monkeypatch):
    pdir, metadata = _project(tmp_path, record_digest=True)

    def _download(_arxiv_id, out_path):
        out_path.write_bytes(INTAKE_BYTES)
        return True

    monkeypatch.setattr(preprint_pdf, "_download_arxiv_pdf", _download)
    got = preprint_pdf.resolve_original_pdf(pdir, metadata)
    assert got is not None and got.read_bytes() == INTAKE_BYTES
    assert not list(got.parent.glob("*version-mismatch.json"))


def test_a_changed_redownload_is_flagged_and_still_returned(tmp_path, monkeypatch):
    """The caller keeps working; the discrepancy becomes discoverable."""
    pdir, metadata = _project(tmp_path, record_digest=True)

    def _download(_arxiv_id, out_path):
        out_path.write_bytes(REVISED_BYTES)
        return True

    monkeypatch.setattr(preprint_pdf, "_download_arxiv_pdf", _download)
    got = preprint_pdf.resolve_original_pdf(pdir, metadata)
    assert got is not None, "control flow is deliberately unchanged"
    marker = got.parent / "original-version-mismatch.json"
    assert marker.is_file(), "a silent version swap is the failure being prevented"
    flagged = json.loads(marker.read_text())
    assert flagged["arxiv_id"] == "2606.18216"
    assert flagged["recorded_at_intake"]["bytes"] == len(INTAKE_BYTES)
    assert flagged["redownloaded"]["bytes"] == len(REVISED_BYTES)
    assert flagged["redownloaded"]["sha256"] == hashlib.sha256(REVISED_BYTES).hexdigest()


def test_a_fresh_intake_has_nothing_to_compare(tmp_path, monkeypatch):
    pdir, metadata = _project(tmp_path, record_digest=False)

    def _download(_arxiv_id, out_path):
        out_path.write_bytes(REVISED_BYTES)
        return True

    monkeypatch.setattr(preprint_pdf, "_download_arxiv_pdf", _download)
    got = preprint_pdf.resolve_original_pdf(pdir, metadata)
    assert got is not None
    assert not list(got.parent.glob("*version-mismatch.json"))


# --- the committed records themselves ------------------------------------

def _repo_metadata():
    from llmxive.config import repo_root

    return sorted(repo_root().glob("projects/*/paper/metadata.json"))


@pytest.mark.skipif(not _repo_metadata(), reason="preprint metadata not checked out")
def test_every_recorded_digest_is_well_formed():
    """A half-written record would be worse than none: it would read as proof."""
    checked = 0
    for meta_file in _repo_metadata():
        record = json.loads(meta_file.read_text(encoding="utf-8")).get("committed_pdf_digests") or {}
        for name, entry in record.items():
            assert name.endswith(".pdf"), (meta_file, name)
            assert isinstance(entry, dict), (meta_file, name)
            assert len(entry["sha256"]) == 64, (meta_file, name)
            assert int(entry["bytes"]) > 0, (meta_file, name)
            checked += 1
    assert checked, "no digests found to verify"
