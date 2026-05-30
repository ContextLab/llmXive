"""Open-access full-text retrieval + text extraction for claim grounding."""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from html.parser import HTMLParser

_WS_RE = re.compile(r"[ \t]+")
_NL_RE = re.compile(r"\n{3,}")


@dataclass(frozen=True, slots=True)
class RetrievedDoc:
    kind: str
    value: str
    tier: str | None
    full_text: str | None
    abstract: str | None
    title: str | None
    final_url: str
    error: str | None = None

    @property
    def readable(self) -> bool:
        return bool(self.full_text or self.abstract)


def _normalize_extracted(text: str, *, max_chars: int) -> str:
    """Collapse runs of spaces/blank lines and hard-cap length."""
    t = _WS_RE.sub(" ", text or "")
    t = _NL_RE.sub("\n\n", t)
    t = "\n".join(line.strip() for line in t.splitlines())
    t = t.strip()
    return t[:max_chars]


def extract_pdf_text(pdf_bytes: bytes, *, max_chars: int = 200_000) -> str:
    """Extract all page text from PDF bytes via pypdf. Returns '' on failure."""
    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        parts: list[str] = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
            if sum(len(p) for p in parts) > max_chars:
                break
        return _normalize_extracted("\n".join(parts), max_chars=max_chars)
    except Exception:
        return ""


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.chunks.append(data)


def html_to_text(html: str, *, max_chars: int = 200_000) -> str:
    """Strip tags/scripts/styles from HTML, returning readable text."""
    p = _TextExtractor()
    try:
        p.feed(html or "")
    except Exception:
        pass
    return _normalize_extracted(" ".join(p.chunks), max_chars=max_chars)
