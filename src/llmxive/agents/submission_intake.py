"""Submission-intake maintenance agent (FR-020).

Triages one human-submission GitHub issue from the public website:

  - `feedback` → one LLM call decides whether to route the feedback to a
    pipeline step (as a comment on the project's tracking issue, optionally
    nudging state — conservatively), turn it into a new brainstormed project,
    or just acknowledge it.
  - `new-paper` → create-or-link a project and either move the staged
    `submissions/inbox/<…>.pdf` to the project's canonical home (via the
    Contents API: read → PUT → DELETE the inbox copy) or record the URL.

In all `ok` cases the agent comments on the human-submission issue describing
what it did and then closes it. On any LLM/parse/unexpected failure it leaves
an explanatory comment and the issue stays open (the next cron tick retries; a
maintainer can also handle it). It is idempotent — if the work is already done
(target project exists / PDF already moved / issue already closed) it returns
`skipped` rather than re-doing it.

Invoked hourly by `.github/workflows/submission-intake.yml` over open
`human-submission` issues; the entry point is the `submissions process` CLI
subcommand (`python -m llmxive submissions process`).
"""

from __future__ import annotations

import dataclasses
import json
import re
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from llmxive.agents import registry as registry_loader
from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import chat_with_fallback
from llmxive.librarian import LIBRARIAN_DEFAULT_FIELDS
from llmxive.state import project as project_store
from llmxive.types import AgentRegistryEntry, Project, Stage

REPO = "ContextLab/llmXive"
PROMPT_PATH = "agents/prompts/submission_intake.md"
INBOX_DIR = "submissions/inbox"

# Pipeline-step keys a feedback verdict may route to (mirrors web_data.py's
# pipeline_steps[] keys + their stage). Used to validate the LLM verdict and to
# map a step key → the Stage to nudge toward.
_STEP_TO_STAGE: dict[str, Stage] = {
    "brainstormed": Stage.BRAINSTORMED,
    "flesh_out": Stage.FLESH_OUT_IN_PROGRESS,
    "specified": Stage.SPECIFIED,
    "clarified": Stage.CLARIFY_IN_PROGRESS,
    "planned": Stage.PLANNED,
    "tasked": Stage.TASKED,
    "in_progress": Stage.IN_PROGRESS,
    "research_review": Stage.RESEARCH_REVIEW,
    "paper_init": Stage.PAPER_DRAFTING_INIT,
    "paper_spec": Stage.PAPER_SPECIFIED,
    "paper_plan": Stage.PAPER_PLANNED,
    "paper_tasks": Stage.PAPER_TASKED,
    "paper_drafting": Stage.PAPER_IN_PROGRESS,
    "paper_complete": Stage.PAPER_COMPLETE,
    "paper_review": Stage.PAPER_REVIEW,
    "posted": Stage.POSTED,
}


# ── result type (E8) ────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class IntakeResult:
    status: str            # "ok" | "failed" | "skipped"
    action: str | None = None     # "routed-to-step" | "created-project" | "filed-paper" | "acknowledged" | None
    target: str | None = None     # project/artifact id acted on / created, or None
    error: str | None = None
    comment_url: str | None = None


# ── a thin `gh` wrapper (reuses the existing pattern in integrations.issues) ─

GhFn = Callable[..., tuple[int, str, str]]


def _default_gh(*args: str, stdin: str | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, input=stdin)
    return proc.returncode, proc.stdout, proc.stderr


def _gh_json(gh: GhFn, *args: str) -> Any:
    rc, out, err = gh(*args)
    if rc != 0:
        raise RuntimeError("gh " + " ".join(args) + " failed: " + (err or out).strip())
    return json.loads(out) if out.strip() else None


def _comment(gh: GhFn, issue_number: int, body: str) -> str | None:
    """Post a comment; return the comment's html_url, or None on failure."""
    try:
        data = _gh_json(gh, "api", f"repos/{REPO}/issues/{issue_number}/comments",
                        "-X", "POST", "-f", f"body={body}")
        return (data or {}).get("html_url")
    except Exception:
        return None


def _close_issue(gh: GhFn, issue_number: int) -> None:
    try:
        gh("api", f"repos/{REPO}/issues/{issue_number}", "-X", "PATCH", "-f", "state=closed")
    except Exception:
        pass


# ── helpers ─────────────────────────────────────────────────────────────────

def _labels(issue: dict[str, Any]) -> set[str]:
    out = set()
    for lab in issue.get("labels", []) or []:
        out.add(lab["name"] if isinstance(lab, dict) else str(lab))
    return out


def _subtype(issue: dict[str, Any]) -> str | None:
    labs = _labels(issue)
    if "human-submission" not in labs:
        return None
    has_fb, has_np = "feedback" in labs, "new-paper" in labs
    if has_fb and not has_np:
        return "feedback"
    if has_np and not has_fb:
        return "new-paper"
    return None  # malformed: neither, or both


_FIELD_RE = re.compile(r"\*\*([^*]+):\*\*\s*(.+?)\s*$", re.MULTILINE)


def _parse_feedback_body(body: str) -> dict[str, str]:
    """Pull the structured fields out of a feedback issue body (best-effort)."""
    fields = {m.group(1).strip().lower(): m.group(2).strip() for m in _FIELD_RE.finditer(body or "")}
    out = {
        "target_id": fields.get("project / artifact") or fields.get("project") or "",
        "target_kind": fields.get("artifact kind") or "",
        "target_stage": fields.get("stage") or "",
        "submitter": fields.get("submitter") or "",
    }
    # The feedback text is the `## Feedback` section (between it and `## Target`).
    m = re.search(r"##\s*Feedback\s*\n+(.*?)\n+##\s*Target", body or "", re.DOTALL | re.IGNORECASE)
    out["content"] = (m.group(1).strip() if m else (body or "").strip())
    for k in ("target_id", "target_kind", "target_stage", "submitter"):
        if out[k] in ("(unspecified)", "(unspecified)."):
            out[k] = ""
    return out


def _parse_new_paper_body(body: str) -> dict[str, str]:
    fields = {m.group(1).strip().lower(): m.group(2).strip() for m in _FIELD_RE.finditer(body or "")}
    url = fields.get("url", "")
    staged = fields.get("staged file", "").strip("`").strip()
    return {"url": url, "staged_file": staged, "submitter": fields.get("submitter", "")}


def _project_exists(repo: Path, project_id: str) -> bool:
    if not project_id:
        return False
    try:
        project_store.load(project_id, repo_root=repo)
        return True
    except Exception:
        return (repo / "state" / "projects" / f"{project_id}.yaml").exists()


def _issue_number_for_project(repo: Path, project_id: str) -> int | None:
    """Read `github_issue` from the project's idea front-matter."""
    idea_dir = repo / "projects" / project_id / "idea"
    if not idea_dir.is_dir():
        return None
    import yaml
    for md in idea_dir.glob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            continue
        try:
            front = yaml.safe_load(text[3:text.index("---", 3)]) or {}
        except (ValueError, yaml.YAMLError):
            continue
        v = front.get("github_issue")
        if v is None:
            continue
        m = re.search(r"/issues/(\d+)", str(v)) or re.match(r"^(\d+)$", str(v).strip())
        if m:
            return int(m.group(1))
    return None


def _fetch_arxiv_source(arxiv_id: str, dest_dir: Path) -> dict[str, Any]:
    """Fetch the .tar.gz source for an arXiv paper and extract it into
    `dest_dir`. Returns a dict with `{ok, files, toplevel_tex, error}`.

    The arXiv e-print endpoint returns a gzipped tar (or sometimes a bare
    `.tex.gz` for single-file submissions). We sniff the magic bytes and
    handle both. Safe-extract per Python 3.12's `filter="data"` (rejects
    absolute paths, `..`, symlinks).
    """
    import io
    import tarfile
    import urllib.request
    out: dict[str, Any] = {"ok": False, "files": [], "toplevel_tex": [], "error": None}
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "llmXive-bot/0.1 (https://context-lab.com/llmXive)",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except Exception as exc:
        out["error"] = f"download failed: {exc}"
        return out
    # Cap size at 50 MB compressed (arXiv's hard cap).
    if len(data) > 50 * 1024 * 1024:
        out["error"] = f"source too large ({len(data)} bytes)"
        return out
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Detect tar.gz vs. bare gzipped single file.
    # gzip magic = 0x1f 0x8b; tar inside gzip = "ustar" at byte offset 257 of
    # the *decompressed* stream.
    try:
        import gzip
        decompressed = gzip.decompress(data)
    except Exception as exc:
        out["error"] = f"not gzip: {exc}"
        return out
    is_tar = (len(decompressed) >= 262 and decompressed[257:262] == b"ustar")
    try:
        if is_tar:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
                # Defensive: reject members with .., absolute paths, links.
                for m in tar.getmembers():
                    name = m.name
                    if name.startswith("/") or ".." in Path(name).parts or m.issym() or m.islnk() or m.isdev():
                        continue
                    tar.extract(m, path=dest_dir, filter="data")
                    out["files"].append(name)
        else:
            # Bare .tex.gz — single file.
            (dest_dir / "main.tex").write_bytes(decompressed)
            out["files"].append("main.tex")
    except Exception as exc:
        out["error"] = f"extract failed: {exc}"
        return out
    # Identify toplevel .tex files via 00README.json if present; else heuristics.
    readme = dest_dir / "00README.json"
    if readme.exists():
        try:
            j = json.loads(readme.read_text(encoding="utf-8"))
            out["toplevel_tex"] = [s["filename"] for s in j.get("sources", [])
                                   if s.get("usage") == "toplevel" and s.get("filename", "").endswith(".tex")]
        except Exception:
            pass
    if not out["toplevel_tex"]:
        # Heuristics: a top-level .tex containing \documentclass.
        for f in sorted(dest_dir.glob("*.tex")):
            try:
                t = f.read_text(encoding="utf-8", errors="replace")
                if r"\documentclass" in t:
                    out["toplevel_tex"].append(f.name)
            except Exception:
                pass
    out["ok"] = True
    return out


_GITHUB_RE = re.compile(r"https?://github\.com/([A-Za-z0-9._-]+/[A-Za-z0-9._-]+)")
_OSF_RE = re.compile(r"https?://osf\.io/[A-Za-z0-9_-]+")
_ZENODO_RE = re.compile(r"https?://zenodo\.org/(?:record|doi)/[A-Za-z0-9./_-]+")


def _parse_tex_external_resources(tex_dir: Path) -> dict[str, list[str]]:
    """Scan all .tex files in `tex_dir` for code + data resource pointers
    (github / osf / zenodo URLs). Returns `{code: [...], data: [...]}`.
    """
    out: dict[str, list[str]] = {"code": [], "data": []}
    seen_code, seen_data = set(), set()
    for f in tex_dir.rglob("*.tex"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for u in _GITHUB_RE.findall(text):
            url = f"https://github.com/{u}"
            if url not in seen_code:
                seen_code.add(url)
                out["code"].append(url)
        for u in _OSF_RE.findall(text):
            if u not in seen_data:
                seen_data.add(u)
                out["data"].append(u)
        for u in _ZENODO_RE.findall(text):
            if u not in seen_data:
                seen_data.add(u)
                out["data"].append(u)
    return out


def _slugify(s: str) -> str:
    # Strip BOTH before AND after truncation — otherwise the [:40] cut can land
    # on a `-` and leave the slug ending with one (e.g. "ecotourism-in-").
    base = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return base[:40].strip("-") or "submission"


# arXiv top-level category → project field (best-effort; the user can refine).
_ARXIV_CATEGORY_TO_FIELD: dict[str, str] = {
    "cs": "computer science",
    "math": "mathematics",
    "stat": "statistics",
    "physics": "physics",
    "astro-ph": "astronomy", "astro": "astronomy",
    "cond-mat": "physics",
    "gr-qc": "physics", "hep-th": "physics", "hep-ph": "physics",
    "hep-ex": "physics", "hep-lat": "physics", "nucl-ex": "physics",
    "nucl-th": "physics", "quant-ph": "physics",
    "q-bio": "biology", "bio": "biology",
    "q-fin": "economics", "econ": "economics",
    "eess": "engineering",
    # cs.CL is computation+language — closer to linguistics than CS for our taxonomy
    "cs.cl": "linguistics",
}


def _arxiv_metadata(
    url: str,
) -> tuple[list[str], str | None, str | None, str | None]:
    """Best-effort arXiv metadata fetch for a paper-submission URL.

    The user's rule: credit on a submitted paper goes to its *authors* (parsed
    from the paper itself), not the submitter. For arXiv URLs we can grab the
    author list cheaply via the arXiv API (no auth, returns Atom XML); for
    other URLs / uploaded PDFs the paper-pipeline's existing tooling handles
    author parsing later.

    Returns `(authors, title, field, abstract)` — empty / None when not
    applicable or on any failure (a missing/failed lookup never blocks intake).
    `field` is derived from the primary arXiv category via
    `_ARXIV_CATEGORY_TO_FIELD`. `abstract` is the paper's summary from arXiv
    (whitespace-normalized; arXiv embeds line breaks the API doesn't strip).
    """
    if not url:
        return [], None, None, None
    m = re.search(r"arxiv\.org/(?:abs|pdf|html)/([0-9]{4}\.[0-9]{4,6})", url)
    if not m:
        return [], None, None, None
    arxiv_id = m.group(1)
    try:
        import urllib.request
        from xml.etree import ElementTree as ET
        with urllib.request.urlopen(
            f"http://export.arxiv.org/api/query?id_list={arxiv_id}", timeout=15
        ) as r:
            xml = r.read().decode("utf-8", errors="replace")
        ns = {"a": "http://www.w3.org/2005/Atom", "ar": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(xml)
        entry = root.find("a:entry", ns)
        if entry is None:
            return [], None, None, None
        authors = [
            (a.findtext("a:name", default="", namespaces=ns) or "").strip()
            for a in entry.findall("a:author", ns)
        ]
        authors = [a for a in authors if a]
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        # arXiv embeds hard line breaks inside the summary; the card UI wants
        # a single paragraph of prose. Collapse whitespace.
        raw_summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
        abstract = re.sub(r"\s+", " ", raw_summary) if raw_summary else None
        # Map the primary arXiv category to a project field — exact-match first
        # (e.g. cs.CL → linguistics), then top-level (cs → computer science).
        primary = entry.find("ar:primary_category", ns)
        field = None
        if primary is not None:
            cat = (primary.get("term") or "").strip().lower()
            field = _ARXIV_CATEGORY_TO_FIELD.get(cat) or _ARXIV_CATEGORY_TO_FIELD.get(cat.split(".")[0])
        return authors, (title or None), field, abstract
    except Exception:
        return [], None, None, None


# Backwards-compatible shim — older test imports + callers expect a 2-tuple.
def _arxiv_authors(url: str) -> tuple[list[str], str | None]:
    authors, title, _, _ = _arxiv_metadata(url)
    return authors, title


# Pattern used to detect projects whose title is literally an arXiv URL
# (the intake fallback when the arXiv API was rate-limited at submission
# time — see line ~866's `title = fetched_title or title_seed`).
_ARXIV_URL_TITLE_RE = re.compile(
    r"^\s*https?://(?:www\.)?arxiv\.org/(?:abs|pdf|html)/[0-9]{4}\.[0-9]{4,6}\s*$",
    re.IGNORECASE,
)


def heal_paper_metadata(repo_root: Path) -> dict[str, Any]:
    """Heal paper-submission metadata that was incompletely populated at
    intake time (typically because the arXiv API was rate-limited).

    Two failure modes we fix:
      1. `paper/metadata.json::title` is an arXiv URL string — the intake
         fell back to the issue title (which the website auto-fills from
         the URL when no human title was provided).
      2. `paper/metadata.json::abstract` is null/missing while
         `arxiv_id` is present — same root cause, the API call dropped.

    For each affected project:
      - Re-fetch arXiv metadata (title, authors, field, abstract).
      - Update `paper/metadata.json` (preserve all other fields).
      - Update `state/projects/<id>.yaml::title` (and `field` if empty).

    Symptom seen in the wild (PROJ-578/579/580/581 on 2026-05-16): paper
    cards showed `https://arxiv.org/abs/2605.14906` as the title and the
    GitHub-issue boilerplate body as the description. After heal: real
    paper title + the actual abstract.

    Returns a summary dict for logging.
    """
    repo_root = Path(repo_root)
    summary: dict[str, Any] = {"scanned": 0, "healed": [], "skipped": [], "failed": []}
    projects_dir = repo_root / "projects"
    if not projects_dir.is_dir():
        return summary
    for pdir in sorted(projects_dir.iterdir()):
        if not pdir.is_dir() or not pdir.name.startswith("PROJ-"):
            continue
        meta_path = pdir / "paper" / "metadata.json"
        if not meta_path.is_file():
            continue
        summary["scanned"] += 1
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError) as exc:
            summary["failed"].append({"project": pdir.name, "reason": f"unreadable: {exc}"})
            continue
        if not isinstance(meta, dict):
            continue
        arxiv_id = (meta.get("arxiv_id") or "").strip()
        if not arxiv_id:
            # Nothing to fetch against — can't heal.
            continue
        title = (meta.get("title") or "").strip()
        abstract = (meta.get("abstract") or "").strip() if meta.get("abstract") else ""
        title_is_url = bool(_ARXIV_URL_TITLE_RE.match(title))
        needs_heal = title_is_url or not abstract or not meta.get("authors")
        if not needs_heal:
            continue
        # Re-fetch from arXiv (this is the same call the intake makes;
        # if arXiv is rate-limited again, this skip-then-retry-next-tick
        # is exactly what we want).
        url = meta.get("arxiv_url") or f"https://arxiv.org/abs/{arxiv_id}"
        authors, fetched_title, fetched_field, fetched_abstract = _arxiv_metadata(url)
        if not fetched_title and not fetched_abstract:
            summary["skipped"].append({"project": pdir.name,
                                       "reason": "arxiv fetch returned empty"})
            continue
        # Snapshot pre-update truths for the report — `meta` is mutated in place.
        had_authors_before = bool(meta.get("authors"))
        had_abstract_before = bool(abstract)
        # Update metadata.json in place (preserve unrelated fields).
        if fetched_title:
            meta["title"] = fetched_title
        if authors and not had_authors_before:
            meta["authors"] = authors
        if fetched_abstract and not had_abstract_before:
            meta["abstract"] = fetched_abstract
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        # Update state YAML title (and field if empty).
        try:
            project = project_store.load(pdir.name, repo_root=repo_root)
            updates: dict[str, Any] = {}
            if fetched_title and project.title != fetched_title:
                updates["title"] = fetched_title[:200]
            if (fetched_field and fetched_field in VALID_FIELDS
                    and (project.field in (None, "", "other"))):
                updates["field"] = fetched_field
            if updates:
                updates["updated_at"] = datetime.now(UTC)
                project = project.model_copy(update=updates)
                project_store.save(project, repo_root=repo_root)
        except Exception as exc:
            summary["failed"].append({"project": pdir.name,
                                       "reason": f"state update failed: {exc}"})
            continue
        summary["healed"].append({
            "project": pdir.name,
            "old_title": title,
            "new_title": fetched_title or title,
            "abstract_filled": bool(fetched_abstract and not had_abstract_before),
            "authors_filled": bool(authors and not had_authors_before),
        })
    return summary


# Sentinels that mean "no real submitter named" — fall back to the GitHub issue
# author. Matches the legacy llmXive automation-system's text and our own form.
_NO_SUBMITTER_SENTINELS = (
    "(unspecified)",
    "submitted via llmxive dashboard",
    "submitted via the llmxive dashboard",
    "llmxive dashboard",
    "spec007-test",          # automated-test marker
    "spec-007 test",
    "",
)


def _looks_like_no_submitter(s: str) -> bool:
    n = (s or "").strip().lower().rstrip(".")
    return any(n == sentinel for sentinel in _NO_SUBMITTER_SENTINELS)


# A "🤖 Model Attribution" comment from the legacy llmXive automation system —
# the contributing model is in the **bold** after the colon on the first line.
_MODEL_ATTR_RE = re.compile(
    r"Model Attribution\s*\n+(?:This contribution was generated by:\s*)?\*\*([^*]+)\*\*",
    re.IGNORECASE,
)
# Also recognize the "Model: <name>" line legacy ideas sometimes have in the body.
_LEGACY_MODEL_BODY_RE = re.compile(r"\*?Model:\s*([^\n*]+)", re.IGNORECASE)


def _model_from_comments(comments: list[dict[str, Any]]) -> str | None:
    """Scan the issue's comments for a legacy '🤖 Model Attribution' block;
    return the model name if found (most-recent comment wins — later attributions
    supersede earlier ones)."""
    if not comments:
        return None
    for c in reversed(comments):
        body = (c or {}).get("body") or ""
        m = _MODEL_ATTR_RE.search(body)
        if m:
            return m.group(1).strip()
    return None


def _resolve_submitter(
    issue: dict[str, Any],
    *,
    body_submitter: str = "",
    comments: list[dict[str, Any]] | None = None,
) -> str:
    """Decide who the *author* of a submission is, per the user's rule:

      1. If the body explicitly names a real submitter, use that.
      2. Else if a comment contains a '🤖 Model Attribution' block, use that
         model name (these are the legacy llmXive automation-system ideas — the
         author IS the model that generated the idea).
      3. Else if the body has a legacy `*Model: <name>*` line, use that.
      4. Otherwise fall back to the GitHub issue creator (`issue.user.login`).

    The "Submitted via llmXive Dashboard" / "(unspecified)" / etc. body markers
    are treated as "no real submitter" — falling through to the model attribution
    or the issue author.
    """
    if body_submitter and not _looks_like_no_submitter(body_submitter):
        return body_submitter.strip().lstrip("@")
    body = issue.get("body") or ""
    # An explicit **Author**: <handle> line in the body (legacy ideas like #22).
    m_auth = re.search(r"\*\*Author\*\*:\s*([^\n]+)", body, re.IGNORECASE)
    if m_auth:
        name = m_auth.group(1).strip().lstrip("@")
        if name and not _looks_like_no_submitter(name):
            return name
    # comments may be in the passed `issue` dict (GitHub's expand-comments)
    cs = comments or (issue.get("comments") if isinstance(issue.get("comments"), list) else None) or []
    model = _model_from_comments(cs)
    if model:
        return model
    m = _LEGACY_MODEL_BODY_RE.search(body)
    if m:
        return m.group(1).strip()
    return (issue.get("user") or {}).get("login") or "anonymous"


# ── the agent ───────────────────────────────────────────────────────────────

class SubmissionIntakeAgent(Agent):
    """Tool-style agent — doesn't own a pipeline stage; one LLM call per
    feedback issue to produce a triage verdict."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:  # pragma: no cover - not used directly
        raise NotImplementedError("use process_submission_issue()")

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:  # pragma: no cover
        raise NotImplementedError("use process_submission_issue()")


# Valid research fields the LLM may classify a new project into (matches the
# prompt's "Valid fields" list). Used to validate the verdict's `field` value.
# Built from the librarian's canonical default-field list (single source of
# truth, Constitution Principle I — see #116) PLUS the broader
# submission-classification extras; do NOT re-type the canonical nine here.
VALID_FIELDS: frozenset[str] = frozenset(LIBRARIAN_DEFAULT_FIELDS) | {
    "astronomy", "environmental science", "economics", "engineering",
    "medicine", "philosophy", "linguistics", "other",
}


def _triage_feedback_llm(
    entry: AgentRegistryEntry,
    *,
    feedback: str,
    target_context: str,
    repo_root: Path,
) -> dict[str, str]:
    """One LLM call → a parsed {target, action, field, rationale} verdict.

    Raises on an unparseable response (the caller turns that into a `failed`).
    """
    valid_steps = ", ".join(_STEP_TO_STAGE.keys())
    system = render_prompt(PROMPT_PATH, {}, repo_root=None)  # package default
    user = (
        "## Feedback\n\n" + feedback + "\n\n"
        "## Target context\n\n" + (target_context or "(no target named)") + "\n\n"
        "## Valid pipeline step keys\n\n" + valid_steps + "\n\n"
        "Reply with exactly one line of JSON per the contract."
    )
    response = chat_with_fallback(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        default_backend=entry.default_backend.value,
        fallback_backends=[b.value for b in entry.fallback_backends],
        model=entry.default_model,
        max_tokens=512,
    )
    text = (response.text or "").strip()
    # Find the first {...} JSON object.
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON object in the verdict: {text[:200]!r}")
    verdict = json.loads(m.group(0))
    action = str(verdict.get("action", "")).strip()
    if action not in ("create-project", "acknowledge") and not action.startswith("route-to-"):
        raise ValueError(f"invalid action {action!r}")
    if action.startswith("route-to-"):
        step = action[len("route-to-"):]
        if step not in _STEP_TO_STAGE:
            raise ValueError(f"unknown route step {step!r}")
    # Validate the field (REQUIRED only when create-project; otherwise pass-through).
    field = str(verdict.get("field") or "").strip().lower()
    if action == "create-project" and field and field not in VALID_FIELDS:
        # Soft-validate: fall back to "other" rather than failing the whole triage.
        field = "other"
    return {
        "target": str(verdict.get("target") or "").strip(),
        "action": action,
        "field": field,
        "rationale": str(verdict.get("rationale") or "").strip(),
    }


def _create_brainstormed_project(
    repo: Path, *, title: str, content: str, submitter: str,
    field: str = "other", issue_number: int | None = None,
    paper_authors: list[str] | None = None,
) -> str:
    """Create a minimal brainstormed-stage project from submitted content.
    Reuses the project-id-lock + project_store.save pattern.

    Persists `github_issue: <url>` in the idea front-matter when `issue_number`
    is given, so `_issue_number_for_project` makes re-runs idempotent.
    """
    from llmxive.state.project_id_lock import next_available_proj_num, project_id_lock
    now = datetime.now(UTC)
    slug = _slugify(title or content[:60])
    with project_id_lock(repo):
        n = next_available_proj_num(repo_root=repo)
        pid = f"PROJ-{n:03d}-{slug}"
        project = Project(
            id=pid, title=(title or content[:80]).strip() or "Submitted idea",
            field=field, current_stage=Stage.BRAINSTORMED,
            points_research={}, points_paper={}, created_at=now, updated_at=now,
            artifact_hashes={},
        )
        project_store.save(project, repo_root=repo)
        idea_dir = repo / "projects" / pid / "idea"
        idea_dir.mkdir(parents=True, exist_ok=True)
    fm_lines = ["---", f"field: {field}", f"submitter: {submitter or 'website-submission'}"]
    if issue_number:
        fm_lines.append(f"github_issue: https://github.com/ContextLab/llmXive/issues/{issue_number}")
    if paper_authors:
        # Credit on a submitted paper goes to the paper's *authors* (parsed from
        # the paper itself), separately from the submitter who submitted it.
        # `web_data.py::_project_authors` reads this list and surfaces each as a
        # kind="human" author of the project (FR-007).
        fm_lines.append("paper_authors:")
        for a in paper_authors:
            fm_lines.append(f"  - {a}")
    fm_lines += ["---", "", f"# {project.title}", "", content, ""]
    (idea_dir / f"{slug}.md").write_text("\n".join(fm_lines), encoding="utf-8")
    return pid


def _move_staged_pdf(gh: GhFn, *, staged_path: str, dest_path: str) -> bool:
    """Move a staged PDF to its canonical home via the Contents API:
    read inbox copy → PUT at dest → DELETE inbox copy. Returns True on success.
    Idempotent: if dest already exists with content, treat as done."""
    # If the inbox copy is already gone and dest exists → already moved.
    try:
        dest = _gh_json(gh, "api", f"repos/{REPO}/contents/{dest_path}?ref=main")
        if dest and dest.get("content"):
            # dest exists — ensure the inbox copy is cleaned up, then done.
            try:
                src = _gh_json(gh, "api", f"repos/{REPO}/contents/{staged_path}?ref=main")
                if src and src.get("sha"):
                    gh("api", f"repos/{REPO}/contents/{staged_path}", "-X", "DELETE",
                       "-f", "message=submission-intake: remove staged inbox copy [skip ci]",
                       "-f", f"sha={src['sha']}", "-f", "branch=main")
            except Exception:
                pass
            return True
    except Exception:
        pass  # dest doesn't exist yet — proceed
    # Read the inbox copy.
    try:
        src = _gh_json(gh, "api", f"repos/{REPO}/contents/{staged_path}?ref=main")
    except Exception:
        return False
    if not src or not src.get("content"):
        return False
    content_b64 = src["content"].replace("\n", "")
    # PUT at dest.
    rc, _, _ = gh("api", f"repos/{REPO}/contents/{dest_path}", "-X", "PUT",
                  "-f", "message=submission-intake: file submitted paper [skip ci]",
                  "-f", f"content={content_b64}", "-f", "branch=main")
    if rc != 0:
        return False
    # DELETE the inbox copy.
    gh("api", f"repos/{REPO}/contents/{staged_path}", "-X", "DELETE",
       "-f", "message=submission-intake: remove staged inbox copy [skip ci]",
       "-f", f"sha={src['sha']}", "-f", "branch=main")
    return True


def _write_run_log_entry(repo_root: Path, entry: dict[str, Any]) -> None:
    """Append a single JSONL line to the canonical per-run log path.

    Mirrors `llmxive.agents.personality._write_run_log_entry` so the
    Activity tab on the website (which reads from
    `state/run-log/<YYYY-MM>/*.jsonl`) surfaces submission-intake events
    alongside personality and pipeline events. Before this helper landed,
    submission-intake invoked LLM triage and created projects, but its
    outcomes never appeared in the Activity feed — the only evidence was
    a GitHub Actions log and the new project's idea file.
    """
    import os
    now = datetime.now(UTC)
    log_dir = repo_root / "state" / "run-log" / now.strftime("%Y-%m")
    log_dir.mkdir(parents=True, exist_ok=True)
    rid = os.environ.get("GITHUB_RUN_ID") or f"local-{now.strftime('%Y%m%dT%H%M%SZ')}"
    log_path = log_dir / f"{rid}.jsonl"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


# Map IntakeResult.status → run-log outcome vocabulary used elsewhere in
# the pipeline (so the Activity tab's filters/labels work consistently).
_INTAKE_STATUS_TO_OUTCOME = {
    "ok": "committed",       # the LLM triage produced an actionable result
    "skipped": "no-op",       # already-closed issue / duplicate paper / etc.
    "failed": "failed",       # malformed labels / unhandled exception
}


def process_submission_issue(
    issue: dict[str, Any],
    *,
    repo_root: Path,
    gh: GhFn | None = None,
    registry_entry: AgentRegistryEntry | None = None,
) -> IntakeResult:
    gh = gh or _default_gh
    repo = Path(repo_root)
    number = int(issue.get("number", 0))
    body = issue.get("body") or ""
    author = (issue.get("user") or {}).get("login") or "anonymous"

    started = datetime.now(UTC)
    result: IntakeResult

    # Already closed? → nothing to do.
    if str(issue.get("state", "")).lower() == "closed":
        result = IntakeResult(status="skipped")
    else:
        subtype = _subtype(issue)
        if subtype is None:
            _comment(gh, number, "🤖 The submission-intake agent couldn't determine this issue's type — "
                     "it should be labelled `human-submission` plus exactly one of `feedback` / `new-paper`. "
                     "Leaving it open for a maintainer.")
            result = IntakeResult(status="failed", error="malformed labels")
        else:
            try:
                if subtype == "feedback":
                    result = _handle_feedback(issue, number, body, author, repo=repo, gh=gh, registry_entry=registry_entry)
                else:
                    result = _handle_new_paper(issue, number, body, author, repo=repo, gh=gh)
            except Exception as exc:
                _comment(gh, number, f"🤖 The submission-intake agent couldn't process this automatically: "
                         f"`{type(exc).__name__}: {exc}`. A maintainer will take a look. (It'll retry on the next cron tick.)")
                result = IntakeResult(status="failed", error=f"{type(exc).__name__}: {exc}")

    ended = datetime.now(UTC)
    # Surface the per-issue outcome on the Activity tab.
    try:
        _write_run_log_entry(repo, {
            "agent_name": "submission_intake",
            "model_kind": "deterministic_router",  # only the inner _triage_feedback_llm hits the LLM
            "project_id": result.target,            # may be None for skipped/failed
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "duration_s": (ended - started).total_seconds(),
            "outcome": _INTAKE_STATUS_TO_OUTCOME.get(result.status, result.status),
            "action": result.action,
            "issue_number": number,
            "issue_author": author,
            "comment_url": result.comment_url,
            "error": result.error,
        })
    except Exception as exc:
        print(f"[submissions] could not write run-log entry for #{number}: {exc!r}",
              file=__import__("sys").stderr)
    return result


def _fetch_comments(gh: GhFn, issue_number: int) -> list[dict[str, Any]]:
    """Fetch all comments on an issue (paginated)."""
    try:
        rc, out, _ = gh("api", "--paginate", f"repos/{REPO}/issues/{issue_number}/comments?per_page=100")
        if rc != 0 or not out.strip():
            return []
        # `--paginate` may concatenate JSON arrays; handle that.
        try:
            result: list[dict[str, Any]] = json.loads(out)
            return result
        except json.JSONDecodeError:
            out_combined: list[dict[str, Any]] = []
            for chunk in re.split(r"\]\s*\[", out):
                chunk = chunk.strip()
                if not chunk.startswith("["):
                    chunk = "[" + chunk
                if not chunk.endswith("]"):
                    chunk = chunk + "]"
                try:
                    out_combined.extend(json.loads(chunk))
                except json.JSONDecodeError:
                    pass
            return out_combined
    except Exception:
        return []


def _handle_feedback(issue: dict[str, Any], number: int, body: str, author: str, *, repo: Path, gh: GhFn, registry_entry: AgentRegistryEntry | None) -> IntakeResult:
    parsed = _parse_feedback_body(body)
    target_id = parsed["target_id"]
    content = parsed["content"] or body
    # Build the target context for the LLM.
    if target_id and _project_exists(repo, target_id):
        try:
            proj = project_store.load(target_id, repo_root=repo)
            target_context = (f"Project {proj.id} — “{proj.title}” — current stage: {proj.current_stage.value}. "
                              f"The feedback was filed against the “{parsed['target_kind'] or 'project'}” artifact "
                              f"at the “{parsed['target_stage'] or proj.current_stage.value}” stage.")
        except Exception:
            target_context = f"Project {target_id} (could not load full state)."
    elif target_id:
        target_context = f"A target “{target_id}” was named but no such project exists in state/projects/."
    else:
        target_context = "(no target named — likely a general remark or a new idea)"

    entry = registry_entry
    if entry is None:
        try:
            entry = registry_loader.get("submission_intake", repo_root=repo)
        except Exception:
            entry = registry_loader.get("submission_intake")  # package default
    verdict = _triage_feedback_llm(entry, feedback=content, target_context=target_context, repo_root=repo)
    action = verdict["action"]
    rationale = verdict["rationale"] or "(no rationale given)"

    if action.startswith("route-to-"):
        step = action[len("route-to-"):]
        # Idempotency: if we already commented on this on the project issue, skip.
        if not (target_id and _project_exists(repo, target_id)):
            # Routing to a project that doesn't exist — treat as acknowledge.
            cu = _comment(gh, number, f"🤖 Thanks for the feedback. The named target couldn't be matched to a "
                          f"project, so I've recorded it here for a maintainer.\n\n> {rationale}")
            _close_issue(gh, number)
            return IntakeResult(status="ok", action="acknowledged", target=None, comment_url=cu)
        proj_issue = _issue_number_for_project(repo, target_id)
        relay = (f"💬 **Human feedback relayed from the website** (submission #{number}, by @{author}):\n\n"
                 f"> {content}\n\n"
                 f"The submission-intake agent routed this to the **{step}** step ({rationale}). "
                 f"The next pipeline run for this project should pick it up.")
        if proj_issue:
            _comment(gh, proj_issue, relay)
        # Conservative state nudge: only if the project's current stage is at or
        # past the target step's stage AND moving back to it is a "revision"-ish
        # no-op-safe transition; otherwise just leave the comment. We do NOT
        # forcibly mutate state here — that's left to the next agent run / a
        # maintainer (err toward commenting, per the prompt).
        # (Intentionally a no-op on state for v1 — the comment is the signal.)
        cu = _comment(gh, number, f"🤖 Routed to **{target_id}** at the **{step}** step "
                      f"({'commented on its tracking issue' if proj_issue else 'noted on the project'}). "
                      f"{rationale}")
        _close_issue(gh, number)
        return IntakeResult(status="ok", action="routed-to-step", target=target_id, comment_url=cu)

    if action == "create-project":
        # Idempotency: if a project with a matching slug already exists for this
        # submission, skip. (We don't have a deterministic id; best-effort: check
        # whether this issue is already referenced by some project's idea
        # front-matter — if so, it was handled.)
        for pdir in (repo / "projects").glob("PROJ-*"):
            if _issue_number_for_project(repo, pdir.name) == number:
                return IntakeResult(status="skipped", target=pdir.name)
        # Title: prefer the issue title (cleaner than the body's first line for
        # legacy idea submissions); fall back to the body's first line.
        title = (issue.get("title") or "").strip()
        # strip our own automated-test prefixes / common noise.
        title = re.sub(r"^\[automated test[^\]]*\]\s*", "", title, flags=re.IGNORECASE).strip()
        if not title:
            title = (content.splitlines() or [""])[0].strip().lstrip("#").strip()
        # Resolve the *author* per the user's rule: a real submitter named in
        # the body wins; else a "🤖 Model Attribution" comment names the model;
        # else the GitHub issue creator. (For ideas submitted via the legacy
        # automation system, the author IS the model that generated them.)
        comments = _fetch_comments(gh, number)
        submitter = _resolve_submitter(issue, body_submitter=parsed.get("submitter", ""), comments=comments)
        # Resolve the research field, in priority order:
        #   1. the LLM verdict's `field` (the model just classified it; trusted)
        #   2. an explicit **Field**: line in the body (legacy ideas have one)
        #   3. fallback "other"
        field_m = re.search(r"\*\*Field\*\*:\s*([^\n*]+)", body, re.IGNORECASE)
        body_field = (field_m.group(1).strip().lower() if field_m else "")
        field = verdict.get("field") or body_field or "other"
        if field not in VALID_FIELDS:
            field = "other"
        pid = _create_brainstormed_project(repo, title=title[:200], content=content,
                                           submitter=submitter, field=field, issue_number=number)
        cu = _comment(gh, number, f"🤖 This looked like a brand-new research idea, so I created "
                      f"**{pid}** (brainstormed stage) from it — submitter: `{submitter}`. The Flesh-Out "
                      f"agent will expand it on the next pipeline cycle.\n\n> {rationale}")
        _close_issue(gh, number)
        return IntakeResult(status="ok", action="created-project", target=pid, comment_url=cu)

    # acknowledge
    cu = _comment(gh, number, f"🤖 Thanks for the feedback! {rationale} (Recorded — no specific pipeline "
                  f"action needed right now.)")
    _close_issue(gh, number)
    return IntakeResult(status="ok", action="acknowledged", target=target_id or None, comment_url=cu)


def _handle_new_paper(issue: dict[str, Any], number: int, body: str, author: str, *, repo: Path, gh: GhFn) -> IntakeResult:
    parsed = _parse_new_paper_body(body)
    url = parsed["url"]
    staged = parsed["staged_file"]
    title_seed = (issue.get("title") or "submitted paper").replace("New paper (link):", "").replace("New paper (upload):", "").strip()

    # Idempotency: if this issue is already referenced by a project, skip.
    for pdir in (repo / "projects").glob("PROJ-*"):
        if _issue_number_for_project(repo, pdir.name) == number:
            return IntakeResult(status="skipped", target=pdir.name)

    # Dedup by arXiv ID: a single paper can be filed multiple times (e.g. the
    # HF-daily-papers cron picks up the same paper on consecutive days if it
    # remained popular). Without this check we end up with PROJ-566, PROJ-578,
    # PROJ-583 all pointing at the same MinT paper. Scan existing
    # paper/metadata.json::arxiv_id; if a project already owns this arXiv ID,
    # comment on the duplicate issue and return skipped.
    incoming_arxiv = None
    if url:
        _m = re.search(r"arxiv\.org/(?:abs|pdf|html|e-print)/([0-9]{4}\.[0-9]{4,6})", url)
        if _m:
            incoming_arxiv = _m.group(1)
    if incoming_arxiv:
        for pdir in (repo / "projects").glob("PROJ-*"):
            meta_path = pdir / "paper" / "metadata.json"
            if not meta_path.is_file():
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(meta, dict) and meta.get("arxiv_id") == incoming_arxiv:
                # Found a duplicate — leave a breadcrumb on the issue and skip.
                try:
                    gh("issue", "comment", str(number), "--body",
                       f"This paper (arXiv:{incoming_arxiv}) is already tracked by "
                       f"[{pdir.name}](../tree/main/projects/{pdir.name}). "
                       f"Closing as a duplicate.")
                    gh("issue", "close", str(number),
                       "--comment", "duplicate of arXiv:" + incoming_arxiv,
                       "--reason", "not planned")
                except Exception:
                    # If gh comms fail, still return skipped — the dedup
                    # decision is the user-visible action.
                    pass
                return IntakeResult(status="skipped", target=pdir.name,
                                    error=f"duplicate of arXiv:{incoming_arxiv} at {pdir.name}")

    # Create-or-link a project. For a submitted paper we create a brainstormed
    # project that records the source; a maintainer / the pipeline can promote
    # it. (Reusing the same minimal-project path as feedback create-project —
    # the paper-init pipeline picks up properly-staged projects later.)
    content_lines = ["A paper was submitted via the website for consideration / review.", ""]
    if url:
        content_lines.append(f"Source URL: {url}")
    if staged:
        content_lines.append(f"Submitted PDF (staged): `{staged}`")
    # Resolve the *submitter* (who submitted it) — credit for the act of
    # submitting goes here, but the paper's authors are tracked separately
    # in `paper_authors` (parsed from the paper itself when possible).
    comments = _fetch_comments(gh, number)
    submitter = _resolve_submitter(issue, body_submitter=parsed.get("submitter", ""), comments=comments)
    # Best-effort paper-author + title + field parsing from arXiv (cheap public
    # API, no auth). For non-arXiv URLs / uploaded PDFs the paper-pipeline's
    # tooling parses authors later — a missing lookup never blocks intake.
    paper_authors, fetched_title, fetched_field, fetched_abstract = (
        _arxiv_metadata(url) if url else ([], None, None, None)
    )
    if paper_authors:
        content_lines.append("Paper authors (from arXiv): " + ", ".join(paper_authors))
    title = (fetched_title or title_seed or "Submitted paper").strip()
    field = (fetched_field if (fetched_field and fetched_field in VALID_FIELDS) else "other")
    content_lines += ["", f"Submitted by: {submitter}", "", f"(Intake from human-submission issue #{number}.)"]
    pid = _create_brainstormed_project(repo, title=title[:200] or "Submitted paper",
                                       content="\n".join(content_lines),
                                       submitter=submitter, field=field,
                                       issue_number=number, paper_authors=paper_authors)

    # ── arXiv flow: fetch the .tex source, parse for code/data, stage under
    #    paper/source/, then transition the project to paper_review so the 12
    #    paper-stage specialist reviewers run on the next pipeline tick. The
    #    user's rule for submitted papers: they skip the research + drafting
    #    stages (the work is already done) and go straight to review. The
    #    `speckit_paper_dir` validator only kicks in at paper_specified..
    #    paper_complete, so a project at paper_review can have it unset.
    arxiv_id = None
    if url:
        am = re.search(r"arxiv\.org/(?:abs|pdf|html|e-print)/([0-9]{4}\.[0-9]{4,6})", url)
        if am:
            arxiv_id = am.group(1)
    arxiv_status = "skipped"
    if arxiv_id:
        paper_dir = repo / "projects" / pid / "paper"
        source_dir = paper_dir / "source"
        fetch = _fetch_arxiv_source(arxiv_id, source_dir)
        if fetch["ok"]:
            ext = _parse_tex_external_resources(source_dir)
            # Write metadata.json + external_resources.md
            (paper_dir / "metadata.json").write_text(json.dumps({
                "arxiv_id": arxiv_id,
                "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
                "title": title, "authors": paper_authors, "submitter": submitter,
                # The paper's actual abstract, surfaced on the dashboard card
                # via _project_description in web_data.py. Whitespace-normalized.
                "abstract": fetched_abstract,
                "submitted_via": f"llmXive dashboard, GitHub issue #{number}",
                "license": "arXiv Non-exclusive Distribution License",
                "license_url": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/",
                "code": ext["code"], "data": ext["data"],
                "toplevel_tex": fetch["toplevel_tex"],
                "source_files": fetch["files"],
            }, indent=2), encoding="utf-8")
            ext_lines = ["# External resources", "", "This project was created from an arXiv-submitted paper.", "",
                         "## Source", "", f"- **arXiv**: [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})",
                         "- **License**: arXiv Non-exclusive Distribution License", "", "## Code"]
            ext_lines += [f"- {u}" for u in ext["code"]] or ["- (none found in the paper source)"]
            if ext["data"]:
                ext_lines += ["", "## Data"] + [f"- {u}" for u in ext["data"]]
            (paper_dir / "external_resources.md").write_text("\n".join(ext_lines) + "\n", encoding="utf-8")
            # Transition the project to paper_review so the reviewers pick it up.
            try:
                p = project_store.load(pid, repo_root=repo)
                p = p.model_copy(update={"current_stage": Stage.PAPER_REVIEW,
                                          "updated_at": datetime.now(UTC)})
                project_store.save(p, repo_root=repo)
                arxiv_status = "staged"
            except Exception as exc:
                arxiv_status = f"staged but couldn't transition: {exc}"
        else:
            arxiv_status = f"fetch failed: {fetch.get('error')}"

    # If a PDF was staged, move it to the project's canonical home.
    moved = None
    if staged and staged.startswith(INBOX_DIR + "/"):
        base = staged.rsplit("/", 1)[-1]
        dest = f"projects/{pid}/paper/submitted/{base}"
        ok = _move_staged_pdf(gh, staged_path=staged, dest_path=dest)
        moved = dest if ok else None

    stage_word = "paper_review (source fetched + staged)" if arxiv_status == "staged" else "brainstormed"
    bits = [f"created **{pid}** ({stage_word})"]
    if url:
        bits.append(f"recorded the source URL ({url})")
    if moved:
        bits.append(f"filed the uploaded PDF at `{moved}`")
    elif staged:
        bits.append(f"(couldn't move the staged PDF `{staged}` automatically — a maintainer should)")
    if arxiv_id and arxiv_status != "staged":
        bits.append(f"arXiv source: {arxiv_status}")
    cu = _comment(gh, number, "🤖 Thanks for the submission — " + "; ".join(bits) + ". "
                  "The pipeline / a maintainer will review it from there.")
    _close_issue(gh, number)
    return IntakeResult(status="ok", action="filed-paper", target=pid, comment_url=cu)


__all__ = [
    "IntakeResult",
    "SubmissionIntakeAgent",
    "process_submission_issue",
]
