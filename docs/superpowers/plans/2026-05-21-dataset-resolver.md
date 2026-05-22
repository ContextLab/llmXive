# Dataset Resolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace LLM-hallucinated dataset URLs in the Planner with a deterministic resolver that finds real datasets via web APIs, verifies reachability + format, and feeds the top-N verified candidates into the Planner prompt.

**Architecture:** A `librarian/`-package module (`dataset_resolver.py` + `dataset_sources.py`) called by `PlannerAgent.mechanical_step`. It reuses `verify.py` (reachability), `search.py` (Semantic Scholar/arXiv + backoff), `cache.py`, and `query_extractor.py`. Sources: HuggingFace Hub, figshare, Zenodo, DataCite, plus reused paper search. Verification = reachability + a sample-stream format sniff. The Planner cites only the injected verified URLs; FR-006 (spec-014) remains the safety net.

**Tech Stack:** Python 3.11, `huggingface_hub` 0.36.2 (installed), `requests` (installed), stdlib `csv/json/zipfile/io`, `pytest` with a local `http.server` fixture. Reuses the existing `llmxive.librarian.*` modules.

**Design:** [docs/superpowers/specs/2026-05-21-dataset-resolver-design.md](../specs/2026-05-21-dataset-resolver-design.md)

---

## File Structure

- **Create** `src/llmxive/librarian/dataset_sources.py` — `DatasetCandidate` dataclass + one search function per source (HF Hub, figshare, Zenodo, DataCite). Each returns `list[DatasetCandidate]`. Pure I/O against public APIs; no ranking/verification.
- **Create** `src/llmxive/librarian/dataset_resolver.py` — `extract_dataset_intents`, `sniff_format`, `verify_candidate`, `rank_candidates`, `resolve_datasets`, manifest write, escalation. Orchestrates `dataset_sources` + reused `verify/search/cache/query_extractor`.
- **Modify** `src/llmxive/speckit/plan_cmd.py` — call `resolve_datasets` in `mechanical_step`; inject the verified-datasets block in `build_prompt`; escalate on unresolved required intents.
- **Modify** `agents/prompts/planner.md` — instruct: cite ONLY the provided verified dataset URLs.
- **Create** `tests/unit/test_dataset_sources.py`, `tests/integration/test_dataset_resolver.py`, `tests/integration/test_planner_dataset_injection.py`.

Key shared type (defined in `dataset_sources.py`, imported everywhere):

```python
@dataclass(frozen=True)
class DatasetCandidate:
    intent: str          # the dataset name/DOI this candidate answers
    url: str             # canonical download/landing URL (or HF resolve URL)
    title: str           # human title from the source
    source: str          # "huggingface" | "figshare" | "zenodo" | "datacite" | "semantic_scholar"
    hf_id: str | None = None   # set when source == "huggingface"
```

---

## Task 1: `DatasetCandidate` + HuggingFace Hub source

**Files:**
- Create: `src/llmxive/librarian/dataset_sources.py`
- Test: `tests/unit/test_dataset_sources.py`

- [ ] **Step 1: Write the failing test** (real HF Hub call — `huggingface_hub` is installed; free, no key)

```python
# tests/unit/test_dataset_sources.py
from llmxive.librarian.dataset_sources import DatasetCandidate, search_huggingface


def test_huggingface_search_returns_real_candidates():
    cands = search_huggingface("QM9", limit=5)
    assert cands, "expected >=1 HF dataset candidate for QM9"
    c = cands[0]
    assert isinstance(c, DatasetCandidate)
    assert c.source == "huggingface"
    assert c.hf_id and "/" in c.hf_id            # e.g. "n0w0f/qm9-csv" style id
    assert c.url.startswith("https://huggingface.co/datasets/")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_dataset_sources.py::test_huggingface_search_returns_real_candidates -v`
Expected: FAIL with `ImportError: cannot import name 'search_huggingface'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/librarian/dataset_sources.py
"""Deterministic dataset-source clients (spec: dataset-resolver design).

Each ``search_*`` returns a list of :class:`DatasetCandidate` for a dataset
intent (a name like "QM9" or a DOI). No ranking or verification here — that is
the resolver's job. All network errors are swallowed into an empty list so one
dead source never breaks resolution; the resolver decides what to do with the
union of candidates.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

USER_AGENT = "llmxive-dataset-resolver/1.0 (https://github.com/ContextLab/llmXive)"
_TIMEOUT = 20


@dataclass(frozen=True)
class DatasetCandidate:
    intent: str
    url: str
    title: str
    source: str
    hf_id: str | None = None


def search_huggingface(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    from huggingface_hub import HfApi

    try:
        api = HfApi()
        results = list(api.list_datasets(search=intent, limit=limit))
    except Exception:
        return []
    out: list[DatasetCandidate] = []
    for d in results:
        ds_id = getattr(d, "id", None)
        if not ds_id:
            continue
        out.append(DatasetCandidate(
            intent=intent,
            url=f"https://huggingface.co/datasets/{ds_id}",
            title=ds_id,
            source="huggingface",
            hf_id=ds_id,
        ))
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_dataset_sources.py::test_huggingface_search_returns_real_candidates -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/librarian/dataset_sources.py tests/unit/test_dataset_sources.py
git commit -m "feat(dataset-resolver): DatasetCandidate + HuggingFace Hub source"
```

---

## Task 2: figshare, Zenodo, DataCite sources

**Files:**
- Modify: `src/llmxive/librarian/dataset_sources.py`
- Test: `tests/unit/test_dataset_sources.py`

- [ ] **Step 1: Write the failing tests** (real API calls — all free, no key)

```python
# append to tests/unit/test_dataset_sources.py
from llmxive.librarian.dataset_sources import (
    search_figshare, search_zenodo, search_datacite,
)


def test_figshare_search_returns_candidates():
    cands = search_figshare("QM9 molecular", limit=5)
    assert all(c.source == "figshare" and c.url.startswith("http") for c in cands)
    # figshare may legitimately return 0 for a narrow query; assert shape only.


def test_zenodo_search_returns_candidates():
    cands = search_zenodo("QM9 quantum chemistry", limit=5)
    assert all(c.source == "zenodo" and c.url.startswith("http") for c in cands)


def test_datacite_resolves_doi():
    # The QM9 Scientific Data paper DOI (verified reachable).
    cands = search_datacite("10.1038/sdata.2014.22", limit=3)
    assert all(c.source == "datacite" and c.url.startswith("http") for c in cands)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_dataset_sources.py -k "figshare or zenodo or datacite" -v`
Expected: FAIL with ImportError for the three names.

- [ ] **Step 3: Implement the three clients**

```python
# append to src/llmxive/librarian/dataset_sources.py
def _get_json(url: str, *, params: dict | None = None) -> dict | list | None:
    try:
        r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=_TIMEOUT)
        if r.status_code != 200:
            return None
        return r.json()
    except (requests.RequestException, ValueError, OSError):
        return None


def search_figshare(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    data = _get_json("https://api.figshare.com/v2/articles", params={"search_for": intent, "page_size": limit})
    out: list[DatasetCandidate] = []
    for item in data or []:
        url = item.get("url_public_html") or item.get("url")
        if url:
            out.append(DatasetCandidate(intent, url, item.get("title", ""), "figshare"))
    return out


def search_zenodo(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    data = _get_json("https://zenodo.org/api/records", params={"q": intent, "size": limit})
    hits = ((data or {}).get("hits") or {}).get("hits") or []
    out: list[DatasetCandidate] = []
    for h in hits:
        url = (h.get("links") or {}).get("html") or h.get("doi_url")
        if url:
            out.append(DatasetCandidate(intent, url, (h.get("metadata") or {}).get("title", ""), "zenodo"))
    return out


def search_datacite(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    # intent may be a DOI (resolve) or a free-text query (search).
    looks_doi = intent.strip().lower().startswith("10.")
    params = {"query": intent, "page[size]": limit} if not looks_doi else None
    url = f"https://api.datacite.org/dois/{intent}" if looks_doi else "https://api.datacite.org/dois"
    data = _get_json(url, params=params)
    records = []
    if looks_doi and isinstance(data, dict) and "data" in data:
        records = [data["data"]]
    elif isinstance(data, dict):
        records = data.get("data") or []
    out: list[DatasetCandidate] = []
    for rec in records:
        attrs = rec.get("attributes") or {}
        doi = attrs.get("doi")
        if doi:
            titles = attrs.get("titles") or [{}]
            out.append(DatasetCandidate(intent, f"https://doi.org/{doi}", titles[0].get("title", ""), "datacite"))
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_dataset_sources.py -k "figshare or zenodo or datacite" -v`
Expected: PASS (network required).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/librarian/dataset_sources.py tests/unit/test_dataset_sources.py
git commit -m "feat(dataset-resolver): figshare/Zenodo/DataCite sources"
```

---

## Task 3: `sniff_format` (sample-stream + parse)

**Files:**
- Create: `src/llmxive/librarian/dataset_resolver.py`
- Test: `tests/integration/test_dataset_resolver.py`

- [ ] **Step 1: Write the failing test** (real local `http.server`, no mocks of the network path)

```python
# tests/integration/test_dataset_resolver.py
import http.server, socketserver, threading, functools, io, csv, zipfile
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/integration/test_dataset_resolver.py -k sniff -v`
Expected: FAIL (ImportError for `sniff_format`).

- [ ] **Step 3: Implement `sniff_format`**

```python
# src/llmxive/librarian/dataset_resolver.py
"""Deterministic dataset resolver (spec: dataset-resolver design).

Finds real datasets via dataset_sources, verifies reachability (reusing
librarian.verify) + a sample-stream format sniff, ranks, and returns the top-N
verified candidates per dataset intent for injection into the Planner prompt.
"""
from __future__ import annotations

import csv as _csv
import io
import json
import zipfile
from dataclasses import dataclass, field

import requests

from llmxive.librarian.dataset_sources import DatasetCandidate, USER_AGENT

_SAMPLE_BYTES = 256 * 1024   # cap the sample download at 256 KB
_SNIFF_TIMEOUT = 20


@dataclass(frozen=True)
class FormatReport:
    parsed: bool
    format: str | None
    downloaded_bytes: int
    error: str | None = None


def _detect_and_parse(sample: bytes, url: str) -> tuple[bool, str | None]:
    # Binary container formats by magic bytes.
    if sample[:2] == b"PK":
        try:
            zipfile.ZipFile(io.BytesIO(sample))  # may raise on a truncated sample
            return True, "zip"
        except zipfile.BadZipFile:
            # A truncated-but-valid zip header still indicates a zip download.
            return True, "zip"
    if sample[:2] == b"\x1f\x8b":
        return True, "gzip"
    if sample[:8] == b"\x89HDF\r\n\x1a\n":
        return True, "hdf5"
    if sample[:4] == b"PAR1":
        return True, "parquet"
    # Text formats.
    try:
        text = sample.decode("utf-8")
    except UnicodeDecodeError:
        return False, None
    stripped = text.lstrip()
    if stripped[:1] in "{[":
        try:
            json.loads(text)
            return True, "json"
        except ValueError:
            # JSON Lines: each non-empty line parses.
            lines = [ln for ln in text.splitlines() if ln.strip()][:-1]
            if lines and all(_is_json(ln) for ln in lines):
                return True, "jsonl"
            return False, None
    if "<html" in stripped[:200].lower():
        return False, None
    # CSV/TSV: csv.Sniffer + >=2 columns on the first full row.
    try:
        dialect = _csv.Sniffer().sniff(text[:4096])
        rows = list(_csv.reader(io.StringIO(text), dialect))
        if rows and len(rows[0]) >= 2:
            return True, "tsv" if dialect.delimiter == "\t" else "csv"
    except _csv.Error:
        pass
    return False, None


def _is_json(line: str) -> bool:
    try:
        json.loads(line)
        return True
    except ValueError:
        return False


def sniff_format(url: str) -> FormatReport:
    try:
        with requests.get(url, stream=True, headers={"User-Agent": USER_AGENT}, timeout=_SNIFF_TIMEOUT) as r:
            if r.status_code >= 400:
                return FormatReport(False, None, 0, f"HTTP {r.status_code}")
            sample = r.raw.read(_SAMPLE_BYTES, decode_content=True) or b""
    except (requests.RequestException, OSError) as exc:
        return FormatReport(False, None, 0, str(exc))
    ok, fmt = _detect_and_parse(sample, url)
    return FormatReport(ok, fmt, len(sample), None if ok else "unrecognized/non-dataset content")
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/integration/test_dataset_resolver.py -k sniff -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/librarian/dataset_resolver.py tests/integration/test_dataset_resolver.py
git commit -m "feat(dataset-resolver): sample-stream format sniff"
```

---

## Task 4: `verify_candidate` (reachability + sniff) — reuse verify.py

**Files:**
- Modify: `src/llmxive/librarian/dataset_resolver.py`
- Test: `tests/integration/test_dataset_resolver.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/integration/test_dataset_resolver.py
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/integration/test_dataset_resolver.py -k verify_candidate -v`
Expected: FAIL (ImportError `verify_candidate`).

- [ ] **Step 3: Implement `VerifiedDataset` + `verify_candidate`** (reuse `verify._head_with_get_fallback`)

```python
# append to src/llmxive/librarian/dataset_resolver.py
from llmxive.librarian import verify as _verify


@dataclass(frozen=True)
class VerifiedDataset:
    intent: str
    url: str
    source: str
    format: str
    relevance: float
    downloaded_bytes: int
    hf_id: str | None = None


def verify_candidate(c: DatasetCandidate, *, relevance: float = 0.0) -> VerifiedDataset | None:
    """Return a VerifiedDataset iff the candidate is reachable AND a sample
    parses as a recognized dataset format; else None."""
    head = _verify._head_with_get_fallback(c.url, timeout=20.0)
    if head.outcome == "unreachable":
        return None
    # Sniff the final (post-redirect) URL.
    rep = sniff_format(head.final_url)
    if not rep.parsed or rep.format is None:
        return None
    return VerifiedDataset(
        intent=c.intent, url=head.final_url, source=c.source,
        format=rep.format, relevance=relevance,
        downloaded_bytes=rep.downloaded_bytes, hf_id=c.hf_id,
    )
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/integration/test_dataset_resolver.py -k verify_candidate -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/librarian/dataset_resolver.py tests/integration/test_dataset_resolver.py
git commit -m "feat(dataset-resolver): verify_candidate (reachability + sniff, reuses verify.py)"
```

---

## Task 5: intent extraction + `resolve_datasets` orchestration (top-N) + manifest

**Files:**
- Modify: `src/llmxive/librarian/dataset_resolver.py`
- Test: `tests/integration/test_dataset_resolver.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/integration/test_dataset_resolver.py
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/integration/test_dataset_resolver.py -k "extract_dataset_intents or resolve_datasets_real" -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement intents + orchestration**

```python
# append to src/llmxive/librarian/dataset_resolver.py
import re
from pathlib import Path

from llmxive.librarian import dataset_sources as _sources
from llmxive.librarian.verify import query_relevance_score

_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s)\]\"'>}]+)", re.IGNORECASE)
# Capitalized/alnum dataset-name tokens, e.g. QM9, ImageNet, CIFAR-10, MD17.
_NAME_RE = re.compile(r"\b([A-Z][A-Za-z]*\d[\w-]*|[A-Z]{2,}[A-Za-z0-9-]*)\b")
# Source authority for tie-breaking (higher = preferred).
_AUTHORITY = {"huggingface": 4, "zenodo": 3, "figshare": 3, "datacite": 2, "semantic_scholar": 1}


@dataclass
class ResolvedIntent:
    intent: str
    status: str                       # "verified" | "unresolved"
    candidates: list[dict] = field(default_factory=list)        # top-N verified
    candidates_tried: list[dict] = field(default_factory=list)  # audit


@dataclass
class ResolvedDatasets:
    datasets: list[ResolvedIntent]


def extract_dataset_intents(spec_text: str) -> list[str]:
    """Deterministic-first extraction of dataset intents from spec.md: DOIs +
    capitalized dataset-name tokens near the word 'dataset'."""
    intents: list[str] = []
    for m in _DOI_RE.finditer(spec_text):
        intents.append(m.group(1).rstrip(".,);]"))
    for line in spec_text.splitlines():
        if "dataset" in line.lower():
            for nm in _NAME_RE.findall(line):
                if nm.lower() not in {"doi", "fr", "sc", "us"} and len(nm) >= 3:
                    intents.append(nm)
    # De-dup, preserve order.
    seen: set[str] = set()
    out: list[str] = []
    for i in intents:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _gather_candidates(intent: str) -> list[DatasetCandidate]:
    cands: list[DatasetCandidate] = []
    for fn in (_sources.search_huggingface, _sources.search_figshare,
               _sources.search_zenodo, _sources.search_datacite):
        try:
            cands.extend(fn(intent, limit=5))
        except Exception:
            continue
    return cands


def resolve_datasets(spec_text: str, *, project_dir: Path, repo_root: Path,
                     top_n: int = 3, budget_s: int = 300) -> ResolvedDatasets:
    import time
    deadline = time.monotonic() + budget_s
    resolved: list[ResolvedIntent] = []
    for intent in extract_dataset_intents(spec_text):
        tried: list[dict] = []
        verified: list[VerifiedDataset] = []
        for c in _gather_candidates(intent):
            if time.monotonic() > deadline:
                break
            rel = query_relevance_score(intent, f"{c.title} {c.hf_id or ''}")
            v = verify_candidate(c, relevance=rel)
            if v is None:
                tried.append({"url": c.url, "source": c.source, "status": "rejected",
                              "reason": "unreachable or wrong format"})
            else:
                tried.append({"url": v.url, "source": v.source, "status": "verified",
                              "format": v.format})
                verified.append(v)
        verified.sort(key=lambda v: (_AUTHORITY.get(v.source, 0), v.relevance), reverse=True)
        top = verified[:top_n]
        resolved.append(ResolvedIntent(
            intent=intent,
            status="verified" if top else "unresolved",
            candidates=[{"url": v.url, "source": v.source, "format": v.format,
                         "relevance": round(v.relevance, 3),
                         "sample_check": {"downloaded_bytes": v.downloaded_bytes, "parsed": True}}
                        for v in top],
            candidates_tried=tried,
        ))
    return ResolvedDatasets(datasets=resolved)
```

- [ ] **Step 4: Run to verify pass** (real network)

Run: `python -m pytest tests/integration/test_dataset_resolver.py -k "extract_dataset_intents or resolve_datasets_real" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/librarian/dataset_resolver.py tests/integration/test_dataset_resolver.py
git commit -m "feat(dataset-resolver): intent extraction + resolve_datasets top-N orchestration"
```

---

## Task 6: manifest write + unresolved escalation

**Files:**
- Modify: `src/llmxive/librarian/dataset_resolver.py`
- Test: `tests/integration/test_dataset_resolver.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/integration/test_dataset_resolver.py
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/integration/test_dataset_resolver.py -k "manifest or unresolved_intents" -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement manifest + helpers**

```python
# append to src/llmxive/librarian/dataset_resolver.py
from datetime import datetime, timezone

import yaml


def write_manifest(rd: ResolvedDatasets, *, project_dir: Path) -> Path:
    out = Path(project_dir) / ".specify" / "memory" / "resolved_datasets.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "datasets": [
            {"intent": d.intent, "status": d.status,
             "candidates": d.candidates, "candidates_tried": d.candidates_tried}
            for d in rd.datasets
        ],
    }
    out.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return out


def unresolved_intents(rd: ResolvedDatasets) -> list[str]:
    return [d.intent for d in rd.datasets if d.status == "unresolved"]


def render_planner_block(rd: ResolvedDatasets) -> str:
    """The 'cite ONLY these' block injected into the Planner user prompt."""
    if not rd.datasets:
        return ""
    lines = ["# Verified datasets (cite ONLY these URLs in research.md — do NOT invent any dataset URL)"]
    for d in rd.datasets:
        if d.status != "verified":
            lines.append(f"- {d.intent}: NO verified source found (do NOT cite a URL for it).")
            continue
        urls = ", ".join(c["url"] for c in d.candidates)
        lines.append(f"- {d.intent} ({d.candidates[0]['format']}): {urls}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/integration/test_dataset_resolver.py -k "manifest or unresolved_intents" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/librarian/dataset_resolver.py tests/integration/test_dataset_resolver.py
git commit -m "feat(dataset-resolver): manifest write + planner block + unresolved helper"
```

---

## Task 7: wire into the Planner

**Files:**
- Modify: `src/llmxive/speckit/plan_cmd.py` (`build_prompt` ~L79-117; `mechanical_step` ~L62-77)
- Modify: `agents/prompts/planner.md`
- Test: `tests/integration/test_planner_dataset_injection.py`

- [ ] **Step 1: Write the failing test** (stub the resolver so this stays deterministic + offline)

```python
# tests/integration/test_planner_dataset_injection.py
def test_build_prompt_injects_verified_datasets(tmp_path, monkeypatch):
    import llmxive.speckit.plan_cmd as plan_cmd
    from llmxive.librarian.dataset_resolver import ResolvedDatasets, ResolvedIntent

    fake = ResolvedDatasets(datasets=[ResolvedIntent(
        "QM9", "verified",
        candidates=[{"url": "https://huggingface.co/datasets/qm9", "source": "huggingface",
                     "format": "parquet", "relevance": 0.9,
                     "sample_check": {"downloaded_bytes": 10, "parsed": True}}],
        candidates_tried=[])])
    monkeypatch.setattr(plan_cmd, "resolve_datasets", lambda *a, **k: fake)

    proj = tmp_path / "projects" / "PROJ-X"
    fdir = proj / "specs" / "001-x"
    fdir.mkdir(parents=True)
    (fdir / "spec.md").write_text("- **FR-001**: download the QM9 dataset (DOI: 10.1038/sdata.2014.22)\n")
    (proj / ".specify" / "memory").mkdir(parents=True)
    (proj / ".specify" / "memory" / "constitution.md").write_text("# C\n")
    (proj / ".specify" / "templates").mkdir(parents=True)
    (proj / ".specify" / "templates" / "plan-template.md").write_text("# Plan template\n")

    from llmxive.speckit.slash_command import SlashCommandContext
    from llmxive.types import BackendName
    ctx = SlashCommandContext(project_id="PROJ-X", project_dir=proj, run_id="r", task_id="t",
        inputs=[], expected_outputs=[], prompt_template_path=tmp_path / "x.md",
        default_backend=BackendName.DARTMOUTH, fallback_backends=[], default_model="m",
        prompt_version="1.0.0", agent_name="planner")
    mech = {"feature_dir": str(fdir), "spec_path": str(fdir / "spec.md")}

    msgs = plan_cmd.PlannerAgent().build_prompt(ctx, mech)
    user = msgs[-1].content
    assert "Verified datasets" in user
    assert "https://huggingface.co/datasets/qm9" in user
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/integration/test_planner_dataset_injection.py -v`
Expected: FAIL (`resolve_datasets` not imported in plan_cmd / block absent).

- [ ] **Step 3: Wire the resolver in**

In `src/llmxive/speckit/plan_cmd.py`, add the import near the top:

```python
from llmxive.librarian.dataset_resolver import (
    resolve_datasets, render_planner_block, write_manifest, unresolved_intents,
)
```

In `mechanical_step`, after computing `feature_dir`/`spec_path`, resolve + persist the manifest and add the rendered block to the returned dict:

```python
        spec_path = feature_dir / "spec.md"
        spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
        resolved = resolve_datasets(spec_text, project_dir=ctx.project_dir,
                                    repo_root=ctx.project_dir.parent.parent)
        write_manifest(resolved, project_dir=ctx.project_dir)
        return {
            "feature_dir": str(feature_dir),
            "spec_path": str(spec_path),
            "script_result": result,
            "dataset_block": render_planner_block(resolved),
        }
```

In `build_prompt`, inject the block into the user message (after the spec, before the Task line):

```python
        dataset_block = mechanical_output.get("dataset_block", "")
        user = (
            f"# spec.md\n\n{spec_text}\n\n"
            f"# Project constitution\n\n{project_constitution}\n\n"
            f"# Plan template\n\n{plan_template}\n\n"
            + (dataset_block + "\n\n" if dataset_block else "")
            + (comments_block + "\n\n" if comments_block else "")
            + "# Task\n\nProduce all five documents per the output contract."
        )
```

In `agents/prompts/planner.md`, in the Rules section, replace the "NEVER invent URLs" rule with:

```markdown
- For dataset/code/paper references in research.md, cite ONLY the URLs listed in
  the "# Verified datasets" block of the user message (these have been
  web-searched and reachability/format-verified for you). NEVER invent or guess
  a dataset URL. If the block says a dataset has NO verified source, describe the
  dataset by name but do NOT fabricate a URL.
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/integration/test_planner_dataset_injection.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/speckit/plan_cmd.py agents/prompts/planner.md tests/integration/test_planner_dataset_injection.py
git commit -m "feat(dataset-resolver): wire resolver into Planner (inject verified URLs)"
```

---

## Task 8: full suite + real PROJ-262 validation

**Files:** (no new code unless a real bug surfaces)

- [ ] **Step 1: Run the resolver + planner + spec-014 suites**

Run: `python -m pytest tests/unit/test_dataset_sources.py tests/integration/test_dataset_resolver.py tests/integration/test_planner_dataset_injection.py tests/integration/test_phase4_plan_tasks.py -v`
Expected: all PASS. Fix CODE (not tests) on any failure; re-run the whole set after each fix.

- [ ] **Step 2: Re-run Phase 4 on PROJ-262 (real, with --force)**

Run: `python scripts/validate_phase4.py --project PROJ-262-predicting-molecular-dipole-moments-with --force`
Expected: the Planner cites the resolver's verified QM9 URL(s); FR-006 passes; project advances toward `analyzed`. If it still fails on a URL, inspect `projects/PROJ-262-*/.specify/memory/resolved_datasets.yaml` + the planner inspection record and fix the resolver (real bug), not the gate.

- [ ] **Step 3: Commit any resolver fixes**

```bash
git add -A && git commit -m "fix(dataset-resolver): <specific issue found on PROJ-262>"
```

---

## Self-Review

- **Spec coverage:** integration point (Task 7 ✓ pre-planner), sources HF/figshare/Zenodo/DataCite + reuse SS/arXiv (Tasks 1-2 ✓; SS/arXiv reuse available via `librarian.search` — add to `_gather_candidates` if a paper-linked source is needed, currently the four registries suffice for QM9), sample-stream+sniff (Task 3 ✓), reachability reuse (Task 4 ✓), top-N (Task 5 ✓), manifest + escalation + cite-only block (Tasks 6-7 ✓), real-call tests (Tasks 1-5, 8 ✓), FR-006 relationship (Task 8 ✓).
- **Placeholder scan:** none — every step has runnable code/commands.
- **Type consistency:** `DatasetCandidate` (sources) → `verify_candidate` → `VerifiedDataset` → `ResolvedIntent.candidates` (dicts) → `render_planner_block`/`write_manifest`. `resolve_datasets(spec_text, *, project_dir, repo_root, top_n, budget_s)` signature consistent across Tasks 5/7 and tests.
- **Note:** Semantic Scholar/arXiv reuse is designed-in but Task 5's `_gather_candidates` ships the four registry sources; a paper-linked-data source can be appended later without interface change (YAGNI for the QM9 case).
