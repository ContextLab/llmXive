"""Per-paper compile/restyle/audit status records (spec 023 / US6,
FR-022..024; contract:
specs/023-pipeline-e2e-completion/contracts/paper-status-record.md).

One canonical JSON record per paper under ``state/paper_status/<id>.json``.
Every compile, restyle, and audit outcome writes here — serving the
original (un-restyled) PDF without a recorded failure reason is a contract
violation (pre-023, 18 of 94 shelf papers were exactly that: silent
fallbacks). The records feed the bounded automatic repair loop (reusing
the US1 revision machinery) and the public site's honest status display.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from llmxive.config import repo_root as _repo_root
from llmxive.state._io import atomic_write_text

logger = logging.getLogger(__name__)

STATUS_AUDITED = "audited"
STATUS_RESTYLED_UNAUDITED = "restyled_unaudited"
STATUS_FALLBACK = "fallback_original"
VALID_STATUSES = (STATUS_AUDITED, STATUS_RESTYLED_UNAUDITED, STATUS_FALLBACK)

#: Bounded repair discipline (FR-023): after this many repair rounds the
#: paper honestly keeps its failure/fallback status instead of looping.
MAX_REPAIR_ROUNDS = 3


def _dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "state" / "paper_status"


def _path(paper_id: str, *, repo_root: Path | None = None) -> Path:
    return _dir(repo_root) / f"{paper_id}.json"


def load(paper_id: str, *, repo_root: Path | None = None) -> dict[str, Any] | None:
    p = _path(paper_id, repo_root=repo_root)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def list_all(*, repo_root: Path | None = None) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    d = _dir(repo_root)
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.json")):
        rec = load(p.stem, repo_root=repo_root)
        if rec:
            out[p.stem] = rec
    return out


def _save(
    paper_id: str, record: dict[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    if record.get("status") not in VALID_STATUSES:
        raise ValueError(
            f"paper status for {paper_id} must be one of {VALID_STATUSES}, "
            f"got {record.get('status')!r}"
        )
    if record["status"] == STATUS_FALLBACK and not record.get("failure"):
        raise ValueError(
            f"paper {paper_id}: serving the original PDF REQUIRES a recorded "
            "failure reason — silent fallback is prohibited (FR-022)"
        )
    record["paper_id"] = paper_id
    record["updated_at"] = datetime.now(UTC).isoformat()
    record.setdefault("repair_rounds", 0)
    p = _path(paper_id, repo_root=repo_root)
    atomic_write_text(p, json.dumps(record, indent=2) + "\n")
    return record


def record_compile_result(
    paper_id: str, result: dict[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    """Persist the outcome of one compile/restyle attempt (FR-022).

    ``result`` is the dict ``scripts/compile_paper.compile_project``
    returns: {ok, strategy, pdf, errors, overflow?}.
    """
    existing = load(paper_id, repo_root=repo_root) or {}
    strategy = result.get("strategy")
    errors = [str(e) for e in result.get("errors") or []]
    pdf = result.get("pdf")
    record: dict[str, Any] = {
        "pdf": pdf,
        "audit": existing.get("audit"),
        "repair_rounds": existing.get("repair_rounds", 0),
    }
    pdf_name = Path(str(pdf)).name if pdf else ""
    is_restyled = pdf_name.startswith("main-llmxive") or strategy == "llmxive-compile"
    # Bounded llmxive-restyle retry bookkeeping (defect: a fallback used to be
    # permanent). compile_paper marks each REAL themed-compile attempt with
    # ``llmxive_attempted``; failures increment the counter, a restyled
    # success resets it. ``compile-exhausted`` sweep skips don't re-count.
    attempts = existing.get("llmxive_compile_attempts", 0)
    attempts = int(attempts) if isinstance(attempts, int) and attempts >= 0 else 0
    if result.get("ok") and is_restyled:
        record["llmxive_compile_attempts"] = 0
    elif result.get("llmxive_attempted"):
        record["llmxive_compile_attempts"] = attempts + 1
    else:
        record["llmxive_compile_attempts"] = attempts
    if result.get("ok") and is_restyled:
        # A fresh restyled compile invalidates any prior audit verdict.
        prior_audit = existing.get("audit") if strategy == "already-present" else None
        record["audit"] = prior_audit
        record["status"] = (
            STATUS_AUDITED
            if prior_audit and prior_audit.get("passed")
            else STATUS_RESTYLED_UNAUDITED
        )
        record["failure"] = None
    else:
        reason = "; ".join(errors) or (
            "served pre-existing non-restyled PDF" if result.get("ok")
            else "compile produced no PDF"
        )
        stage = "restyle" if any("restyle" in e for e in errors) else "compile"
        record["status"] = STATUS_FALLBACK
        record["failure"] = {
            "stage": stage,
            "reason": reason[:1000],
            "log_excerpt": (errors[-1][-2000:] if errors else ""),
        }
    return _save(paper_id, record, repo_root=repo_root)


def record_audit_result(
    paper_id: str, audit: dict[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    """Persist a rendering-audit outcome and resolve the final status
    (FR-023: papers are re-audited after repair; the record updates before
    the site does)."""
    existing = load(paper_id, repo_root=repo_root) or {
        "status": STATUS_RESTYLED_UNAUDITED,
        "pdf": None,
        "failure": None,
    }
    findings = audit.get("findings") or audit.get("defects") or []
    passed = bool(audit.get("passed", not findings))
    existing["audit"] = {
        "passed": passed,
        "defects": findings,
        "audited_at": datetime.now(UTC).isoformat(),
    }
    if existing.get("status") != STATUS_FALLBACK:
        existing["status"] = STATUS_AUDITED if passed else STATUS_RESTYLED_UNAUDITED
    return _save(paper_id, existing, repo_root=repo_root)


def ensure_repair_round(
    paper_id: str, *, repo_root: Path | None = None
) -> Path | None:
    """Convert the record's failure/defects into a bounded repair
    work-spec via the US1 revision machinery (FR-023).

    Returns the round dir, or None when there is nothing to repair, the
    cap is reached (honest fallback — no loop), or the project cannot
    carry revision work.
    """
    repo = repo_root or _repo_root()
    record = load(paper_id, repo_root=repo)
    if not record:
        return None
    failure = record.get("failure")
    defects = ((record.get("audit") or {}).get("defects")) or []
    if not failure and not defects:
        return None
    rounds = int(record.get("repair_rounds", 0))
    if rounds >= MAX_REPAIR_ROUNDS:
        logger.info(
            "%s: repair cap (%d) reached — keeping honest %s status",
            paper_id, MAX_REPAIR_ROUNDS, record.get("status"),
        )
        return None
    from llmxive.convergence.revision_adapter import kickback_to_revision_spec
    from llmxive.convergence.types import Concern, KickbackRecord, Severity
    from llmxive.state import project as project_store
    from llmxive.types import Stage

    try:
        project = project_store.load(paper_id, repo_root=repo)
    except FileNotFoundError:
        return None
    concerns: list[Concern] = []
    if failure:
        concerns.append(
            Concern(
                id="compilerepair",
                reviewer="pdf-pipeline",
                severity=Severity.WRITING,
                artifact=f"projects/{paper_id}/paper/source/",
                location=str(failure.get("stage", "compile")),
                text=(
                    f"The paper's {failure.get('stage', 'compile')} step "
                    f"failed: {failure.get('reason', 'unknown')}. Fix the "
                    "LaTeX source so the restyled wrapper compiles."
                ),
                round=rounds + 1,
            )
        )
    for i, d in enumerate(defects[:20]):
        concerns.append(
            Concern(
                id=f"auditdef{i:05d}",
                reviewer="pdf-auditor",
                severity=Severity.WRITING,
                artifact=f"projects/{paper_id}/paper/source/",
                location=f"page {d.get('page', '?')}",
                text=(
                    f"Rendering-audit defect ({d.get('kind', d.get('check', 'defect'))}): "
                    f"{d.get('detail', d.get('message', json.dumps(d)[:200]))}"
                ),
                round=rounds + 1,
            )
        )
    kb = KickbackRecord(
        from_stage="paper_review",
        to_stage="paper_tasked",
        worst_severity=Severity.WRITING,
        unresolved_concerns=concerns,
        artifact_links=[f"projects/{paper_id}/paper/source/"],
        reason="spec 023 / FR-023: compile/audit repair round",
    )
    spec_dir = kickback_to_revision_spec(kb, project_id=paper_id, repo_root=repo)
    record["repair_rounds"] = rounds + 1
    _save(paper_id, record, repo_root=repo)
    if project.current_stage in {
        Stage.PAPER_REVIEW, Stage.RESEARCH_REVIEW, Stage.AGENT_BLOCKED,
    } and not project.revision_spec_path:
        project_store.save(
            project.model_copy(
                update={
                    "revision_spec_path": str(spec_dir.relative_to(repo)),
                    "updated_at": datetime.now(UTC),
                }
            ),
            repo_root=repo,
        )
    return spec_dir


__all__ = [
    "MAX_REPAIR_ROUNDS",
    "STATUS_AUDITED",
    "STATUS_FALLBACK",
    "STATUS_RESTYLED_UNAUDITED",
    "VALID_STATUSES",
    "ensure_repair_round",
    "list_all",
    "load",
    "record_audit_result",
    "record_compile_result",
]
