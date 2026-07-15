"""Exhaustion-evidence escalation records + engine-failure issue filing
(spec 023 / US4, FR-016 + FR-017; contract:
specs/023-pipeline-e2e-completion/contracts/escalation-record.md).

Routine human escalation is a deal-breaker for an automated-science
system. The discipline enforced here:

* A project may park for a human ONLY with a record proving a bounded
  automated loop was exhausted — :func:`write_record` fail-fast-validates
  ``rounds_used >= bound`` at write time (Constitution V).
* Unexpected ENGINE failures never park the project: they file (or
  reuse) a tracked GitHub issue with the failure evidence via
  :func:`file_engine_failure_issue`, and the project stays schedulable.
* Open records aggregate into a single periodic digest issue
  (:func:`update_digest`) — no per-project pings.

The GitHub calls go through an injected ``gh`` callable with the same
``(returncode, stdout, stderr)`` protocol as
``llmxive.integrations.issues._gh`` so tests substitute a recording fake
at the subprocess boundary.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

from llmxive.config import repo_root as _repo_root
from llmxive.state._io import atomic_write_text

logger = logging.getLogger(__name__)

GITHUB_REPO = "ContextLab/llmXive"

_ESCALATIONS_REL = Path("state") / "escalations"
_ISSUE_LEDGER_REL = _ESCALATIONS_REL / "issues"

DIGEST_TITLE = "Escalation digest — bounded automation exhausted"
ENGINE_FAILURE_LABEL = "engine-failure"
DIGEST_LABEL = "escalation-digest"


class EscalationValidationError(ValueError):
    """A record was attempted before its bounded loop was exhausted."""


@dataclass
class EscalationRecord:
    """One exhausted-automation escalation (contract: escalation-record.md)."""

    project_id: str
    stage: str
    loop: str
    bound: int
    rounds_used: int
    attempts: list[dict[str, str]] = field(default_factory=list)
    recommended_action: str = ""
    timestamp: str = ""
    digest_id: str | None = None

    def validate(self) -> None:
        if self.rounds_used < self.bound:
            raise EscalationValidationError(
                f"escalation for {self.project_id} attempted after only "
                f"{self.rounds_used} of {self.bound} bounded rounds — "
                "automation is NOT exhausted (FR-017)"
            )
        if self.bound <= 0:
            raise EscalationValidationError(
                f"escalation for {self.project_id} carries no bounded loop "
                f"(bound={self.bound}); unbounded escalation writers are "
                "prohibited (FR-017)"
            )


def _dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / _ESCALATIONS_REL


def write_record(
    record: EscalationRecord, *, repo_root: Path | None = None
) -> Path:
    """Validate + persist an escalation record; returns its path."""
    record.validate()
    if not record.timestamp:
        record.timestamp = datetime.now(UTC).isoformat()
    out_dir = _dir(repo_root)
    safe_ts = record.timestamp.replace(":", "").replace("+", "Z")
    path = out_dir / f"{record.project_id}__{safe_ts}.yaml"
    atomic_write_text(path, yaml.safe_dump(asdict(record), sort_keys=False))
    logger.warning(
        "escalation recorded for %s (%s: %d/%d rounds): %s",
        record.project_id, record.loop, record.rounds_used, record.bound, path,
    )
    return path


def list_records(
    *, repo_root: Path | None = None, open_only: bool = False
) -> list[EscalationRecord]:
    out: list[EscalationRecord] = []
    d = _dir(repo_root)
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.yaml")):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            rec = EscalationRecord(**data)
        except (yaml.YAMLError, TypeError) as exc:
            logger.warning("unreadable escalation record %s: %s", p, exc)
            continue
        if open_only and rec.digest_id:
            continue
        out.append(rec)
    return out


def _default_gh(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


# --- FR-016: engine failures file a tracked issue, never park ------------


def _issue_ledger_path(
    project_id: str, failure_class: str, *, repo_root: Path | None = None
) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in failure_class)
    return (repo_root or _repo_root()) / _ISSUE_LEDGER_REL / f"{project_id}__{safe}.yaml"


def file_engine_failure_issue(
    *,
    project_id: str,
    stage: str,
    error: str,
    evidence: str = "",
    run_id: str = "",
    repo_root: Path | None = None,
    gh=None,
) -> int | None:
    """File (or reuse) the tracked issue for an engine failure (FR-016).

    Deduped per (project, failure class): the first occurrence opens an
    issue and records its number in the ledger; repeats add nothing (the
    project keeps retrying on schedule; the issue tracks the fix). Returns
    the issue number, or None when GitHub is unreachable — filing is
    best-effort and NEVER blocks or parks the project.
    """
    gh = gh or _default_gh
    failure_class = error.split(":", 1)[0].strip() or "EngineFailure"
    ledger = _issue_ledger_path(project_id, failure_class, repo_root=repo_root)
    if ledger.exists():
        try:
            data = yaml.safe_load(ledger.read_text(encoding="utf-8")) or {}
            return int(data.get("issue_number", 0)) or None
        except (yaml.YAMLError, ValueError):
            pass
    title = f"[engine-failure] {project_id} @ {stage}: {failure_class}"
    body = (
        f"Automated report (spec 023 / FR-016) — an unexpected engine "
        f"failure occurred while processing **{project_id}** at stage "
        f"`{stage}`.\n\n"
        f"```\n{error}\n```\n\n"
        + (f"**Evidence**:\n\n```\n{evidence}\n```\n\n" if evidence else "")
        + (f"Run: `{run_id}`\n\n" if run_id else "")
        + "The project remains schedulable; it will retry on its normal "
        "cadence and recover once the underlying defect is fixed. Closing "
        "this issue does not require any project-state change."
    )
    rc, out, err = gh(
        "api", f"repos/{GITHUB_REPO}/issues", "-X", "POST",
        "-f", f"title={title}", "-f", f"body={body}",
        "-f", f"labels[]={ENGINE_FAILURE_LABEL}",
    )
    if rc != 0:
        logger.warning(
            "engine-failure issue filing failed for %s (%s): %s",
            project_id, failure_class, err.strip(),
        )
        return None
    try:
        number = int(json.loads(out).get("number", 0))
    except (json.JSONDecodeError, ValueError):
        number = 0
    atomic_write_text(
        ledger,
        yaml.safe_dump(
            {
                "issue_number": number,
                "project_id": project_id,
                "failure_class": failure_class,
                "filed_at": datetime.now(UTC).isoformat(),
            }
        ),
    )
    return number or None


# --- FR-017: periodic digest ----------------------------------------------


def build_digest_markdown(records: list[EscalationRecord]) -> str:
    lines = [
        "Open exhaustion-evidence escalations (spec 023 / FR-017). Each row "
        "proves a bounded automated loop ran to its cap before asking a "
        "human. Steady-state target: zero rows.",
        "",
        "| Project | Stage | Loop | Rounds | Recommended action |",
        "|-|-|-|-|-|",
    ]
    for r in records:
        lines.append(
            f"| {r.project_id} | {r.stage} | {r.loop} | "
            f"{r.rounds_used}/{r.bound} | {r.recommended_action or '—'} |"
        )
    if not records:
        lines.append("| _none_ | | | | |")
    return "\n".join(lines)


def update_digest(*, repo_root: Path | None = None, gh=None) -> int | None:
    """Aggregate open records into the single digest issue; mark them
    digested. Called by the scheduled audit lane. Returns the digest issue
    number (None when there is nothing to digest or GitHub is unreachable).
    """
    gh = gh or _default_gh
    open_records = list_records(repo_root=repo_root, open_only=True)
    if not open_records:
        return None
    rc, out, _err = gh(
        "api",
        f"search/issues?q=repo:{GITHUB_REPO}+is:issue+is:open"
        f"+label:{DIGEST_LABEL}+in:title+%22Escalation+digest%22",
    )
    number: int | None = None
    if rc == 0:
        try:
            items = json.loads(out).get("items", [])
            if items:
                number = int(items[0]["number"])
        except (json.JSONDecodeError, KeyError, ValueError):
            number = None
    body = build_digest_markdown(list_records(repo_root=repo_root))
    if number is None:
        rc, out, err = gh(
            "api", f"repos/{GITHUB_REPO}/issues", "-X", "POST",
            "-f", f"title={DIGEST_TITLE}", "-f", f"body={body}",
            "-f", f"labels[]={DIGEST_LABEL}",
        )
        if rc != 0:
            logger.warning("digest issue creation failed: %s", err.strip())
            return None
        try:
            number = int(json.loads(out).get("number", 0)) or None
        except (json.JSONDecodeError, ValueError):
            number = None
    else:
        rc, _out, err = gh(
            "api", f"repos/{GITHUB_REPO}/issues/{number}", "-X", "PATCH",
            "-f", f"body={body}",
        )
        if rc != 0:
            logger.warning("digest issue update failed: %s", err.strip())
    if number:
        # Mark the digested records so they don't re-aggregate.
        d = _dir(repo_root)
        for p in sorted(d.glob("*.yaml")):
            try:
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            if not data.get("digest_id"):
                data["digest_id"] = str(number)
                atomic_write_text(p, yaml.safe_dump(data, sort_keys=False))
    return number


__all__ = [
    "DIGEST_TITLE",
    "GITHUB_REPO",
    "EscalationRecord",
    "EscalationValidationError",
    "build_digest_markdown",
    "file_engine_failure_issue",
    "list_records",
    "update_digest",
    "write_record",
]
