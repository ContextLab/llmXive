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

_MODNOTFOUND_RE = re.compile(r"No module named ['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")

#: Import name → PyPI distribution name, for the common cases where they differ
#: (a bare ``pip install <import-name>`` would 404). Unmapped names install as-is.
_IMPORT_TO_PIP = {
    "yaml": "pyyaml", "sklearn": "scikit-learn", "cv2": "opencv-python",
    "PIL": "pillow", "bs4": "beautifulsoup4", "skimage": "scikit-image",
    "dateutil": "python-dateutil", "dotenv": "python-dotenv",
}


def _declare_missing_imports(project_dir: Path, failures: list[str]) -> list[str]:
    """Add third-party modules the run-book imports-but-can't-find to
    ``code/requirements.txt`` so the next ``ensure_venv`` installs them.

    Generalizable self-heal for the implementer dropping deps from
    requirements.txt. Skips the stdlib and the project's OWN ``code/`` modules
    (those are import-path issues, not missing packages). Best-effort: a wrong
    import→pip name simply fails to install and resurfaces (no correctness risk).
    Returns the modules newly declared.
    """
    import ast
    import os
    import sys

    code = project_dir / "code"
    # All module/package names defined ANYWHERE under code/ (not just the top
    # level): scripts in code/analysis/ import siblings by bare name, so
    # `data_quality` (code/analysis/data_quality.py) is LOCAL, not a pip dep.
    # Include directory (package) names too — even empty ones — and prune .venv.
    local_names: set[str] = set()
    for root, dirs, files in os.walk(code):
        if ".venv" in Path(root).parts:
            dirs[:] = []
            continue
        local_names.add(Path(root).name)
        local_names.update(dirs)
        local_names.update(f[:-3] for f in files if f.endswith(".py"))

    def _third_party(mod: str) -> str | None:
        """Top-level pip-installable module name, or None for stdlib/local."""
        top = mod.split(".")[0]
        if not top or top in sys.stdlib_module_names or top in local_names:
            return None
        return top

    candidates: set[str] = set()
    # (a) modules that actually raised ModuleNotFoundError this run.
    for f in failures:
        for mod in _MODNOTFOUND_RE.findall(f):
            if (top := _third_party(mod)):
                candidates.add(top)
    # (b) STATIC scan of every code/*.py import — declares the whole third-party
    # stack in ONE pass so deps don't peel one-failed-import-per-round (which
    # would burn the bounded fix-round budget). ast only, no execution.
    for py in code.rglob("*.py"):
        if "/.venv/" in str(py):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, ValueError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module]
            else:
                continue
            for mod in mods:
                if (top := _third_party(mod)):
                    candidates.add(top)
    if not candidates:
        return []
    req = code / "requirements.txt"
    existing = req.read_text(encoding="utf-8") if req.is_file() else ""

    def _bare(line: str) -> str:
        return re.split(r"[<>=!~\[ ;]", line.strip(), maxsplit=1)[0].lower().replace("_", "-")

    have = {_bare(ln) for ln in existing.splitlines() if ln.strip() and not ln.lstrip().startswith("#")}
    added = []
    for m in sorted(candidates):
        pip = _IMPORT_TO_PIP.get(m, m)  # map import name → PyPI name where they differ
        if pip.lower().replace("_", "-") not in have:
            added.append(pip)
    if not added:
        return []
    code.mkdir(parents=True, exist_ok=True)
    sep = "" if (not existing or existing.endswith("\n")) else "\n"
    block = "\n".join(f"{pip}  # auto-added: imported by run-book but missing from venv" for pip in added)
    req.write_text(existing + sep + block + "\n", encoding="utf-8")
    return added


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
    # Self-heal a venv missing third-party deps: the implementer sometimes
    # regenerates requirements.txt incompletely (e.g. dropping pandas/numpy when
    # it adds the data-source package), so run-book scripts die with
    # ModuleNotFoundError. Declare any third-party module the run-book imports
    # but couldn't find, so the next ensure_venv installs it.
    try:
        added = _declare_missing_imports(project_dir, failures)
        if added:
            logger.info("declared missing run-book imports in requirements.txt: %s", added)
    except Exception as exc:
        logger.warning("_declare_missing_imports skipped: %s", exc)

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
    # Detect shared-module API-contract failures (a symbol the project defines,
    # called incompatibly by many scripts). The implementer must fix the ONE
    # definition tolerant of all callers — not the callers — else the loop
    # oscillates forever. Feed it the call sites + re-open the DEFINING module's
    # task so it works on the root.
    try:
        from llmxive.execution.shared_contract import find_contract_issues

        contract_issues = find_contract_issues(project_dir, failures)
    except Exception as exc:
        logger.warning("shared-contract analysis skipped: %s", exc)
        contract_issues = []
    _write_execution_feedback(mem, res, failures, contract_issues)
    reopened = _reopen_failing_tasks(project_dir, res, contract_issues)
    logger.info("re-opened %d task(s) for the auto-fix loop", reopened)
    return False


def _write_execution_feedback(
    mem_dir: Path, res: AnalysisRunResult, failures: list[str],
    contract_issues: list | None = None,
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

    # Shared-module contract guidance (call sites + "fix the definition, tolerant
    # of all callers") — the thing that lets the loop converge a shared symbol
    # used incompatibly by many scripts instead of oscillating.
    if contract_issues:
        try:
            from llmxive.execution.shared_contract import render_contract_feedback

            block = render_contract_feedback(contract_issues)
            if block:
                lines.append(block)
        except Exception as exc:
            logger.warning("contract feedback skipped: %s", exc)

    (mem_dir / _FEEDBACK_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _reopen_failing_tasks(
    project_dir: Path, res: AnalysisRunResult, contract_issues: list | None = None
) -> int:
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
    # Re-open the task that owns the SHARED MODULE behind a contract error, so the
    # implementer fixes the ROOT definition (not just the failing callers).
    if contract_issues:
        try:
            from llmxive.execution.shared_contract import defining_files

            targets |= defining_files(contract_issues)
        except Exception:
            pass
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
