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
