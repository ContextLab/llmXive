"""Dedicated execution phase + auto-fix loop (spec 023 defect #25, part 2).

After the implementer has written all tasks, this runs the project's
analysis end-to-end (:func:`llmxive.execution.analysis_runner.run_analysis`)
and GATES ``research_complete`` on real artifacts:

* success → record ``ok=True``, mint harness receipts for produced
  artifacts, clear the feedback file. ``research_complete`` may proceed.
* failure → record ``ok=False`` with the failing-command tracebacks, write
  ``.specify/memory/execution_feedback.md`` (the implementer injects it),
  and RE-OPEN (un-check) the tasks whose scripts failed or are missing so
  the next implementer tick fixes them — the bounded auto-fix loop.

The loop is bounded by ``execution_status.MAX_EXECUTION_FIX_ROUNDS``; the
graph escalates to ``human_input_needed`` past the cap (honest terminal,
not silent advance).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from llmxive.execution.analysis_runner import AnalysisRunResult, run_analysis
from llmxive.state import execution_status

logger = logging.getLogger(__name__)

_FEEDBACK_FILENAME = "execution_feedback.md"


def execute_and_gate(project_dir: Path, *, repo_root: Path | None = None) -> bool:
    """Run the analysis and gate. Returns True iff it produced real artifacts.

    Side effects on failure: records status, writes the implementer feedback
    note, re-opens failing/missing tasks. On success: records status, mints
    receipts, clears the feedback note.
    """
    project_dir = Path(project_dir)
    project_id = project_dir.name
    repo = repo_root or project_dir.parent.parent

    # If a verified real data source was discovered, GUARANTEE its package is
    # declared so the per-project venv installs it (the implementer wires the
    # `import` but often forgets requirements.txt → ModuleNotFoundError). Safe:
    # discovery already proved `pip install <ref>` works.
    try:
        from llmxive.execution.data_source import ensure_source_in_requirements

        if ensure_source_in_requirements(project_dir):
            logger.info("declared discovered data-source package in requirements.txt")
    except Exception as exc:  # never block execution on this best-effort step
        logger.warning("ensure_source_in_requirements skipped: %s", exc)

    res = run_analysis(project_dir)
    failures = [
        f"{r.command} -> rc={r.returncode}"
        + (" [script missing]" if r.script_missing else "")
        + (f"\n    {r.tail.strip()[-400:]}" if not r.ok and r.tail else "")
        for r in res.commands if not r.ok
    ]
    execution_status.record(
        project_id, ok=res.ok, reason=res.reason,
        artifacts=res.artifacts_produced, failures=failures, repo_root=repo,
    )

    mem = project_dir / ".specify" / "memory"
    feedback = mem / _FEEDBACK_FILENAME

    if res.ok:
        logger.info(
            "execution OK for %s: %d artifacts produced",
            project_id, len(res.artifacts_produced),
        )
        _mint_artifact_receipts(project_dir, res, repo)
        feedback.unlink(missing_ok=True)
        return True

    logger.warning("execution FAILED for %s: %s", project_id, res.reason)
    _write_execution_feedback(mem, res, failures)
    reopened = _reopen_failing_tasks(project_dir, res)
    logger.info("re-opened %d task(s) for the auto-fix loop", reopened)
    return False


def _write_execution_feedback(
    mem_dir: Path, res: AnalysisRunResult, failures: list[str]
) -> None:
    mem_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Execution failures — fix these before the analysis can run",
        "",
        "The analysis code was EXECUTED end-to-end (per quickstart.md) and "
        "FAILED. The project cannot reach research_complete until the "
        "run-book runs cleanly AND produces its declared data/figure "
        "artifacts. Fix the ROOT CAUSE of each failure below — do not stub, "
        "do not fake outputs, do not mark a task done until its script "
        "actually runs and writes its real output.",
        "",
        f"**Summary**: {res.reason}",
        "",
        "## Failing / missing run-book commands",
        "",
    ]
    if failures:
        lines.extend(f"- {f}" for f in failures)
    else:
        lines.append("- (no per-command failures; the run produced no real "
                     "data/figure artifacts — ensure scripts WRITE their "
                     "declared outputs under data/ and figures/)")
    if res.declared_missing:
        lines += ["", "## Declared deliverables still missing", ""]
        lines.extend(f"- {d}" for d in res.declared_missing)

    # If a DATA deliverable is missing, the loader almost certainly lacks a real,
    # programmatically-accessible source (the implementer can't search, so it
    # hallucinates a fake endpoint). Discover + verify a real source ONCE and
    # inject it so the next implementer tick writes a loader that fetches REAL
    # data. Best-effort: discovery failure just omits the block.
    data_missing = any(
        d.startswith("data/") for d in res.declared_missing
    ) or (not res.artifacts_produced and "data" in (res.reason or ""))
    if data_missing:
        try:
            from llmxive.execution.data_source import (
                ensure_discovered_source,
                render_feedback_block,
            )

            project_dir = mem_dir.parent.parent
            block = render_feedback_block(ensure_discovered_source(project_dir))
            if block:
                lines.append(block)
        except Exception as exc:  # never block feedback-writing on discovery
            logger.warning("data-source discovery skipped: %s", exc)

    (mem_dir / _FEEDBACK_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _reopen_failing_tasks(project_dir: Path, res: AnalysisRunResult) -> int:
    """Un-check tasks.md lines that reference a failed/missing script path or
    its stem, so the implementer re-implements them. Returns count re-opened.
    """
    tasks_files = sorted(project_dir.glob("specs/*/tasks.md"))
    if not tasks_files:
        return 0
    tasks_path = tasks_files[0]
    text = tasks_path.read_text(encoding="utf-8", errors="replace")

    # Collect failing/missing script paths + stems from the run.
    targets: set[str] = set()
    for r in res.commands:
        if r.ok:
            continue
        m = re.search(r"\b(code/[\w./-]+\.py)\b", r.command)
        if m:
            rel = m.group(1)
            targets.add(rel)
            targets.add(Path(rel).stem)
    for d in res.declared_missing:
        targets.add(d)
        targets.add(Path(d).name)
    if not targets:
        return 0

    out_lines: list[str] = []
    reopened = 0
    for line in text.splitlines():
        m = re.match(r"^(\s*-\s*\[)[xX](\]\s.*)$", line)
        if m and any(t in line for t in targets):
            out_lines.append(m.group(1) + " " + m.group(2))  # [x] -> [ ]
            reopened += 1
        else:
            out_lines.append(line)
    if reopened:
        tasks_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return reopened


def _mint_artifact_receipts(
    project_dir: Path, res: AnalysisRunResult, repo: Path
) -> None:
    """Best-effort: mint a harness receipt per produced artifact so report
    numbers can trace to receipts (Constitution: no hallucinated results).
    Never raises — a receipt-key/HMAC issue must not block a real, OK run."""
    try:
        import hashlib

        from llmxive.results.harness import mint_receipt
        for rel in res.artifacts_produced:
            p = project_dir / rel
            if not p.is_file():
                continue
            kind = "figure" if p.suffix.lower() in (".png", ".pdf", ".jpg", ".jpeg", ".svg") else "table"
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            mint_receipt(
                value=rel, kind=kind,
                producer={"stage": "research_executing", "artifact": rel},
                inputs={"command": "quickstart run-book"},
                env_sha=digest[:16],
                captured={"path": rel, "sha256": digest},
                repo_root=repo, project_id=project_dir.name,
            )
    except Exception as exc:  # never block an OK run on receipt minting
        logger.warning("artifact receipt minting skipped: %s", exc)


__all__ = ["execute_and_gate"]
