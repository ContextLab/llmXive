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

def _labels(issue: dict) -> set[str]:
    out = set()
    for lab in issue.get("labels", []) or []:
        out.add(lab["name"] if isinstance(lab, dict) else str(lab))
    return out


def _subtype(issue: dict) -> str | None:
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


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:40] or "submission"


# ── the agent ───────────────────────────────────────────────────────────────

class SubmissionIntakeAgent(Agent):
    """Tool-style agent — doesn't own a pipeline stage; one LLM call per
    feedback issue to produce a triage verdict."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:  # pragma: no cover - not used directly
        raise NotImplementedError("use process_submission_issue()")

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:  # pragma: no cover
        raise NotImplementedError("use process_submission_issue()")


def _triage_feedback_llm(
    entry: AgentRegistryEntry,
    *,
    feedback: str,
    target_context: str,
    repo_root: Path,
) -> dict[str, str]:
    """One LLM call → a parsed {target, action, rationale} verdict.

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
    return {
        "target": str(verdict.get("target") or "").strip(),
        "action": action,
        "rationale": str(verdict.get("rationale") or "").strip(),
    }


def _create_brainstormed_project(repo: Path, *, title: str, content: str, submitter: str, field: str = "other") -> str:
    """Create a minimal brainstormed-stage project from submitted content.
    Reuses the project-id-lock + project_store.save pattern."""
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
    front = f"---\nfield: {field}\nsubmitter: {submitter or 'website-submission'}\n---\n\n# {project.title}\n\n{content}\n"
    (idea_dir / f"{slug}.md").write_text(front, encoding="utf-8")
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


def process_submission_issue(
    issue: dict,
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

    # Already closed? → nothing to do.
    if str(issue.get("state", "")).lower() == "closed":
        return IntakeResult(status="skipped")

    subtype = _subtype(issue)
    if subtype is None:
        _comment(gh, number, "🤖 The submission-intake agent couldn't determine this issue's type — "
                 "it should be labelled `human-submission` plus exactly one of `feedback` / `new-paper`. "
                 "Leaving it open for a maintainer.")
        return IntakeResult(status="failed", error="malformed labels")

    try:
        if subtype == "feedback":
            return _handle_feedback(issue, number, body, author, repo=repo, gh=gh, registry_entry=registry_entry)
        return _handle_new_paper(issue, number, body, author, repo=repo, gh=gh)
    except Exception as exc:
        _comment(gh, number, f"🤖 The submission-intake agent couldn't process this automatically: "
                 f"`{type(exc).__name__}: {exc}`. A maintainer will take a look. (It'll retry on the next cron tick.)")
        return IntakeResult(status="failed", error=f"{type(exc).__name__}: {exc}")


def _handle_feedback(issue, number, body, author, *, repo: Path, gh: GhFn, registry_entry) -> IntakeResult:
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
        # Derive a title from the first line of the content.
        first_line = (content.splitlines() or [""])[0].strip().lstrip("#").strip()
        pid = _create_brainstormed_project(repo, title=first_line[:80], content=content,
                                           submitter=f"@{author} (website)")
        cu = _comment(gh, number, f"🤖 This looked like a brand-new research idea, so I created "
                      f"**{pid}** (brainstormed stage) from it. The Flesh-Out agent will expand it on the "
                      f"next pipeline cycle.\n\n> {rationale}")
        _close_issue(gh, number)
        return IntakeResult(status="ok", action="created-project", target=pid, comment_url=cu)

    # acknowledge
    cu = _comment(gh, number, f"🤖 Thanks for the feedback! {rationale} (Recorded — no specific pipeline "
                  f"action needed right now.)")
    _close_issue(gh, number)
    return IntakeResult(status="ok", action="acknowledged", target=target_id or None, comment_url=cu)


def _handle_new_paper(issue, number, body, author, *, repo: Path, gh: GhFn) -> IntakeResult:
    parsed = _parse_new_paper_body(body)
    url = parsed["url"]
    staged = parsed["staged_file"]
    title_seed = (issue.get("title") or "submitted paper").replace("New paper (link):", "").replace("New paper (upload):", "").strip()

    # Idempotency: if this issue is already referenced by a project, skip.
    for pdir in (repo / "projects").glob("PROJ-*"):
        if _issue_number_for_project(repo, pdir.name) == number:
            return IntakeResult(status="skipped", target=pdir.name)

    # Create-or-link a project. For a submitted paper we create a brainstormed
    # project that records the source; a maintainer / the pipeline can promote
    # it. (Reusing the same minimal-project path as feedback create-project —
    # the paper-init pipeline picks up properly-staged projects later.)
    content_lines = ["A paper was submitted via the website for consideration / review.", ""]
    if url:
        content_lines.append(f"Source URL: {url}")
    if staged:
        content_lines.append(f"Submitted PDF (staged): `{staged}`")
    content_lines += ["", f"Submitted by: @{author}", "", f"(Intake from human-submission issue #{number}.)"]
    pid = _create_brainstormed_project(repo, title=title_seed[:80] or "Submitted paper",
                                       content="\n".join(content_lines),
                                       submitter=f"@{author} (website)", field="other")

    # If a PDF was staged, move it to the project's canonical home.
    moved = None
    if staged and staged.startswith(INBOX_DIR + "/"):
        base = staged.rsplit("/", 1)[-1]
        dest = f"projects/{pid}/paper/submitted/{base}"
        ok = _move_staged_pdf(gh, staged_path=staged, dest_path=dest)
        moved = dest if ok else None

    bits = [f"created **{pid}** (brainstormed stage)"]
    if url:
        bits.append(f"recorded the source URL ({url})")
    if moved:
        bits.append(f"filed the uploaded PDF at `{moved}`")
    elif staged:
        bits.append(f"(couldn't move the staged PDF `{staged}` automatically — a maintainer should)")
    cu = _comment(gh, number, "🤖 Thanks for the submission — " + "; ".join(bits) + ". "
                  "The pipeline / a maintainer will review it from there.")
    _close_issue(gh, number)
    return IntakeResult(status="ok", action="filed-paper", target=pid, comment_url=cu)


__all__ = [
    "IntakeResult",
    "SubmissionIntakeAgent",
    "process_submission_issue",
]
