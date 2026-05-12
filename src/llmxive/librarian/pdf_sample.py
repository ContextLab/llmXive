"""PDF download + ≥10% summary-grounding sample audit (spec 005 / Q2).

When the librarian returns N verified citations, this module randomly
samples ``ceil(0.10 * N)`` (minimum 1) and re-verifies their summaries
against the actual PDF body text — not just the search-result abstract.

This catches the worst hallucination cases (LLM-generated summary
agrees with the abstract but contradicts the body) at a fraction of
the cost of full-PDF verification on every citation.

Per Constitution Principle III: real PDF downloads, no mocks. Per
Principle V: per-PDF deadline 30s; PDFs >50MB are skipped (with the
citation flagged ``summary_grounded_pdf: None``).
"""

from __future__ import annotations

import dataclasses
import io
import math
import random
import re
from collections.abc import Sequence

import requests

from llmxive.librarian.search import USER_AGENT
from llmxive.librarian.verify import (
    SUMMARY_GROUNDING_THRESHOLD,
    VerifiedCitation,
    jaccard_tokens,
)

PDF_DOWNLOAD_TIMEOUT = 30.0  # seconds
PDF_MAX_BYTES = 50 * 1024 * 1024  # 50MB
PDF_FIRST_N_WORDS = 1000  # extracted text window for grounding


@dataclasses.dataclass(frozen=True)
class PDFSampleResult:
    """Outcome of one PDF audit on a single VerifiedCitation."""

    primary_pointer: str
    summary_grounded_pdf: bool | None  # None = inaccessible; True/False = audited
    pdf_sample_score: float | None
    failure_reason: str | None  # populated when summary_grounded_pdf is None


def select_pdf_sample(
    verified: Sequence[VerifiedCitation],
    *,
    sample_rate: float = 0.10,
    rng: random.Random | None = None,
) -> list[VerifiedCitation]:
    """Random sample at ``sample_rate`` (default 10%) of the verified
    list, with a minimum of 1 citation when len(verified) > 0.
    """
    if not verified:
        return []
    target = max(1, math.ceil(sample_rate * len(verified)))
    rng = rng or random.Random()
    return rng.sample(list(verified), k=min(target, len(verified)))


def audit_pdf_grounding(citation: VerifiedCitation) -> PDFSampleResult:
    """Download the citation's PDF, extract first ~1000 words, and
    re-verify summary grounding. Returns PDFSampleResult.

    Failure modes (each results in summary_grounded_pdf=None):
      - URL doesn't host a PDF
      - HTTP error (404, 403 paywall, 5xx)
      - PDF >50MB (skipped per PDF_MAX_BYTES)
      - Corrupt PDF (pypdf raises)
      - PDF unparseable (no extractable text)
    """
    pdf_url = _pdf_url_for(citation)
    if not pdf_url:
        return PDFSampleResult(
            primary_pointer=citation.primary_pointer,
            summary_grounded_pdf=None,
            pdf_sample_score=None,
            failure_reason="no_pdf_url_inferable",
        )

    pdf_bytes, fail = _download_pdf(pdf_url)
    if fail or pdf_bytes is None:
        return PDFSampleResult(
            primary_pointer=citation.primary_pointer,
            summary_grounded_pdf=None,
            pdf_sample_score=None,
            failure_reason=fail or "download_returned_no_bytes",
        )

    text = _extract_first_n_words(pdf_bytes, n=PDF_FIRST_N_WORDS)
    if not text:
        return PDFSampleResult(
            primary_pointer=citation.primary_pointer,
            summary_grounded_pdf=None,
            pdf_sample_score=None,
            failure_reason="pdf_extraction_yielded_empty_text",
        )

    score = jaccard_tokens(citation.summary, text) if citation.summary else 0.0
    grounded = score >= SUMMARY_GROUNDING_THRESHOLD
    return PDFSampleResult(
        primary_pointer=citation.primary_pointer,
        summary_grounded_pdf=grounded,
        pdf_sample_score=round(score, 4),
        failure_reason=None,
    )


def annotate_with_pdf_sample(
    verified: Sequence[VerifiedCitation],
    sample_results: Sequence[PDFSampleResult],
) -> list[VerifiedCitation]:
    """Return a new list of VerifiedCitations with each citation's
    ``summary_grounded_pdf`` and ``verification_log.pdf_sample_score``
    populated for the sampled subset, and left at default for the rest.

    The sampled subset is identified by primary_pointer matching across
    the two lists.
    """
    by_pointer = {r.primary_pointer: r for r in sample_results}
    out: list[VerifiedCitation] = []
    for v in verified:
        sr = by_pointer.get(v.primary_pointer)
        if sr is None:
            # Not sampled — leave summary_grounded_pdf at False per E3
            # ("False if abstract-only verification passed but not PDF-sampled").
            out.append(
                dataclasses.replace(
                    v,
                    summary_grounded_pdf=False,
                )
            )
            continue
        new_log = dataclasses.replace(
            v.verification_log,
            pdf_sample_score=sr.pdf_sample_score,
        )
        out.append(
            dataclasses.replace(
                v,
                summary_grounded_pdf=sr.summary_grounded_pdf,
                verification_log=new_log,
            )
        )
    return out


# --- helpers --------------------------------------------------------------


_ARXIV_BARE_RE = re.compile(r"^\d{4}\.\d{4,5}$")


def _pdf_url_for(citation: VerifiedCitation) -> str | None:
    """Best-effort guess of the citation's PDF URL.

    arXiv: rewrite ``<id>`` → ``https://arxiv.org/pdf/<id>.pdf``
    DOI: doi.org redirect-follow may land on a PDF, but most publishers
         require login; we only attempt the URL form, which usually 403s
         (correctly classified as ``paywall_partial``).
    Generic URL: try as-is.
    """
    p = citation.primary_pointer
    if _ARXIV_BARE_RE.match(p):
        return f"https://arxiv.org/pdf/{p}.pdf"
    if p.startswith("https://arxiv.org/abs/"):
        arxiv_id = p.removeprefix("https://arxiv.org/abs/")
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    if p.startswith(("http://", "https://")):
        return p
    return None


def _download_pdf(url: str) -> tuple[bytes | None, str | None]:
    """Download (bytes, None) on success, (None, reason) on failure."""
    try:
        r = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/pdf"},
            timeout=PDF_DOWNLOAD_TIMEOUT,
            stream=True,
            allow_redirects=True,
        )
    except (requests.RequestException, OSError) as exc:
        return None, f"network_error: {type(exc).__name__}: {exc}"

    if r.status_code == 401 or r.status_code == 403:
        r.close()
        return None, f"paywall_or_forbidden_{r.status_code}"
    if not r.ok:
        r.close()
        return None, f"http_{r.status_code}"

    # Stream chunks with a hard size cap.
    chunks: list[bytes] = []
    total = 0
    for chunk in r.iter_content(chunk_size=65536):
        chunks.append(chunk)
        total += len(chunk)
        if total > PDF_MAX_BYTES:
            r.close()
            return None, f"pdf_too_large_{total // (1024 * 1024)}mb"
    r.close()
    return b"".join(chunks), None


def _extract_first_n_words(pdf_bytes: bytes, *, n: int = PDF_FIRST_N_WORDS) -> str:
    """Extract the first ``n`` whitespace-delimited words of body text.

    Uses ``pypdf`` (added to deps in spec 005 T003). Catches all extraction
    errors and returns an empty string on failure (caller flags
    ``summary_grounded_pdf=None``).
    """
    try:
        import pypdf
    except ImportError:
        return ""

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception:
        return ""

    out: list[str] = []
    word_count = 0
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            continue
        for word in text.split():
            out.append(word)
            word_count += 1
            if word_count >= n:
                return " ".join(out)
    return " ".join(out)


__all__ = [
    "PDF_DOWNLOAD_TIMEOUT",
    "PDF_FIRST_N_WORDS",
    "PDF_MAX_BYTES",
    "PDFSampleResult",
    "annotate_with_pdf_sample",
    "audit_pdf_grounding",
    "select_pdf_sample",
]
