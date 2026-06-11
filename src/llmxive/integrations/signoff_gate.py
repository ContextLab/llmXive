"""Publication sign-off by lightweight maintainer vote (spec 023 / US5,
FR-019..021; contract:
specs/023-pipeline-e2e-completion/contracts/signoff-issue.md).

The ONE sanctioned human decision in the pipeline. When a paper reaches
``awaiting_publication_signoff`` with its checks green, the gate opens a
tracking issue tagging every maintainer; maintainers vote with a 👍/👎
reaction or an ``approve`` / ``reject: <reason>`` comment. The scheduled
poll lane parses the votes:

* approval → the FR-054 sign-off record is written (the publisher's
  existing self-gate), the publisher runs (idempotent DOI mint), the
  project posts, and the issue closes with the DOI;
* rejection → the reason becomes review feedback via the US1 revision
  machinery (``kickback_to_revision_spec``) and the paper re-enters
  ``paper_review``;
* silence → periodic reminder comments; the project stays parked with
  zero scheduler load (``awaiting_publication_signoff`` is never picked).

Decisions are idempotent and ledgered in
``projects/<id>/paper/signoff.yaml`` — the local ledger is authoritative
once a decision is recorded, so edited/deleted issues can never double-
mint. Any maintainer rejection takes precedence over approvals; the
conflict is recorded on the issue. Non-maintainer responses are ignored
for decision purposes.

GitHub calls go through an injected ``gh`` callable (``(rc, out, err)``
tuple protocol) so tests fake the subprocess boundary.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from llmxive.config import repo_root as _repo_root
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

logger = logging.getLogger(__name__)

GITHUB_REPO = "ContextLab/llmXive"
SIGNOFF_LABEL = "publication-signoff"
REMINDER_INTERVAL_HOURS = 72.0
MAINTAINERS_ENV = "LLMXIVE_MAINTAINERS"

_APPROVE_RE = re.compile(r"^\s*approve\b", re.IGNORECASE)
_REJECT_RE = re.compile(r"^\s*reject\s*:?\s*(?P<reason>.*)$", re.IGNORECASE | re.DOTALL)


def _default_gh(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _ledger_path(project_id: str, *, repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "projects" / project_id / "paper" / "signoff.yaml"


def read_ledger(project_id: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    p = _ledger_path(project_id, repo_root=repo_root)
    if not p.is_file():
        return {}
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _write_ledger(
    project_id: str, data: dict[str, Any], *, repo_root: Path | None = None
) -> Path:
    p = _ledger_path(project_id, repo_root=repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return p


def maintainers(*, gh=None) -> set[str]:
    """Voter-identity source (FR-020): the ``LLMXIVE_MAINTAINERS`` env list
    when set, else the repo's push-permission collaborators."""
    env = os.environ.get(MAINTAINERS_ENV, "").strip()
    if env:
        return {m.strip() for m in env.split(",") if m.strip()}
    gh = gh or _default_gh
    rc, out, err = gh(
        "api", "--paginate", f"repos/{GITHUB_REPO}/collaborators?per_page=100"
    )
    if rc != 0:
        logger.warning("could not list collaborators: %s", err.strip())
        return set()
    names: set[str] = set()
    try:
        for chunk in re.split(r"\]\s*\[", out.strip()):
            if not chunk.startswith("["):
                chunk = "[" + chunk
            if not chunk.endswith("]"):
                chunk = chunk + "]"
            for c in json.loads(chunk):
                perms = c.get("permissions") or {}
                if perms.get("push") or perms.get("admin"):
                    names.add(str(c.get("login", "")))
    except json.JSONDecodeError:
        logger.warning("could not parse collaborators response")
    names.discard("")
    return names


def _issue_body(project: Project, *, repo_root: Path, maint: set[str]) -> str:
    pid = project.id
    paper_dir = repo_root / "projects" / pid / "paper"
    meta_path = paper_dir / "metadata.json"
    abstract = ""
    title = project.title
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            title = str(meta.get("title") or title)
            abstract = str(meta.get("abstract") or "")[:800]
        except json.JSONDecodeError:
            pass
    base = f"https://github.com/{GITHUB_REPO}/blob/main"
    tags = " ".join(f"@{m}" for m in sorted(maint)) or "(no maintainers resolved)"
    status_note = ""
    status_path = repo_root / "state" / "paper_status" / f"{pid}.json"
    if status_path.is_file():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status_note = f"\n- Compile/audit status: `{status.get('status', 'unknown')}`"
        except json.JSONDecodeError:
            pass
    return (
        f"{tags}\n\n"
        f"**{title}** ({pid}) has passed every automated gate — unanimous "
        "paper-review panel acceptance, claim/citation verification, and "
        "compile checks — and awaits the publication decision.\n\n"
        f"- 📄 [Compiled PDF]({base}/projects/{pid}/paper/pdf/main.pdf)\n"
        f"- 📁 [Paper source]({base}/projects/{pid}/paper/source/)\n"
        f"- 🔍 [Review trail]({base}/projects/{pid}/paper/reviews/)\n"
        f"- 🗂 [Project](https://contextlab.github.io/llmXive/project.html?id={pid})"
        f"{status_note}\n\n"
        + (f"**Abstract**: {abstract}\n\n" if abstract else "")
        + "## How to vote (maintainers only)\n\n"
        "- **Approve**: react 👍 on this issue, or comment `approve` — the "
        "DOI is minted and the paper posts automatically.\n"
        "- **Reject**: comment `reject: <reason>` — the reason routes into "
        "the automated revision loop. (A bare 👎 prompts for a reason and "
        "does not decide.)\n\n"
        "Any maintainer rejection takes precedence over approvals. "
        "Non-maintainer responses are welcome but do not decide. "
        "This issue is the durable sign-off record (spec 023 / FR-019..021)."
    )


def ensure_signoff_issue(
    project: Project, *, repo_root: Path | None = None, gh=None
) -> int | None:
    """Open (or reuse) the sign-off issue for a gate-ready paper (FR-019).

    Fail-fast preconditions (Constitution V): correct stage and a compiled
    PDF on disk; a failing paper-status record blocks the gate.
    Returns the issue number, or None when preconditions fail or GitHub is
    unreachable.
    """
    gh = gh or _default_gh
    repo = repo_root or _repo_root()
    if project.current_stage != Stage.AWAITING_PUBLICATION_SIGNOFF:
        logger.info(
            "%s not at awaiting_publication_signoff; gate not opened", project.id
        )
        return None
    pdf = repo / "projects" / project.id / "paper" / "pdf" / "main.pdf"
    if not pdf.is_file():
        logger.warning("%s: no compiled PDF at %s; gate not opened", project.id, pdf)
        return None
    status_path = repo / "state" / "paper_status" / f"{project.id}.json"
    if status_path.is_file():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if status.get("failure"):
                logger.warning(
                    "%s: paper status carries a failure report; gate not opened",
                    project.id,
                )
                return None
        except json.JSONDecodeError:
            pass
    ledger = read_ledger(project.id, repo_root=repo)
    if ledger.get("issue_number") and ledger.get("decision") in (None, "pending"):
        return int(ledger["issue_number"])
    if ledger.get("decision") in ("approved", "rejected"):
        # Decided ledgers are authoritative (idempotence) — never reopen.
        return int(ledger.get("issue_number") or 0) or None
    maint = maintainers(gh=gh)
    if not maint:
        logger.warning("%s: no maintainers resolvable; gate not opened", project.id)
        return None
    title = f"[sign-off] {project.id} — {project.title}"[:240]
    rc, out, err = gh(
        "api", f"repos/{GITHUB_REPO}/issues", "-X", "POST",
        "-f", f"title={title}",
        "-f", f"body={_issue_body(project, repo_root=repo, maint=maint)}",
        "-f", f"labels[]={SIGNOFF_LABEL}",
    )
    if rc != 0:
        logger.warning("%s: sign-off issue creation failed: %s", project.id, err.strip())
        return None
    try:
        number = int(json.loads(out).get("number", 0))
    except (json.JSONDecodeError, ValueError):
        return None
    _write_ledger(
        project.id,
        {
            "issue_number": number,
            "decision": "pending",
            "decided_by": None,
            "rejection_reason": None,
            "doi": None,
            "reminders_sent": [],
            "opened_at": datetime.now(UTC).isoformat(),
        },
        repo_root=repo,
    )
    logger.info("%s: sign-off issue #%d opened", project.id, number)
    return number


def _collect_votes(
    issue_number: int, maint: set[str], *, gh
) -> tuple[list[str], list[tuple[str, str | None]], bool]:
    """Returns (approvals, rejections[(user, reason|None)], bare_thumbsdown)."""
    approvals: list[str] = []
    rejections: list[tuple[str, str | None]] = []
    bare_down = False
    rc, out, _err = gh(
        "api", "--paginate",
        f"repos/{GITHUB_REPO}/issues/{issue_number}/reactions?per_page=100",
    )
    if rc == 0:
        try:
            for r in json.loads(out) if out.strip().startswith("[") else []:
                user = str((r.get("user") or {}).get("login", ""))
                if user not in maint:
                    continue
                if r.get("content") == "+1":
                    approvals.append(user)
                elif r.get("content") == "-1":
                    rejections.append((user, None))
                    bare_down = True
        except json.JSONDecodeError:
            pass
    rc, out, _err = gh(
        "api", "--paginate",
        f"repos/{GITHUB_REPO}/issues/{issue_number}/comments?per_page=100",
    )
    if rc == 0:
        try:
            for c in json.loads(out) if out.strip().startswith("[") else []:
                user = str((c.get("user") or {}).get("login", ""))
                if user not in maint:
                    continue
                body = str(c.get("body") or "")
                m = _REJECT_RE.match(body)
                if m:
                    reason = m.group("reason").strip() or None
                    rejections.append((user, reason))
                    if reason:
                        bare_down = False
                elif _APPROVE_RE.match(body):
                    approvals.append(user)
        except json.JSONDecodeError:
            pass
    return approvals, rejections, bare_down


def _comment(issue_number: int, body: str, *, gh) -> None:
    gh(
        "api", f"repos/{GITHUB_REPO}/issues/{issue_number}/comments",
        "-X", "POST", "-f", f"body={body}",
    )


def _close_issue(issue_number: int, *, gh) -> None:
    gh(
        "api", f"repos/{GITHUB_REPO}/issues/{issue_number}",
        "-X", "PATCH", "-f", "state=closed",
    )


def _route_rejection(
    project: Project, *, reason: str, rejected_by: str, repo_root: Path
) -> None:
    """FR-020: convert the maintainer's reason into review feedback via the
    US1 revision machinery and re-enter the revision loop."""
    from llmxive.convergence.revision_adapter import kickback_to_revision_spec
    from llmxive.convergence.types import Concern, KickbackRecord, Severity
    from llmxive.speckit._publication_signoff import clear_signoff

    concern = Concern(
        id="maintrejected",
        reviewer="maintainer-signoff",
        severity=Severity.WRITING,
        artifact=f"projects/{project.id}/paper/source/",
        location="publication sign-off",
        text=f"Maintainer @{rejected_by} rejected publication: {reason}",
        round=1,
    )
    kb = KickbackRecord(
        from_stage="paper_review",
        to_stage="paper_tasked",
        worst_severity=Severity.WRITING,
        unresolved_concerns=[concern],
        artifact_links=[f"projects/{project.id}/paper/source/"],
        reason=f"publication sign-off rejected by @{rejected_by}: {reason}",
    )
    spec_dir = kickback_to_revision_spec(kb, project_id=project.id, repo_root=repo_root)
    rel = spec_dir.relative_to(repo_root)
    clear_signoff(repo_root / "projects" / project.id / ".specify" / "memory")
    project_store.save(
        project.model_copy(
            update={
                "current_stage": Stage.PAPER_REVIEW,
                "revision_spec_path": str(rel),
                "updated_at": datetime.now(UTC),
            }
        ),
        repo_root=repo_root,
    )


def poll_project(
    project: Project,
    *,
    repo_root: Path | None = None,
    gh=None,
    now: datetime | None = None,
) -> str:
    """Process one gate-parked project; returns the action taken
    (``opened`` / ``approved`` / ``rejected`` / ``reminded`` / ``waiting``
    / ``already-decided`` / ``skipped``)."""
    gh = gh or _default_gh
    repo = repo_root or _repo_root()
    now = now or datetime.now(UTC)
    ledger = read_ledger(project.id, repo_root=repo)
    if ledger.get("decision") in ("approved", "rejected"):
        return "already-decided"
    issue_number = ledger.get("issue_number")
    if not issue_number:
        issue_number = ensure_signoff_issue(project, repo_root=repo, gh=gh)
        if issue_number is None:
            return "skipped"
        return "opened"
    issue_number = int(issue_number)
    maint = maintainers(gh=gh)
    approvals, rejections, bare_down = _collect_votes(issue_number, maint, gh=gh)

    reasoned = [(u, r) for (u, r) in rejections if r]
    if reasoned:
        user, reason = reasoned[0]
        if approvals:
            _comment(
                issue_number,
                f"Conflicting votes recorded: approval(s) from "
                f"{', '.join('@' + a for a in sorted(set(approvals)))} and a "
                f"rejection from @{user}. Per the gate protocol, the "
                "rejection takes precedence.",
                gh=gh,
            )
        _route_rejection(project, reason=reason, rejected_by=user, repo_root=repo)
        ledger.update(
            decision="rejected", decided_by=user, rejection_reason=reason,
            decided_at=now.isoformat(),
        )
        _write_ledger(project.id, ledger, repo_root=repo)
        _comment(
            issue_number,
            f"Rejection by @{user} recorded — the reason has been converted "
            "into review feedback and the paper re-entered the automated "
            "revision loop. A fresh sign-off issue will open when it passes "
            "review again.",
            gh=gh,
        )
        _close_issue(issue_number, gh=gh)
        return "rejected"

    if bare_down and not ledger.get("reason_prompted"):
        _comment(
            issue_number,
            "A maintainer 👎 was recorded without a reason. Per the gate "
            "protocol a bare 👎 does not decide — please comment "
            "`reject: <reason>` so the revision loop can act on it (or 👍 / "
            "`approve` to proceed).",
            gh=gh,
        )
        ledger["reason_prompted"] = True
        _write_ledger(project.id, ledger, repo_root=repo)
        return "waiting"

    if approvals:
        approver = sorted(set(approvals))[0]
        from llmxive.speckit._publication_signoff import write_signoff

        memory_dir = repo / "projects" / project.id / ".specify" / "memory"
        write_signoff(
            memory_dir,
            who=approver,
            what=f"sign-off issue #{issue_number} approval (spec 023 gate)",
            recorded_by_gh_user=approver,
        )
        from llmxive.pipeline.graph import run_one_step

        updated = run_one_step(project, repo_root=repo)
        if updated.current_stage == Stage.POSTED:
            from llmxive.state import publication as pub_state

            pub = pub_state.load(project.id, repo_root=repo)
            doi = pub.doi if pub else None
            ledger.update(
                decision="approved", decided_by=approver, doi=doi,
                decided_at=now.isoformat(),
            )
            _write_ledger(project.id, ledger, repo_root=repo)
            _comment(
                issue_number,
                f"Approved by @{approver}. Published: DOI "
                f"[{doi}](https://doi.org/{doi}). 🎉",
                gh=gh,
            )
            _close_issue(issue_number, gh=gh)
            return "approved"
        # Publisher didn't reach POSTED this tick (transient failure or
        # compile issue). The FR-054 record is in place; the idempotent
        # publisher retries on the next poll — never a second mint.
        logger.warning(
            "%s: approval recorded but publisher ended at %s; will retry",
            project.id, updated.current_stage.value,
        )
        return "waiting"

    reminders = [
        datetime.fromisoformat(str(r)) for r in ledger.get("reminders_sent") or []
    ]
    anchor = max(
        reminders
        + [datetime.fromisoformat(str(ledger.get("opened_at", now.isoformat())))]
    )
    if (now - anchor) >= timedelta(hours=REMINDER_INTERVAL_HOURS):
        maint_tags = " ".join(f"@{m}" for m in sorted(maint))
        _comment(
            issue_number,
            f"Reminder: this paper awaits a publication decision. {maint_tags} "
            "— react 👍 / comment `approve`, or `reject: <reason>`.",
            gh=gh,
        )
        ledger.setdefault("reminders_sent", []).append(now.isoformat())
        _write_ledger(project.id, ledger, repo_root=repo)
        return "reminded"
    return "waiting"


def poll_all(*, repo_root: Path | None = None, gh=None) -> dict[str, str]:
    """Poll every project parked at the gate (the scheduled lane entry)."""
    repo = repo_root or _repo_root()
    actions: dict[str, str] = {}
    for project in project_store.list_all(repo_root=repo):
        if project.current_stage != Stage.AWAITING_PUBLICATION_SIGNOFF:
            continue
        try:
            actions[project.id] = poll_project(project, repo_root=repo, gh=gh)
        except Exception as exc:
            logger.warning("sign-off poll failed for %s: %s", project.id, exc)
            actions[project.id] = f"error: {exc}"
    return actions


__all__ = [
    "GITHUB_REPO",
    "REMINDER_INTERVAL_HOURS",
    "SIGNOFF_LABEL",
    "ensure_signoff_issue",
    "maintainers",
    "poll_all",
    "poll_project",
    "read_ledger",
]
