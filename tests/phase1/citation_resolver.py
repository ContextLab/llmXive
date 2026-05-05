"""Phase 1 citation resolver (Stage 1: mechanical).

Implements the contract at
``specs/003-phase1-idea-lifecycle-testing/contracts/citation-resolver.md``.

Reads ``projects/<id>/idea/<slug>.md``, extracts citations matching one of
four patterns (arXiv md-link, DOI md-link, URL md-link, inline raw URL
inside Related-work / References sections), resolves each via the
appropriate mechanism (arXiv API, DOI HEAD with redirect-follow, URL HEAD
with GET-fallback on 405), and emits a JSON array of ``ResolutionResult``
records to stdout.

Runs each citation in a thread-pool with a hard
``Future.result(timeout=N)`` deadline (matches the production-side pattern
in ``src/llmxive/backends/dartmouth.py``).
"""

from __future__ import annotations

import argparse
import concurrent.futures as _cf
import dataclasses
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

import requests

USER_AGENT = "llmxive-citation-resolver/1.0 (https://github.com/ContextLab/llmXive)"
DEFAULT_TIMEOUT_SECONDS = 60.0
ARXIV_API = "http://export.arxiv.org/api/query"

ARXIV_RE = re.compile(
    r"\[(?P<title>[^\]]+)\]\(https?://arxiv\.org/abs/(?P<id>\d{4}\.\d{4,5})(?:v\d+)?\)"
)
DOI_RE = re.compile(
    r"\[(?P<title>[^\]]+)\]\(https?://(?:dx\.)?doi\.org/(?P<doi>10\.\d{4,9}/[^\s)]+)\)"
)
URL_RE = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<url>https?://[^\s)]+)\)")
INLINE_URL_RE = re.compile(r"\bhttps?://[^\s)]+\b")
INLINE_SECTION_HEADER_RE = re.compile(
    r"^#{1,6}\s+(related\s*work|references)\b", re.IGNORECASE
)
SECTION_HEADER_RE = re.compile(r"^#{1,6}\s+\S")


@dataclasses.dataclass
class Citation:
    raw_text: str
    kind: str
    identifier: str
    line_number: int

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ResolutionResult:
    citation: Citation
    stage1_status: str
    stage1_evidence: dict[str, Any]
    stage2_status: str | None = None
    stage2_evidence: str | None = None
    final_verdict: str = "failed"
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["citation"] = self.citation.to_dict()
        return d


def extract_citations(text: str) -> list[Citation]:
    """Walk the input line-by-line, applying patterns in priority order.

    arXiv > DOI > URL md-link > inline URL (only inside Related-work /
    References sections). Each line emits one citation per non-overlapping
    match; lines that match a higher-priority pattern do NOT also produce
    matches for lower-priority patterns at the same span.
    """
    citations: list[Citation] = []
    in_inline_section = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        # Track which subsection we're in so the inline-URL pattern knows
        # whether it's allowed to fire on raw URLs.
        if INLINE_SECTION_HEADER_RE.match(line):
            in_inline_section = True
            continue
        if SECTION_HEADER_RE.match(line):
            in_inline_section = False

        consumed_spans: list[tuple[int, int]] = []

        for m in ARXIV_RE.finditer(line):
            citations.append(
                Citation(
                    raw_text=m.group(0),
                    kind="arxiv",
                    identifier=m.group("id"),
                    line_number=lineno,
                )
            )
            consumed_spans.append(m.span())

        for m in DOI_RE.finditer(line):
            if any(_overlaps(m.span(), s) for s in consumed_spans):
                continue
            citations.append(
                Citation(
                    raw_text=m.group(0),
                    kind="doi",
                    identifier=m.group("doi"),
                    line_number=lineno,
                )
            )
            consumed_spans.append(m.span())

        for m in URL_RE.finditer(line):
            if any(_overlaps(m.span(), s) for s in consumed_spans):
                continue
            citations.append(
                Citation(
                    raw_text=m.group(0),
                    kind="url",
                    identifier=m.group("url"),
                    line_number=lineno,
                )
            )
            consumed_spans.append(m.span())

        if in_inline_section:
            for m in INLINE_URL_RE.finditer(line):
                if any(_overlaps(m.span(), s) for s in consumed_spans):
                    continue
                citations.append(
                    Citation(
                        raw_text=m.group(0),
                        kind="inline_url",
                        identifier=m.group(0),
                        line_number=lineno,
                    )
                )
                consumed_spans.append(m.span())

    return citations


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_arxiv(citation: Citation) -> tuple[str, dict[str, Any]]:
    url = f"{ARXIV_API}?id_list={citation.identifier}"
    try:
        r = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=30, allow_redirects=True
        )
        body = r.text
        n_entries = body.count("<entry>")
        snippet = body[:400] if "<entry>" in body else body[:200]
        evidence = {
            "url_checked": url,
            "http_status": r.status_code,
            "redirect_chain": [resp.url for resp in r.history],
            "api_response_snippet": snippet,
        }
        if r.status_code == 200 and n_entries == 1:
            return "resolved", evidence
        if r.status_code == 200 and n_entries > 1:
            return "ambiguous", evidence
        if r.status_code == 200 and n_entries == 0:
            return "ambiguous", evidence  # arxiv returns 200 with empty result for unknown ids
        return "unreachable", evidence
    except (requests.RequestException, OSError) as e:
        return "unreachable", {
            "url_checked": url,
            "http_status": None,
            "redirect_chain": [],
            "api_response_snippet": f"error: {type(e).__name__}: {e}",
        }


def _head_with_get_fallback(url: str) -> tuple[str, dict[str, Any]]:
    try:
        r = requests.head(
            url, headers={"User-Agent": USER_AGENT}, timeout=30, allow_redirects=True
        )
        if r.status_code == 405:
            r = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "Range": "bytes=0-2047"},
                timeout=30,
                allow_redirects=True,
                stream=True,
            )
            r.close()
        evidence = {
            "url_checked": url,
            "http_status": r.status_code,
            "redirect_chain": [resp.url for resp in r.history],
            "api_response_snippet": None,
        }
        if 200 <= r.status_code < 300:
            return "resolved", evidence
        if 300 <= r.status_code < 400:
            return "ambiguous", evidence
        # 401 / 403 / 429 after at least one redirect = paywall, login-wall,
        # or rate-limit on a host the resolver demonstrably reached. The DOI /
        # URL itself is real; the *content* needs Stage 2 verification, so
        # classify as ambiguous (not unreachable).
        if r.status_code in (401, 403, 429) and r.history:
            return "ambiguous", evidence
        return "unreachable", evidence
    except (requests.RequestException, OSError) as e:
        return "unreachable", {
            "url_checked": url,
            "http_status": None,
            "redirect_chain": [],
            "api_response_snippet": f"error: {type(e).__name__}: {e}",
        }


def _resolve_doi(citation: Citation) -> tuple[str, dict[str, Any]]:
    return _head_with_get_fallback(f"https://doi.org/{citation.identifier}")


def _resolve_url(citation: Citation) -> tuple[str, dict[str, Any]]:
    return _head_with_get_fallback(citation.identifier)


_RESOLVERS = {
    "arxiv": _resolve_arxiv,
    "doi": _resolve_doi,
    "url": _resolve_url,
    "inline_url": _resolve_url,
}


def resolve_one(citation: Citation, timeout: float) -> ResolutionResult:
    """Run the kind-appropriate resolver under a hard thread-pool deadline."""
    fn = _RESOLVERS[citation.kind]
    with _cf.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fn, citation)
        try:
            status, evidence = fut.result(timeout=timeout)
        except _cf.TimeoutError:
            status = "unreachable"
            evidence = {
                "url_checked": citation.identifier,
                "http_status": None,
                "redirect_chain": [],
                "api_response_snippet": f"error: TimeoutError after {timeout}s",
            }
    final = "verified" if status == "resolved" else "failed"
    return ResolutionResult(
        citation=citation,
        stage1_status=status,
        stage1_evidence=evidence,
        stage2_status=None,
        stage2_evidence=None,
        final_verdict=final,
        timestamp=_now_iso(),
    )


def run_self_test() -> int:
    """Verify resolver behavior on one known-good and one known-bad URL."""
    a = Citation(
        raw_text="[Attention Is All You Need (2017)](https://arxiv.org/abs/1706.03762)",
        kind="arxiv",
        identifier="1706.03762",
        line_number=0,
    )
    b = Citation(
        raw_text="[Made-up (2026)](https://example.invalid/never-existed)",
        kind="url",
        identifier="https://example.invalid/never-existed",
        line_number=0,
    )
    ra = resolve_one(a, timeout=DEFAULT_TIMEOUT_SECONDS)
    rb = resolve_one(b, timeout=DEFAULT_TIMEOUT_SECONDS)
    print(
        f"[self-test] A: {ra.stage1_status}; B: {rb.stage1_status}",
        file=sys.stderr,
    )
    return 0 if ra.stage1_status == "resolved" and rb.stage1_status == "unreachable" else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1 citation resolver (Stage 1: mechanical)."
    )
    parser.add_argument("idea_md_path", nargs="?", default=None)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    if not args.idea_md_path:
        print("error: idea_md_path is required (or use --self-test)", file=sys.stderr)
        return 64

    p = Path(args.idea_md_path)
    if not p.exists() or not p.is_file():
        print(f"error: input file not found: {p}", file=sys.stderr)
        return 1

    text = p.read_text(encoding="utf-8")
    citations = extract_citations(text)
    if not citations:
        print(f"error: no citations parsed from {p}", file=sys.stderr)
        return 1

    results: list[ResolutionResult] = []
    for i, c in enumerate(citations, start=1):
        r = resolve_one(c, timeout=args.timeout)
        results.append(r)
        print(
            f"[{i}/{len(citations)}] {c.kind} {c.identifier} → {r.stage1_status}",
            file=sys.stderr,
        )

    print(json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
