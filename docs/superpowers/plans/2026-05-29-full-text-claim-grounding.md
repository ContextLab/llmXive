# Full-Text Claim Grounding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify that a cited factual claim is substantiated by the *full text* of the source paper (numbers match, concept conveyed accurately) — flagging unsupported claims `[UNVERIFIED]` so the existing F-18c gate hard-blocks them.

**Architecture:** A standalone `llmxive.grounding` service — OA-first retrieval cascade → passage location → one LLM entailment call → persistent cache — invoked by the existing F-19 `grounding_guard.ground_claim` at the reviser chokepoint. The librarian is untouched; we reuse `pdf_sample._download_pdf`, `verify.resolve_reference`/`_fetch_from_arxiv`, and `librarian.cache` SHA-256 keying.

**Tech Stack:** Python 3.11, `requests`, `pypdf` (PDF text), stdlib `html.parser` (HTML text), Dartmouth `qwen.qwen3.5-122b` backend (entailment), Unpaywall + Semantic Scholar + arXiv HTTP APIs.

**Design spec:** `docs/superpowers/specs/2026-05-29-full-text-claim-grounding-design.md`

**Conventions (read once):**
- Run the offline gate with: `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs` (baseline **1290 passed** with the uncommitted F-19 v1 on disk).
- Real-call tests live in `tests/real_call/` and start with `pytestmark = pytest.mark.skipif(os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call")`.
- Commit with `PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit`; trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- `ruff check .` and `mypy src/llmxive` must stay clean after every task.
- NO mocks of external services. Offline tests use real local fixtures / pure-logic inputs; network behavior is covered by `tests/real_call/`.

**File structure:**
- Create `src/llmxive/grounding/__init__.py` — package exports.
- Create `src/llmxive/grounding/full_text.py` — `RetrievedDoc`, `extract_pdf_text`, `html_to_text`, `retrieve`.
- Create `src/llmxive/grounding/entailment.py` — `Verdict`, `locate_passages`, `assess`.
- Create `src/llmxive/grounding/cache.py` — full-text + verdict caches.
- Create `src/llmxive/grounding/service.py` — `decide`, `ground_cited_claim`.
- Create `agents/prompts/_shared/claim_entailment_block.md` — entailment prompt.
- Modify `src/llmxive/config.py` — `UNPAYWALL_EMAIL`, `grounding_cache_dir()`.
- Modify `src/llmxive/agents/grounding_guard.py` — delegate `ground_claim` to the service.
- Tests as named per task.

---

## Task 1: Config — Unpaywall email + cache dir

**Files:**
- Modify: `src/llmxive/config.py`
- Test: `tests/unit/test_grounding_config.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_grounding_config.py
import os
from pathlib import Path
import llmxive.config as config


def test_unpaywall_email_default():
    assert config.unpaywall_email() == "llmxive@gmail.com"


def test_unpaywall_email_env_override(monkeypatch):
    monkeypatch.setenv("UNPAYWALL_EMAIL", "x@example.org")
    assert config.unpaywall_email() == "x@example.org"


def test_unpaywall_email_blank_is_none(monkeypatch):
    monkeypatch.setenv("UNPAYWALL_EMAIL", "")
    assert config.unpaywall_email() is None  # tier-2 disabled when explicitly blank


def test_grounding_cache_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    d = config.grounding_cache_dir()
    assert d == tmp_path / "state" / "grounding-cache"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_grounding_config.py -q`
Expected: FAIL (`AttributeError: module 'llmxive.config' has no attribute 'unpaywall_email'`)

- [ ] **Step 3: Implement**

Add to `src/llmxive/config.py` (near the other env/path helpers; `repo_root` already exists there):

```python
import os


def unpaywall_email() -> str | None:
    """Contact email for the Unpaywall API (tier-2 OA discovery).

    Defaults to the project mailbox. Returns None when explicitly set blank,
    which disables the Unpaywall retrieval tier (Semantic Scholar OA still runs).
    """
    if "UNPAYWALL_EMAIL" in os.environ:
        return os.environ["UNPAYWALL_EMAIL"] or None
    return "llmxive@gmail.com"


def grounding_cache_dir(repo_root: "Path | None" = None) -> "Path":
    """Directory for the full-text + verdict caches (transient, uncommitted)."""
    root = repo_root if repo_root is not None else globals()["repo_root"]()
    return root / "state" / "grounding-cache"
```

(If `config.py` already imports `Path`/`os`, do not re-import. Use the module's existing `repo_root()` rather than the `globals()` shim if it is defined in-module — match the file's style.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_grounding_config.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/config.py tests/unit/test_grounding_config.py && git commit -m "feat(015): grounding config — UNPAYWALL_EMAIL + grounding_cache_dir"
```

---

## Task 2: `RetrievedDoc` + text extractors (`full_text.py`)

**Files:**
- Create: `src/llmxive/grounding/__init__.py`
- Create: `src/llmxive/grounding/full_text.py`
- Test: `tests/unit/test_grounding_full_text.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_grounding_full_text.py
from llmxive.grounding.full_text import RetrievedDoc, html_to_text, extract_pdf_text


def test_retrieved_doc_readable_flag():
    assert RetrievedDoc(kind="doi", value="10.x/y", tier=None, full_text=None,
                        abstract=None, title=None, final_url="", error="e").readable is False
    assert RetrievedDoc(kind="doi", value="10.x/y", tier="unpaywall",
                        full_text="body", abstract=None, title=None,
                        final_url="u", error=None).readable is True
    assert RetrievedDoc(kind="doi", value="10.x/y", tier="s2", full_text=None,
                        abstract="abs only", title=None, final_url="u",
                        error=None).readable is True


def test_html_to_text_strips_tags_and_scripts():
    html = ("<html><head><title>T</title><style>.x{}</style>"
            "<script>var a=1;</script></head><body><h1>Result</h1>"
            "<p>The correlation was r=0.42 across knots.</p></body></html>")
    text = html_to_text(html, max_chars=10_000)
    assert "r=0.42 across knots" in text
    assert "var a=1" not in text and ".x{}" not in text


def test_extract_pdf_text_caps_length():
    # extract_pdf_text post-processes already-extracted page strings; feed raw text
    from llmxive.grounding.full_text import _normalize_extracted
    big = "word " * 100_000
    out = _normalize_extracted(big, max_chars=1000)
    assert len(out) <= 1000
    assert "  " not in out  # whitespace collapsed
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_grounding_full_text.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'llmxive.grounding'`)

- [ ] **Step 3: Implement**

Create `src/llmxive/grounding/__init__.py`:

```python
"""Full-text claim-grounding service (spec 015 / #239 / F-19 v2)."""
```

Create `src/llmxive/grounding/full_text.py` (extractors + dataclass only in this task; `retrieve` lands in Task 3):

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_grounding_full_text.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/grounding/ tests/unit/test_grounding_full_text.py && git commit -m "feat(015): grounding RetrievedDoc + PDF/HTML text extractors"
```

---

## Task 3: OA-first retrieval cascade (`full_text.py::retrieve`)

**Files:**
- Modify: `src/llmxive/grounding/full_text.py`
- Test: `tests/unit/test_grounding_full_text.py` (add offline parser tests), `tests/real_call/test_grounding_retrieval.py` (create)

- [ ] **Step 1: Write the failing tests**

Offline (parser helpers are pure — test them without network), append to `tests/unit/test_grounding_full_text.py`:

```python
def test_unpaywall_pdf_url_from_payload():
    from llmxive.grounding.full_text import _unpaywall_pdf_url
    payload = {"is_oa": True, "best_oa_location": {
        "url_for_pdf": "https://x/y.pdf", "url": "https://x/landing"}}
    assert _unpaywall_pdf_url(payload) == "https://x/y.pdf"
    assert _unpaywall_pdf_url({"is_oa": False, "best_oa_location": None}) is None


def test_s2_oa_pdf_url_from_payload():
    from llmxive.grounding.full_text import _s2_oa_pdf_url
    assert _s2_oa_pdf_url({"openAccessPdf": {"url": "https://x/z.pdf"}}) == "https://x/z.pdf"
    assert _s2_oa_pdf_url({"openAccessPdf": None}) is None


def test_preprint_pdf_urls_biorxiv():
    from llmxive.grounding.full_text import _preprint_pdf_urls
    urls = _preprint_pdf_urls("doi", "10.1101/2020.09.09.290601")
    assert any("biorxiv.org/content/10.1101/2020.09.09.290601" in u and u.endswith(".full.pdf")
               for u in urls)
    assert any("medrxiv.org/content/" in u for u in urls)
```

Real-call, `tests/real_call/test_grounding_retrieval.py`:

```python
import os
import pytest
from llmxive.grounding.full_text import retrieve

pytestmark = pytest.mark.skipif(os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call")


def test_retrieve_arxiv_full_text():
    doc = retrieve("arxiv", "1706.03762", timeout=60.0)
    assert doc.readable and doc.full_text and len(doc.full_text) > 2000
    assert "attention" in doc.full_text.lower()
    assert doc.tier == "arxiv"


def test_retrieve_oa_doi_via_unpaywall_or_s2():
    # PLOS ONE gold-OA article (verified live 2026-05-29)
    doc = retrieve("doi", "10.1371/journal.pone.0000308", timeout=60.0)
    assert doc.readable and doc.full_text and len(doc.full_text) > 2000
    assert doc.tier in ("unpaywall", "s2", "preprint", "url")


def test_retrieve_fake_doi_unreadable():
    doc = retrieve("doi", "10.5281/zenodo.999999999999", timeout=30.0)
    assert doc.readable is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_grounding_full_text.py -q`
Expected: FAIL (`ImportError: cannot import name '_unpaywall_pdf_url'`)

- [ ] **Step 3: Implement**

Append to `src/llmxive/grounding/full_text.py`:

```python
import logging

import requests  # type: ignore[import-untyped]

from llmxive.config import unpaywall_email
from llmxive.librarian.pdf_sample import _download_pdf
from llmxive.librarian.search import USER_AGENT
from llmxive.librarian.verify import _fetch_from_arxiv, resolve_reference

logger = logging.getLogger(__name__)
_S2_BASE = "https://api.semanticscholar.org/graph/v1/paper"
_UNPAYWALL_BASE = "https://api.unpaywall.org/v2"


def _unpaywall_pdf_url(payload: dict) -> str | None:
    if not isinstance(payload, dict) or not payload.get("is_oa"):
        return None
    loc = payload.get("best_oa_location") or {}
    return loc.get("url_for_pdf") or loc.get("url") or None


def _s2_oa_pdf_url(payload: dict) -> str | None:
    oa = (payload or {}).get("openAccessPdf") or {}
    return oa.get("url") or None


def _preprint_pdf_urls(kind: str, value: str) -> list[str]:
    urls: list[str] = []
    if kind == "doi" and value.startswith("10.1101/"):
        for host in ("www.biorxiv.org", "www.medrxiv.org"):
            urls.append(f"https://{host}/content/{value}v1.full.pdf")
    if kind == "doi" and value.startswith(("10.31234/", "10.31219/")):
        osf_id = value.rsplit("/", 1)[-1]
        urls.append(f"https://osf.io/{osf_id}/download")
    return urls


def _pdf_from_url(url: str, *, timeout: float) -> str:
    data, _err = _download_pdf(url, timeout=timeout)
    return extract_pdf_text(data) if data else ""


def _get_json(url: str, *, timeout: float, headers: dict | None = None) -> dict | None:
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT, **(headers or {})},
                         timeout=timeout)
        if r.status_code != 200:
            return None
        return r.json()
    except (requests.RequestException, ValueError, OSError) as exc:
        logger.warning("grounding retrieve: JSON GET failed %s (%s)", url, exc)
        return None


def retrieve(kind: str, value: str, *, timeout: float = 60.0) -> RetrievedDoc:
    """OA-first cascade. Returns the first tier that yields full text; falls
    back to an abstract-only doc; else an unreadable doc (caller flags)."""
    final_url = ""
    abstract: str | None = None
    title: str | None = None

    # Tier 1: arXiv
    if kind == "arxiv":
        t, a = _fetch_from_arxiv(value)
        title, abstract = t or None, a
        body = _pdf_from_url(f"https://arxiv.org/pdf/{value}", timeout=timeout)
        if body:
            return RetrievedDoc(kind, value, "arxiv", body, abstract, title,
                                f"https://arxiv.org/abs/{value}")

    # Tier 2: Unpaywall (DOI)
    if kind == "doi":
        email = unpaywall_email()
        if email:
            payload = _get_json(f"{_UNPAYWALL_BASE}/{value}?email={email}", timeout=timeout)
            if payload:
                abstract = abstract or payload.get("abstract")
                title = title or payload.get("title")
                pdf_url = _unpaywall_pdf_url(payload)
                if pdf_url:
                    body = _pdf_from_url(pdf_url, timeout=timeout)
                    if body:
                        return RetrievedDoc(kind, value, "unpaywall", body, abstract,
                                            title, pdf_url)

    # Tier 3: Semantic Scholar openAccessPdf (DOI or arXiv)
    s2_id = f"DOI:{value}" if kind == "doi" else (f"ARXIV:{value}" if kind == "arxiv" else None)
    if s2_id:
        from llmxive.config import semantic_scholar_api_key  # existing helper

        key = semantic_scholar_api_key()
        headers = {"x-api-key": key} if key else None
        payload = _get_json(
            f"{_S2_BASE}/{s2_id}?fields=openAccessPdf,abstract,title",
            timeout=timeout, headers=headers,
        )
        if payload:
            abstract = abstract or payload.get("abstract")
            title = title or payload.get("title")
            pdf_url = _s2_oa_pdf_url(payload)
            if pdf_url:
                body = _pdf_from_url(pdf_url, timeout=timeout)
                if body:
                    return RetrievedDoc(kind, value, "s2", body, abstract, title, pdf_url)

    # Tier 4: preprint URL patterns
    for url in _preprint_pdf_urls(kind, value):
        body = _pdf_from_url(url, timeout=timeout)
        if body:
            return RetrievedDoc(kind, value, "preprint", body, abstract, title, url)

    # Tier 5: direct URL fetch (kind == url)
    if kind == "url":
        try:
            r = requests.get(value, headers={"User-Agent": USER_AGENT},
                             timeout=timeout, allow_redirects=True)
            final_url = r.url
            ctype = r.headers.get("content-type", "")
            if "pdf" in ctype.lower():
                body = extract_pdf_text(r.content)
            else:
                body = html_to_text(r.text)
            if body:
                return RetrievedDoc(kind, value, "url", body, abstract, title, final_url)
        except (requests.RequestException, OSError) as exc:
            logger.warning("grounding retrieve: URL fetch failed %s (%s)", value, exc)

    # Abstract-only fallback
    if abstract:
        return RetrievedDoc(kind, value, "abstract", None, abstract, title, final_url)

    # Confirm existence for the error message; unreadable either way.
    try:
        outcome = resolve_reference(kind, value, timeout=timeout)
        err = "resolved but no open-access full text" if outcome.present else "unresolvable"
    except Exception as exc:  # noqa: BLE001 - existence probe is best-effort
        err = f"retrieval failed ({type(exc).__name__})"
    return RetrievedDoc(kind, value, None, None, None, title, final_url, error=err)
```

If `config.semantic_scholar_api_key` does not exist under that exact name, grep `src/llmxive/config.py` for the S2 key accessor and use it; if the key lives only in `credentials.toml`, reuse the librarian's existing loader (`llmxive.librarian.search` constructs `SemanticScholarClient` — follow how it reads the key). Do not read `os.environ` directly for the key.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/test_grounding_full_text.py -q` → Expected: PASS (6 passed).
Run (network): `LLMXIVE_REAL_TESTS=1 python -m pytest tests/real_call/test_grounding_retrieval.py -q` → Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/grounding/full_text.py tests/unit/test_grounding_full_text.py tests/real_call/test_grounding_retrieval.py && git commit -m "feat(015): OA-first full-text retrieval cascade (arXiv/Unpaywall/S2/preprint/URL)"
```

---

## Task 4: Passage location + LLM entailment (`entailment.py`)

**Files:**
- Create: `src/llmxive/grounding/entailment.py`
- Create: `agents/prompts/_shared/claim_entailment_block.md`
- Test: `tests/unit/test_grounding_entailment.py` (create), `tests/real_call/test_grounding_entailment.py` (create)

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_grounding_entailment.py
from llmxive.grounding.entailment import Verdict, locate_passages, _parse_verdict


def test_locate_passages_finds_number_window():
    text = ("Intro paragraph. " * 50 +
            "We found a correlation of r=0.42 between crossing number and braid index. " +
            "Later text. " * 50)
    passages = locate_passages(text, claim="correlation between crossing number and braid index",
                               number="0.42")
    assert any("r=0.42" in p for p in passages)
    assert len(passages) <= 5


def test_locate_passages_no_number_uses_overlap():
    text = "Alpha beta. The braid index predicts complexity strongly. Gamma delta."
    passages = locate_passages(text, claim="braid index predicts complexity", number=None)
    assert any("braid index predicts complexity" in p for p in passages)


def test_parse_verdict_grounded():
    v = _parse_verdict('```yaml\nstatus: grounded\nevidence: "r=0.42 ..."\nnote: ok\n```')
    assert v.status == "grounded" and "0.42" in v.evidence


def test_parse_verdict_contradicted_and_unknown_defaults_not_found():
    assert _parse_verdict("status: contradicted\nevidence: x\nnote: y").status == "contradicted"
    assert _parse_verdict("garbage").status == "not_found"  # unparseable -> not_found
```

```python
# tests/real_call/test_grounding_entailment.py
import os
import pytest
from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.grounding.entailment import assess
from llmxive.grounding.full_text import RetrievedDoc

pytestmark = pytest.mark.skipif(os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call")


def _doc(text):
    return RetrievedDoc("arxiv", "x", "arxiv", text, None, None, "u")


def test_assess_grounded_real_backend():
    doc = _doc("In our experiments the model achieved a BLEU score of 41.8 on WMT 2014 En-De.")
    v = assess("the model achieved a BLEU score of 41.8 on WMT 2014 English-to-German",
               doc, backend=DartmouthBackend(), model="qwen.qwen3.5-122b")
    assert v.status == "grounded"


def test_assess_contradicted_real_backend():
    doc = _doc("In our experiments the model achieved a BLEU score of 41.8 on WMT 2014 En-De.")
    v = assess("the model achieved a BLEU score of 99.9 on WMT 2014 English-to-German",
               doc, backend=DartmouthBackend(), model="qwen.qwen3.5-122b")
    assert v.status in ("contradicted", "not_found")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_grounding_entailment.py -q`
Expected: FAIL (`ModuleNotFoundError: ...entailment`)

- [ ] **Step 3: Implement**

Create `agents/prompts/_shared/claim_entailment_block.md`:

```markdown
You are verifying whether a CLAIM is substantiated by VERBATIM PASSAGES from a
cited source. Judge ONLY from the passages — do not use outside knowledge.

Decide one status:
- `grounded`: the passages state (or unambiguously entail) the claim, INCLUDING any
  specific number/value, which must match (allowing equivalent formatting).
- `contradicted`: the passages assert a different value or the opposite of the claim.
- `not_found`: the passages neither support nor contradict the claim.

Return EXACTLY one fenced YAML document and nothing else:

```yaml
status: grounded | contradicted | not_found
evidence: "<verbatim quote from the passages supporting the status, or empty>"
note: "<one short sentence>"
```
```

Create `src/llmxive/grounding/entailment.py`:

```python
"""Passage location + LLM entailment for full-text claim grounding."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from llmxive.agents.grounding_guard import _number_anchor_re  # reuse number forms
from llmxive.agents.prompts import load_prompt
from llmxive.librarian.verify import jaccard_tokens

logger = logging.getLogger(__name__)

_ENTAILMENT_BLOCK = "agents/prompts/_shared/claim_entailment_block.md"
_REASONING_MAX_TOKENS = 131_072
_DEFAULT_MODEL = "qwen.qwen3.5-122b"
_WINDOW = 320  # chars on each side of an anchor
_MAX_PASSAGES = 5
_SENT_RE = re.compile(r"[^.!?\n]+[.!?]?")

Status = Literal["grounded", "contradicted", "not_found"]


@dataclass(frozen=True, slots=True)
class Verdict:
    status: Status
    evidence: str = ""
    note: str = ""


def locate_passages(full_text: str, *, claim: str, number: str | None) -> list[str]:
    """Return up to _MAX_PASSAGES bounded windows likely to bear on the claim:
    windows around each occurrence of the claim's number, then the
    highest-token-overlap sentences. De-duplicated, order-preserving."""
    text = full_text or ""
    out: list[str] = []

    if number:
        anchor = _number_anchor_re(number)
        if anchor is not None:
            for m in anchor.finditer(text):
                lo, hi = max(0, m.start() - _WINDOW), min(len(text), m.end() + _WINDOW)
                out.append(text[lo:hi].strip())
                if len(out) >= _MAX_PASSAGES:
                    break

    if len(out) < _MAX_PASSAGES:
        sents = [s.strip() for s in _SENT_RE.findall(text) if len(s.strip()) > 20]
        ranked = sorted(sents, key=lambda s: jaccard_tokens(claim, s), reverse=True)
        for s in ranked:
            if jaccard_tokens(claim, s) <= 0.0:
                break
            if not any(s in p for p in out):
                out.append(s)
            if len(out) >= _MAX_PASSAGES:
                break

    # de-dup while preserving order
    seen: set[str] = set()
    deduped = []
    for p in out:
        if p and p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped[:_MAX_PASSAGES]


def _parse_verdict(reply: str) -> Verdict:
    import yaml

    raw = (reply or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        obj = yaml.safe_load(raw)
    except Exception:
        obj = None
    if not isinstance(obj, dict):
        return Verdict("not_found", "", "unparseable verdict")
    status = str(obj.get("status", "")).strip().lower()
    if status not in ("grounded", "contradicted", "not_found"):
        status = "not_found"
    return Verdict(status, str(obj.get("evidence") or ""), str(obj.get("note") or ""))


def _chat_reasoning_safe(backend: Any, messages: list[Any], model: str | None) -> Any:
    kwargs: dict[str, Any] = {"max_tokens": _REASONING_MAX_TOKENS}
    if model is not None:
        kwargs["model"] = model
    try:
        return backend.chat(messages, **kwargs)
    except TypeError:
        kwargs.pop("max_tokens", None)
        try:
            return backend.chat(messages, **kwargs)
        except TypeError:
            return backend.chat(messages)


def assess(claim: str, doc: Any, *, backend: Any, model: str | None,
           repo_root: Path | None = None) -> Verdict:
    """One LLM entailment call over the located passages of the source text.
    On any backend/parse error returns not_found (caller flags — no silent pass)."""
    from llmxive.backends.base import ChatMessage
    from llmxive.config import repo_root as _rr

    source_text = doc.full_text or doc.abstract or ""
    if not source_text.strip():
        return Verdict("not_found", "", "no source text")
    number = _extract_claim_number(claim)
    passages = locate_passages(source_text, claim=claim, number=number)
    if not passages:
        return Verdict("not_found", "", "no relevant passages")
    block = load_prompt(_ENTAILMENT_BLOCK, repo_root=repo_root or _rr())
    joined = "\n\n---\n\n".join(passages)
    messages = [
        ChatMessage(role="system", content=block),
        ChatMessage(role="user",
                    content=f"# CLAIM\n{claim}\n\n# PASSAGES\n{joined}\n\n"
                            "Return the single YAML verdict."),
    ]
    try:
        resp = _chat_reasoning_safe(backend, messages, model or _DEFAULT_MODEL)
        reply = getattr(resp, "text", "") or ""
        if not reply.strip():
            raise ValueError("empty entailment reply")
        return _parse_verdict(reply)
    except Exception as exc:
        logger.warning("grounding assess: entailment failed (%s); -> not_found", exc)
        return Verdict("not_found", "", f"entailment error: {type(exc).__name__}")


_CLAIM_NUM_RE = re.compile(r"[-+]?\d[\d,_ ]*(?:\.\d+)?")


def _extract_claim_number(claim: str) -> str | None:
    m = _CLAIM_NUM_RE.search(claim or "")
    return m.group(0).strip() if m else None
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/test_grounding_entailment.py -q` → Expected: PASS (4 passed).
Run (network): `LLMXIVE_REAL_TESTS=1 python -m pytest tests/real_call/test_grounding_entailment.py -q` → Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/grounding/entailment.py agents/prompts/_shared/claim_entailment_block.md tests/unit/test_grounding_entailment.py tests/real_call/test_grounding_entailment.py && git commit -m "feat(015): passage location + LLM entailment for claim grounding"
```

---

## Task 5: Persistent caches (`cache.py`)

**Files:**
- Create: `src/llmxive/grounding/cache.py`
- Test: `tests/unit/test_grounding_cache.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_grounding_cache.py
from llmxive.grounding import cache


def test_fulltext_roundtrip(tmp_path):
    cache.put_fulltext(tmp_path, "arxiv", "1706.03762",
                       {"tier": "arxiv", "full_text": "body", "abstract": None, "title": "T"})
    got = cache.get_fulltext(tmp_path, "arxiv", "1706.03762")
    assert got["full_text"] == "body" and got["tier"] == "arxiv"
    assert cache.get_fulltext(tmp_path, "arxiv", "nope") is None


def test_verdict_roundtrip_and_key_includes_number(tmp_path):
    cache.put_verdict(tmp_path, source_id="doi:10.x/y", claim="c", number="42",
                      verdict={"status": "grounded", "ok": True, "reason": ""})
    assert cache.get_verdict(tmp_path, source_id="doi:10.x/y", claim="c", number="42")["ok"] is True
    # different number -> different key -> miss
    assert cache.get_verdict(tmp_path, source_id="doi:10.x/y", claim="c", number="43") is None


def test_expired_entry_ignored(tmp_path):
    cache.put_verdict(tmp_path, source_id="s", claim="c", number=None,
                      verdict={"status": "grounded", "ok": True, "reason": ""})
    assert cache.get_verdict(tmp_path, source_id="s", claim="c", number=None,
                             max_age_s=-1) is None  # negative TTL => always expired
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_grounding_cache.py -q`
Expected: FAIL (`ModuleNotFoundError: ...cache`)

- [ ] **Step 3: Implement**

Create `src/llmxive/grounding/cache.py`:

```python
"""Persistent full-text + verdict caches for claim grounding."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from llmxive.config import grounding_cache_dir

_FULLTEXT_TTL_S = 90 * 24 * 3600
_VERDICT_TTL_S = 30 * 24 * 3600


def _dir(repo_root: Path, sub: str) -> Path:
    d = grounding_cache_dir(repo_root) / sub
    d.mkdir(parents=True, exist_ok=True)
    return d


def _key(*parts: str) -> str:
    return hashlib.sha256(" ".join(parts).encode("utf-8")).hexdigest()


def _read(path: Path, *, max_age_s: float) -> dict | None:
    if not path.exists():
        return None
    try:
        rec = json.loads(path.read_text())
    except (ValueError, OSError):
        return None
    if max_age_s >= 0 and (time.time() - rec.get("_ts", 0)) > max_age_s:
        return None
    return rec.get("data")


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps({"_ts": _now(), "data": data}))


def _now() -> float:
    return time.time()


def put_fulltext(repo_root: Path, kind: str, value: str, data: dict[str, Any]) -> None:
    _write(_dir(repo_root, "fulltext") / f"{_key(kind, value)}.json", data)


def get_fulltext(repo_root: Path, kind: str, value: str,
                 *, max_age_s: float = _FULLTEXT_TTL_S) -> dict | None:
    return _read(_dir(repo_root, "fulltext") / f"{_key(kind, value)}.json", max_age_s=max_age_s)


def put_verdict(repo_root: Path, *, source_id: str, claim: str, number: str | None,
                verdict: dict[str, Any]) -> None:
    k = _key(source_id, " ".join(claim.lower().split()), number or "")
    _write(_dir(repo_root, "verdict") / f"{k}.json", verdict)


def get_verdict(repo_root: Path, *, source_id: str, claim: str, number: str | None,
                max_age_s: float = _VERDICT_TTL_S) -> dict | None:
    k = _key(source_id, " ".join(claim.lower().split()), number or "")
    return _read(_dir(repo_root, "verdict") / f"{k}.json", max_age_s=max_age_s)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_grounding_cache.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/grounding/cache.py tests/unit/test_grounding_cache.py && git commit -m "feat(015): persistent full-text + verdict caches for grounding"
```

---

## Task 6: Service orchestrator (`service.py`)

**Files:**
- Create: `src/llmxive/grounding/service.py`
- Test: `tests/unit/test_grounding_service.py` (create)

- [ ] **Step 1: Write the failing test (pure policy `decide`)**

```python
# tests/unit/test_grounding_service.py
from llmxive.grounding.service import decide
from llmxive.grounding.entailment import Verdict
from llmxive.grounding.full_text import RetrievedDoc


def _doc(full=None, abstract=None, tier="s2"):
    return RetrievedDoc("doi", "10.x/y", tier, full, abstract, None, "u")


def test_decide_grounded_full_text_ok():
    ok, reason = decide(_doc(full="body"), Verdict("grounded"))
    assert ok is True


def test_decide_contradicted_flags():
    ok, reason = decide(_doc(full="body"), Verdict("contradicted", note="says 9988"))
    assert ok is False and "contradict" in reason.lower()


def test_decide_not_found_full_text_flags():
    ok, reason = decide(_doc(full="body"), Verdict("not_found"))
    assert ok is False


def test_decide_abstract_only_grounded_ok():
    ok, reason = decide(_doc(abstract="abs", tier="abstract"), Verdict("grounded"))
    assert ok is True


def test_decide_abstract_only_not_found_flags():
    ok, reason = decide(_doc(abstract="abs", tier="abstract"), Verdict("not_found"))
    assert ok is False and "abstract" in reason.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_grounding_service.py -q`
Expected: FAIL (`ModuleNotFoundError: ...service`)

- [ ] **Step 3: Implement**

Create `src/llmxive/grounding/service.py`:

```python
"""Orchestrator: cache -> classify -> resolve -> retrieve -> assess -> decide."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from llmxive.agents.grounding_guard import CitedClaim, GroundingVerdict
from llmxive.grounding import cache
from llmxive.grounding.entailment import Verdict, assess
from llmxive.grounding.full_text import RetrievedDoc, retrieve

logger = logging.getLogger(__name__)


def decide(doc: RetrievedDoc, verdict: Verdict) -> tuple[bool, str]:
    """Apply the maintainer-confirmed policy to a retrieval + entailment result."""
    if verdict.status == "grounded":
        return True, ""
    if verdict.status == "contradicted":
        return False, f"cited source contradicts the claim ({verdict.note or verdict.evidence})"[:300]
    # not_found
    if doc.full_text:
        return False, "claim not found in the cited source's full text"
    return False, "claim not found in the cited source's abstract (full text unavailable)"


def ground_cited_claim(claim: CitedClaim, *, backend: Any, model: str | None,
                       repo_root: Path) -> GroundingVerdict:
    """Full-text grounding of one source-attributed claim."""
    kind, value = claim.source_kind, claim.source_value
    if kind is None or value is None:
        return GroundingVerdict(
            claim=claim, ok=False,
            reason="cited source is free-text only (no resolvable DOI/arXiv/URL); cannot substantiate",
        )
    source_id = f"{kind.value}:{value}"

    cached = cache.get_verdict(repo_root, source_id=source_id, claim=claim.claim_text,
                               number=claim.number)
    if cached is not None:
        return GroundingVerdict(claim=claim, ok=bool(cached["ok"]), reason=cached.get("reason", ""))

    ft = cache.get_fulltext(repo_root, kind.value, value)
    if ft is not None:
        doc = RetrievedDoc(kind.value, value, ft.get("tier"), ft.get("full_text"),
                           ft.get("abstract"), ft.get("title"), ft.get("final_url", ""))
    else:
        doc = retrieve(kind.value, value)
        cache.put_fulltext(repo_root, kind.value, value, {
            "tier": doc.tier, "full_text": doc.full_text, "abstract": doc.abstract,
            "title": doc.title, "final_url": doc.final_url})

    if not doc.readable:
        verdict_obj = GroundingVerdict(
            claim=claim, ok=False,
            reason=f"cited source unreadable ({doc.error or 'no open-access text'}); cannot substantiate",
        )
        cache.put_verdict(repo_root, source_id=source_id, claim=claim.claim_text,
                          number=claim.number,
                          verdict={"status": "not_found", "ok": False, "reason": verdict_obj.reason})
        return verdict_obj

    verdict = assess(claim.claim_text, doc, backend=backend, model=model, repo_root=repo_root)
    ok, reason = decide(doc, verdict)
    cache.put_verdict(repo_root, source_id=source_id, claim=claim.claim_text,
                      number=claim.number,
                      verdict={"status": verdict.status, "ok": ok, "reason": reason})
    return GroundingVerdict(claim=claim, ok=ok, reason=reason)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_grounding_service.py -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/grounding/service.py tests/unit/test_grounding_service.py && git commit -m "feat(015): grounding service orchestrator + policy decide()"
```

---

## Task 7: Wire the service into the F-19 guard

**Files:**
- Modify: `src/llmxive/agents/grounding_guard.py` (`ground_claim` body + `__all__` unchanged)
- Test: `tests/unit/test_grounding_guard.py` (existing — keep green), `tests/real_call/test_grounding_guard_flags_fabrication.py` (existing — keep green)

- [ ] **Step 1: Write the failing test (delegation)**

Append to `tests/unit/test_grounding_guard.py`:

```python
def test_ground_claim_delegates_to_service(monkeypatch):
    import llmxive.agents.grounding_guard as gg
    from llmxive.agents.grounding_guard import CitedClaim, GroundingVerdict
    from llmxive.types import CitationKind

    captured = {}

    def fake_service(claim, *, backend, model, repo_root):
        captured["called"] = True
        return GroundingVerdict(claim=claim, ok=False, reason="from-service")

    monkeypatch.setattr(gg, "_service_ground", fake_service)
    c = CitedClaim(claim_text="x", number="1", source_str="arXiv:1706.03762",
                   source_kind=CitationKind.ARXIV, source_value="1706.03762")
    v = gg.ground_claim(c, backend=object(), model=None, repo_root=__import__("pathlib").Path("."))
    assert captured.get("called") and v.reason == "from-service"


def test_ground_claim_free_text_still_flags_without_service():
    from llmxive.agents.grounding_guard import CitedClaim, ground_claim
    c = CitedClaim(claim_text="x", number="1", source_str="Kauffman 2004",
                   source_kind=None, source_value=None)
    v = ground_claim(c, backend=object(), model=None, repo_root=__import__("pathlib").Path("."))
    assert v.ok is False and "free-text" in v.reason
```

Note: this requires `ground_claim` to gain `backend`, `model`, `repo_root` params and to call a module-level `_service_ground` seam. The callers in `_self_consistency.py` already have backend/model/repo_root in scope (Task 7 Step 3 updates the call site).

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_grounding_guard.py -q`
Expected: FAIL (`TypeError: ground_claim() got an unexpected keyword argument 'backend'`)

- [ ] **Step 3: Implement**

In `src/llmxive/agents/grounding_guard.py`:

1. Add a lazy import seam near the top of the module body (not at import time, to avoid a circular import with `grounding.service`, which imports `grounding_guard`):

```python
def _service_ground(claim: "CitedClaim", *, backend: Any, model: str | None, repo_root: Path) -> "GroundingVerdict":
    from llmxive.grounding.service import ground_cited_claim
    return ground_cited_claim(claim, backend=backend, model=model, repo_root=repo_root)
```

2. Replace the body of `ground_claim` so it keeps the free-text short-circuit but delegates the network/grounding to the service:

```python
def ground_claim(claim: CitedClaim, *, backend: Any, model: str | None,
                 repo_root: Path, timeout: float = 30.0) -> GroundingVerdict:
    """Verify the cited source SUBSTANTIATES the claim via the full-text service.
    Free-text-only sources short-circuit to a flag (no resolvable id to fetch)."""
    if claim.source_kind is None or claim.source_value is None:
        return GroundingVerdict(
            claim=claim, ok=False,
            reason="cited source is free-text only (no resolvable DOI/arXiv/URL); cannot substantiate this claim/number",
        )
    return _service_ground(claim, backend=backend, model=model, repo_root=repo_root)
```

3. Delete the now-unused `_fetch_source_text` and the old abstract-only grounding body in `grounding_guard.py` (the service owns retrieval now). Keep `CitedClaim`, `GroundingVerdict`, `classify_source`, `number_appears_in`, `extract_cited_claims`, `apply_grounding_verdicts`, `verify_grounding_and_clean`, `_number_anchor_re`, and `__all__`.

4. Update `verify_grounding_and_clean` to thread `repo_root` into `ground_claim` (it already receives `repo_root`); ensure the call is `ground_claim(c, backend=backend, model=model, repo_root=repo_root)`.

5. Update the call site in `src/llmxive/convergence/revisers/_self_consistency.py::_ground_factual_claims` to pass `repo_root` through to `verify_grounding_and_clean` (grep for the existing call; it already has `repo_root` in scope from `run_with_self_consistency`).

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/test_grounding_guard.py -q` → Expected: PASS (existing + 2 new).
Run: `python -m pytest tests/unit/test_grounding_entailment.py tests/unit/test_grounding_service.py tests/unit/test_grounding_full_text.py tests/unit/test_grounding_cache.py -q` → Expected: PASS.

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/agents/grounding_guard.py src/llmxive/convergence/revisers/_self_consistency.py tests/unit/test_grounding_guard.py && git commit -m "feat(015): delegate F-19 ground_claim to the full-text grounding service"
```

---

## Task 8: End-to-end real-call proof + final gates

**Files:**
- Create: `tests/real_call/test_grounding_end_to_end.py`
- Test: full offline gate + ruff + mypy

- [ ] **Step 1: Write the real-call e2e test**

```python
# tests/real_call/test_grounding_end_to_end.py
import os
import pytest
from pathlib import Path
from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.agents.grounding_guard import verify_grounding_and_clean

pytestmark = pytest.mark.skipif(os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call")


def test_fabricated_number_on_real_paper_is_flagged(tmp_path):
    # Attention Is All You Need reports BLEU 41.8 (En-De); claim a fabricated 99.9.
    doc = ("The proposed model achieves a BLEU score of 99.9 on the WMT 2014 "
           "English-to-German task (arXiv:1706.03762).")
    cleaned, report = verify_grounding_and_clean(
        doc, backend=DartmouthBackend(), model="qwen.qwen3.5-122b", repo_root=tmp_path)
    assert "[UNVERIFIED:" in cleaned and report.flagged_count >= 1


def test_real_number_on_real_paper_passes(tmp_path):
    doc = ("The proposed model achieves a BLEU score of 41.8 on the WMT 2014 "
           "English-to-German task (arXiv:1706.03762).")
    cleaned, report = verify_grounding_and_clean(
        doc, backend=DartmouthBackend(), model="qwen.qwen3.5-122b", repo_root=tmp_path)
    assert "[UNVERIFIED:" not in cleaned
```

- [ ] **Step 2: Run the e2e test**

Run: `LLMXIVE_REAL_TESTS=1 python -m pytest tests/real_call/test_grounding_end_to_end.py -q`
Expected: PASS (2 passed). If the extractor model phrases the claim without a parseable number, inspect and fix the extraction prompt/`_extract_claim_number` — do NOT weaken the assertion.

- [ ] **Step 3: Full offline gate**

Run: `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs`
Expected: PASS — at least the prior **1290** plus all new offline unit tests (config 4, full_text 6, entailment 4, cache 3, service 5, guard +2).

- [ ] **Step 4: Lint + types**

Run: `ruff check .` → Expected: `All checks passed!`
Run: `mypy src/llmxive` → Expected: `Success: no issues found`.
Fix any findings, then re-run Step 3 (re-run the whole gate after any change).

- [ ] **Step 5: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add tests/real_call/test_grounding_end_to_end.py && git commit -m "test(015): end-to-end full-text grounding real-call proof"
```

---

## Task 9: Update tracker note

**Files:**
- Modify: `notes/spec-015-review-status.md`

- [ ] **Step 1: Append an F-19 v2 entry** to the findings log summarizing: the full-text grounding service (retrieval cascade tiers, hybrid entailment, cache), that it replaces F-19 v1's abstract-only/arXiv-only grounding, the offline + real-call test deltas, and that `[UNVERIFIED]` markers from grounding hard-block via the existing F-18c gates. Note the guard stays env-gated (`LLMXIVE_GROUNDING_GUARD`, on in `cli.run`).

- [ ] **Step 2: Commit**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add notes/spec-015-review-status.md && git commit -m "docs(015): tracker — full-text claim grounding (F-19 v2) landed"
```

---

## Self-Review notes (author)

- **Spec coverage:** §3 modules → Tasks 2–7; §4 cascade → Task 3; §5 hybrid entailment → Task 4 + decide() Task 6; §6 cache → Task 5; §7 wiring/config/no-silent-pass → Tasks 1,6,7; §8 testing → every task + Task 8. Covered.
- **Known integration risks to verify during execution (not placeholders — checks):** (a) the Semantic Scholar API-key accessor name in `config.py` (Task 3 Step 3 says grep + reuse; do not read env directly); (b) the exact current signature of `_self_consistency._ground_factual_claims`/`verify_grounding_and_clean` (Task 7 Step 3 — thread `repo_root`); (c) `pdf_sample._download_pdf` return tuple shape `(bytes|None, err|None)` (Task 3 `_pdf_from_url`). Each is a one-line grep before writing the step's code.
- **Type consistency:** `RetrievedDoc`, `Verdict`, `GroundingVerdict`, `CitedClaim` field/attr names are used identically across Tasks 2–7.
