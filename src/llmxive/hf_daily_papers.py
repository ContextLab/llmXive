"""Submit the top-N upvoted Hugging Face *daily-papers* arXiv submissions to
llmXive as `human-submission` / `new-paper` GitHub issues — the same contract
the website's "Submit Paper" dialog uses (`web/js/auth.js::submitPaper`).

Invoked daily at 23:59 UTC by `.github/workflows/hf-daily-papers.yml`. The
hourly `submission-intake.yml` workflow then routes each filed issue through
`agents/submission_intake.py` exactly as if a human had submitted them — the
arXiv source / LaTeX / authors are fetched per the existing pipeline, the
project gets a `PROJ-NNN` id, and the paper enters the paper-review pipeline.

The submitter on each issue is the literal string ``github-actions[bot]`` so
that downstream attribution is honest about the source. ``web_data.py``
filters that submitter out of the contributor leaderboard (see
``_BOT_SUBMITTERS`` there).

Public API:
    fetch_top_papers(date, *, limit=5, http=urllib.request) -> list[Paper]
    build_issue(paper) -> {"title": str, "body": str, "labels": [str, ...]}
    submit_top_papers(date, *, limit=5, dry_run=False, repo="ContextLab/llmXive") -> SubmissionResult

`fetch_top_papers` returns the papers already sorted descending by upvotes,
limited to ``limit`` (the API returns up to ~50; ordering by ``upvotes`` is
applied explicitly so we don't rely on the API's default sort).
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC
from typing import Any

_LOG = logging.getLogger(__name__)

HF_DAILY_ENDPOINT = "https://huggingface.co/api/daily_papers"
ARXIV_ABS_URL = "https://arxiv.org/abs/{id}"
BOT_SUBMITTER = "github-actions[bot]"
ISSUE_LABELS = ["human-submission", "new-paper"]


@dataclass(frozen=True)
class Paper:
    """A single Hugging Face daily-papers entry — only the fields we need."""

    arxiv_id: str
    title: str
    summary: str
    upvotes: int
    arxiv_url: str = field(init=False)

    def __post_init__(self) -> None:  # pragma: no cover — trivial.
        # frozen dataclass workaround for computed field
        object.__setattr__(self, "arxiv_url", ARXIV_ABS_URL.format(id=self.arxiv_id))


@dataclass(frozen=True)
class SubmissionResult:
    """Outcome of one CLI invocation — for human eyeballing + tests."""

    date: str
    fetched: int
    filed: list[dict[str, Any]]    # [{title, url, issue_number, html_url}]
    skipped: list[dict[str, Any]]  # [{title, reason}]
    dry_run: bool


# ────────────────────────────────────────────────────────────────────────────
# HF daily-papers fetch
# ────────────────────────────────────────────────────────────────────────────

def _fetch_daily_json_one(date: str, *, timeout: float = 30.0) -> list[dict[str, Any]]:
    """Hit the public HF daily-papers endpoint for a given YYYY-MM-DD (one attempt).

    Returns the raw JSON list. Raises urllib.error.HTTPError on non-2xx.
    """
    url = f"{HF_DAILY_ENDPOINT}?date={date}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "llmxive-hf-daily/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8")
    data = json.loads(body)
    if not isinstance(data, list):
        raise ValueError(f"unexpected HF daily-papers payload shape: {type(data).__name__}")
    return data


def _fetch_daily_json(date: str, *, timeout: float = 30.0,
                      fallback_days: int = 1) -> tuple[str, list[dict[str, Any]]]:
    """Hit HF daily-papers for `date`; on 400 (date bucket not yet populated)
    fall back to the previous UTC day up to `fallback_days` times.

    Returns (effective_date, payload). Raises urllib.error.HTTPError on
    persistent failure after the fallback chain.

    Rationale: GitHub Actions cron jobs scheduled at ~23:59 UTC routinely
    fire 5-30 minutes late. Once we cross midnight UTC, `_today_utc()` returns
    the *new* day whose HF bucket isn't published yet, and the endpoint
    returns HTTP 400. We must retry against the previous day so the cron
    isn't a roulette wheel keyed on Actions queue depth.
    """
    from datetime import datetime, timedelta

    try:
        ts = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        # Date didn't parse — try a single fetch and let urlopen raise.
        return date, _fetch_daily_json_one(date, timeout=timeout)

    attempts: list[str] = [date]
    for i in range(1, fallback_days + 1):
        attempts.append((ts - timedelta(days=i)).strftime("%Y-%m-%d"))

    last_err: urllib.error.HTTPError | None = None
    for d in attempts:
        try:
            return d, _fetch_daily_json_one(d, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 404):
                # Date bucket not yet populated — try the previous day.
                last_err = exc
                continue
            raise
    # All attempts failed with 400/404 — re-raise the last one.
    assert last_err is not None
    raise last_err


def _parse_paper(entry: dict[str, Any]) -> Paper | None:
    """Pull the fields we need from one HF entry; None if it's malformed."""
    paper = entry.get("paper") if isinstance(entry, dict) else None
    if not isinstance(paper, dict):
        return None
    arxiv_id = str(paper.get("id") or "").strip()
    title = str(paper.get("title") or entry.get("title") or "").strip()
    summary = str(paper.get("summary") or entry.get("summary") or "").strip()
    try:
        upvotes = int(paper.get("upvotes") or 0)
    except (TypeError, ValueError):
        upvotes = 0
    if not arxiv_id or not title:
        return None
    return Paper(arxiv_id=arxiv_id, title=title, summary=summary, upvotes=upvotes)


def fetch_top_papers(
    date: str,
    *,
    limit: int = 5,
    raw_json: list[dict[str, Any]] | None = None,
) -> tuple[str, list[Paper]]:
    """Return (effective_date, top-N HF daily papers) sorted by upvotes desc.

    The effective_date may differ from the requested `date` when the HF
    endpoint returns 400/404 for `date` (bucket not yet populated) and the
    fallback chain in `_fetch_daily_json` succeeds against an earlier day.

    ``raw_json`` lets tests inject without monkey-patching urllib. When
    raw_json is supplied, the effective_date equals the requested date.
    """
    if raw_json is not None:
        effective = date
        data = raw_json
    else:
        effective, data = _fetch_daily_json(date)
    parsed: list[Paper] = []
    for entry in data:
        p = _parse_paper(entry)
        if p is not None:
            parsed.append(p)
    parsed.sort(key=lambda p: (-p.upvotes, p.arxiv_id))
    return effective, parsed[: max(0, int(limit))]


# ────────────────────────────────────────────────────────────────────────────
# Issue payload (matches web/js/auth.js::submitPaper exactly)
# ────────────────────────────────────────────────────────────────────────────

def build_issue(paper: Paper, *, submitter: str = BOT_SUBMITTER) -> dict[str, Any]:
    """Build the same issue payload the website's Submit-Paper dialog files,
    so submission-intake handles it through the identical code path.

    The body markdown matches `web/js/auth.js::submitPaper` (link variant)
    field-for-field — `_parse_new_paper_body` in `submission_intake.py`
    keys off `**URL:**` / `**Submitter:**` (case-insensitive).
    """
    url = paper.arxiv_url
    lines = [
        "> A paper has been submitted for consideration/review (link).",
        "",
        "## Submitted paper",
        "",
        f"- **URL:** {url}",
        f"- **Submitter:** {submitter}",
        f"- **Source:** Hugging Face daily-papers (upvotes: {paper.upvotes})",
        f"- **Title (HF):** {paper.title}",
        "",
        "---",
        "*Submitted automatically by the llmXive HF daily-papers cron — "
        "the submission-intake agent will file this and create/link a "
        "project within the hour.*",
    ]
    return {
        "title": f"New paper (link): {url[:80]}",
        "body": "\n".join(lines),
        "labels": list(ISSUE_LABELS),
    }


# ────────────────────────────────────────────────────────────────────────────
# Filing via `gh` (matches submission-intake.yml's pattern)
# ────────────────────────────────────────────────────────────────────────────

def _gh_api_create_issue(repo: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST a new issue via `gh api`. Returns the parsed response JSON."""
    args = [
        "gh", "api", "--method", "POST",
        f"repos/{repo}/issues",
        "-H", "Accept: application/vnd.github+json",
        "--input", "-",
    ]
    proc = subprocess.run(args, input=json.dumps(payload), capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return json.loads(proc.stdout)


def _list_recent_paper_issue_urls(repo: str, *, per_page: int = 100) -> set[str]:
    """Return the set of arXiv URLs already present in open or recently-closed
    `new-paper` issues so we don't double-file the same paper if the workflow
    is retried within the same day."""
    seen: set[str] = set()
    for state in ("open", "closed"):
        proc = subprocess.run(
            ["gh", "api", "--paginate",
             f"repos/{repo}/issues?state={state}&labels=new-paper&per_page={per_page}"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            _LOG.warning("gh issues list (%s) failed: %s", state, proc.stderr.strip())
            continue
        # gh --paginate concatenates JSON arrays — handle either one array or
        # multiple back-to-back.
        text = proc.stdout.strip()
        try:
            data = json.loads(text)
            chunks = [data]
        except json.JSONDecodeError:
            # adjacent arrays
            text = text.replace("][", ",")
            try:
                data = json.loads(text)
                chunks = [data]
            except Exception:
                continue
        for chunk in chunks:
            for issue in chunk or []:
                body = (issue.get("body") or "")
                # match the URL line we put into build_issue
                for line in body.splitlines():
                    s = line.strip()
                    if s.lower().startswith("- **url:**"):
                        url = s.split(":", 2)[-1].strip()
                        if url:
                            seen.add(url)
                        break
    return seen


# ────────────────────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────────────────────

def submit_top_papers(
    date: str,
    *,
    limit: int = 5,
    dry_run: bool = False,
    repo: str = "ContextLab/llmXive",
    raw_json: list[dict[str, Any]] | None = None,
) -> SubmissionResult:
    """Fetch HF daily top-N and file an issue per paper (or print payloads
    when ``dry_run``). Idempotent across same-day retries: an arXiv URL
    already present in any open or closed `new-paper` issue is skipped.
    """
    effective_date, papers = fetch_top_papers(date, limit=limit, raw_json=raw_json)
    if effective_date != date:
        print(
            f"[hf-daily-papers] HF bucket for {date} not yet populated; "
            f"falling back to {effective_date}",
            file=sys.stderr,
        )
    date = effective_date  # record the date that actually returned data
    filed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    seen: set[str] = set() if dry_run else _list_recent_paper_issue_urls(repo)
    for p in papers:
        if p.arxiv_url in seen:
            skipped.append({"title": p.title, "url": p.arxiv_url,
                            "reason": "already filed as a new-paper issue"})
            continue
        payload = build_issue(p)
        if dry_run:
            filed.append({"title": payload["title"], "url": p.arxiv_url,
                          "issue_number": None, "html_url": None,
                          "preview_body": payload["body"]})
            continue
        try:
            issue = _gh_api_create_issue(repo, payload)
        except Exception as exc:
            skipped.append({"title": p.title, "url": p.arxiv_url,
                            "reason": f"gh api failed: {exc}"})
            continue
        filed.append({
            "title": payload["title"],
            "url": p.arxiv_url,
            "issue_number": issue.get("number"),
            "html_url": issue.get("html_url"),
        })
    return SubmissionResult(
        date=date,
        fetched=len(papers),
        filed=filed,
        skipped=skipped,
        dry_run=dry_run,
    )


def _today_utc() -> str:
    """Default date for the HF daily-papers fetch — YESTERDAY in UTC.

    HF's daily-papers feed is bucketed by *publication* day (UTC). A bucket
    is populated when HF's editorial pipeline finishes that day's roundup.
    Empirically that happens in the late afternoon UTC; running before that
    against today's date returns HTTP 400.

    We default to (today_utc - 1 day) so the cron is robust against
    schedule drift (Actions can fire 5-30 minutes late past midnight UTC)
    AND against HF publishing slowly. The fallback in `_fetch_daily_json`
    will walk further back if even yesterday's bucket is unpopulated.

    Tests / manual runs can still pass an explicit `--date YYYY-MM-DD`.
    """
    from datetime import datetime, timedelta
    return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")


def cli_main(argv: Sequence[str] | None = None) -> int:
    """`python -m llmxive hf-papers submit-top` entry point.

    Returns 0 on success (including all-skipped). Returns 2 if the fetch
    itself fails or `gh` is missing in non-dry-run mode.
    """
    import argparse
    p = argparse.ArgumentParser(prog="llmxive hf-papers submit-top",
                                description="Submit top-N HF daily papers as llmXive new-paper issues.")
    p.add_argument("--date", default=None, help="UTC date (YYYY-MM-DD); defaults to today UTC.")
    p.add_argument("--limit", type=int, default=5, help="how many papers to submit (default: 5).")
    p.add_argument("--repo", default="ContextLab/llmXive", help="GitHub repo (owner/name).")
    p.add_argument("--dry-run", action="store_true", help="print issue payloads instead of filing.")
    args = p.parse_args(argv)
    date = args.date or _today_utc()

    import shutil
    if not args.dry_run and shutil.which("gh") is None:
        print("error: `gh` CLI not found on PATH", file=sys.stderr)
        return 2

    try:
        result = submit_top_papers(date, limit=args.limit, dry_run=args.dry_run, repo=args.repo)
    except urllib.error.HTTPError as exc:
        print(f"error: HF daily-papers HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"error: HF daily-papers fetch failed: {exc!r}", file=sys.stderr)
        return 2

    print(f"hf-daily-papers @ {date}: fetched={result.fetched} filed={len(result.filed)} "
          f"skipped={len(result.skipped)} dry_run={result.dry_run}")
    for row in result.filed:
        n = row.get("issue_number")
        u = row.get("html_url")
        print(f"  filed: {row['title']}  →  #{n} {u or ''}".rstrip())
    for row in result.skipped:
        print(f"  skipped: {row['title']}  ({row.get('reason')})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli_main())
