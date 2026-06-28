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

# Signatures of a COMPUTE-ENVIRONMENT failure (GPU/CUDA/8-bit/OOM) that the free
# CPU-only CI runner cannot satisfy — NOT an implementer-fixable code bug. These
# need the METHOD re-scoped to run on CPU, so the fix-loop must flag them
# distinctly rather than burn rounds editing the failing script in place.
_COMPUTE_INFRA_RE = re.compile(
    r"\bcuda\b|bitsandbytes|load_in_8bit|device_map|out of memory|outofmemory|"
    r"memoryerror|torch not compiled with cuda|no gpu|gpu is required|"
    r"cuda is not available|cuda error|requires a gpu|cudnn",
    re.IGNORECASE,
)


def _compute_infra_failures(failures: list[str]) -> list[str]:
    """Failing commands whose error signals a COMPUTE-ENVIRONMENT limit
    (GPU/CUDA/8-bit/OOM) the free CPU CI can't satisfy. The fix is to RE-SCOPE
    the method to run on CPU (drop 8-bit/GPU, smaller model, sampled data), not
    to edit the failing script in place (the PROJ-261 bitsandbytes / PROJ-262
    GNN dead-end where the implementer can't fix missing hardware)."""
    out: list[str] = []
    for f in failures:
        if _COMPUTE_INFRA_RE.search(f):
            out.append(f.split(" -> rc=", 1)[0].strip())
    return out

#: Import name → PyPI distribution name, for the common cases where they differ
#: (a bare ``pip install <import-name>`` would 404). Unmapped names install as-is.
_IMPORT_TO_PIP = {
    "yaml": "pyyaml", "sklearn": "scikit-learn", "cv2": "opencv-python",
    "PIL": "pillow", "bs4": "beautifulsoup4", "skimage": "scikit-image",
    "dateutil": "python-dateutil", "dotenv": "python-dotenv",
    # Namespace submodules that ship WITH another distribution (no PyPI package
    # of their own) — mapping them to the OWNING dist stops a bogus requirement
    # line that would otherwise abort the whole install (the PROJ-262 stall:
    # `from mpl_toolkits.mplot3d import …` → bare `mpl_toolkits` is not on PyPI).
    "mpl_toolkits": "matplotlib",
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


def _deliverable_repair_feedback(project_dir: Path, res: AnalysisRunResult) -> str:
    """Guidance for declared deliverables the run-book DID NOT produce.

    A declared figure/data file can be absent even when every command exits 0 —
    because the script that should write it has a bug, writes the wrong path, or
    (the quickstart↔tasks mismatch) is never INVOKED by the run-book at all. The
    implement-loop can't see the run-book gap, so spell it out: which scripts
    reference the deliverable, whether each is a run-book command, and that the
    fix is to make one WRITE the exact path AND be invoked by quickstart.md.
    """
    if not res.declared_missing:
        return ""
    code = project_dir / "code"
    if not code.is_dir():
        return ""
    runbook: set[str] = set()
    for c in res.commands:
        m = re.search(r"\b(code/[\w./-]+\.py)\b", c.command)
        if m:
            runbook.add(m.group(1))
    py_files = [p for p in code.rglob("*.py") if "/.venv/" not in str(p)]

    blocks: list[str] = []
    for d in res.declared_missing:
        base, stem = Path(d).name, Path(d).stem
        refs: list[tuple[str, bool]] = []
        for p in py_files:
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if base in txt or (stem and stem in txt):
                rel = str(p.relative_to(project_dir))
                refs.append((rel, ("code/" + str(p.relative_to(code))) in runbook))
        if refs:
            ln = [f"- `{d}` is declared but was NOT written. Scripts referencing it:"]
            for rel, in_rb in refs[:8]:
                ln.append(f"    - `{rel}` — {'IS a run-book command' if in_rb else 'NOT invoked by the run-book'}")
            ln.append(
                f"  Make ONE of these WRITE `{d}` to that EXACT path. If its producing "
                "script is not a run-book command, ADD `python code/<script>.py` to "
                "quickstart.md so the run-book invokes it."
            )
            blocks.append("\n".join(ln))
        else:
            blocks.append(
                f"- `{d}` is declared but NOT written and NO script references it — "
                "create the script that produces it and add it to quickstart.md."
            )
    if not blocks:
        return ""
    return "\n".join([
        "",
        "## Declared deliverables NOT produced — make the run-book produce them",
        "",
        "Every command may exit 0 yet a declared data/figure file is still absent. "
        "Fix the producing script to WRITE it to the exact declared path, and ensure "
        "that script is INVOKED by the quickstart run-book (you may edit "
        "quickstart.md to add the command).",
        "",
        *blocks,
    ])


def execute_and_gate(project_dir: Path, *, repo_root: Path | None = None) -> bool:
    """Run the analysis and gate. Returns True iff it produced real artifacts.

    Side effects on failure: records status, writes the implementer feedback
    note, re-opens failing/missing tasks. On success: records status, mints
    receipts, clears the feedback note.
    """
    project_dir = Path(project_dir)
    project_id = project_dir.name
    repo = repo_root or project_dir.parent.parent

    # GPU-offload lane (issue #367): a project whose analysis already has a
    # Kaggle GPU kernel in flight is POLLED here instead of re-running the
    # (doomed CPU-only) analysis. A pending offload is NOT a failure — it never
    # bumps fix_rounds, so _decide_next_stage keeps the project IN_PROGRESS and
    # polling, never escalating to human_input_needed.
    if execution_status.is_offload_pending(project_id, repo_root=repo):
        return _poll_offload(project_dir, repo)

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

    # REGRESSION detection: a command FAILING now that was NOT failing in the
    # previous round means the implementer's last fix BROKE working code (the
    # live PROJ-262 thrash: a metrics-CSV fix re-broke train_rf.py, so the loop
    # oscillated toward the fix-round cap instead of converging). Surfacing these
    # explicitly — "revert what broke this" — is the convergence guard the
    # fix-one-break-another loop was missing. Computed BEFORE record() overwrites
    # the prior status.
    def _cmd(failure_line: str) -> str:
        return failure_line.split(" -> rc=", 1)[0].strip()

    prev = execution_status.load(project_id, repo_root=repo)
    prev_failing = {_cmd(f) for f in (prev or {}).get("failures", [])}
    regressions = sorted(
        _cmd(f) for f in failures if _cmd(f) not in prev_failing
    ) if prev_failing else []
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

    # GPU-offload lane (issue #367): if the local run FAILED on a COMPUTE-
    # ENVIRONMENT limit the free CPU CI cannot satisfy (GPU/CUDA/8-bit/OOM) AND
    # Kaggle offload is configured, DISPATCH the same run-book to Kaggle's free
    # GPU instead of burning a fix-round on a hardware gap the implementer can't
    # close. record_offload(status=submitted) does NOT bump fix_rounds → the
    # project stays IN_PROGRESS and the next tick polls (no human_input_needed).
    # Do NOT re-dispatch when this round already has a FAILED offload sub-record
    # (we are in the post-failure local pass): we must record one honest local
    # failure (bumping fix_rounds once) rather than thrash dispatch↔poll forever.
    _prior_offload = execution_status.offload_state(project_id, repo_root=repo)
    _offload_already_failed = bool(_prior_offload and _prior_offload.get("status") == "failed")
    if not res.ok and failures and not _offload_already_failed:
        try:
            infra = _compute_infra_failures(failures)
            if infra:
                from llmxive.execution import offload

                if offload.is_available():
                    kernel_ref = offload.dispatch(project_dir, repo)
                    if kernel_ref:
                        execution_status.record_offload(
                            project_id, status="submitted",
                            kernel_ref=kernel_ref, repo_root=repo,
                        )
                        logger.info(
                            "offloaded %s to Kaggle GPU kernel %s (compute-infra "
                            "failure: %s)", project_id, kernel_ref, infra[:2],
                        )
                        return False  # pending — poll on the next tick
        except Exception as exc:  # never let offload break the local fallback
            logger.warning("GPU offload dispatch skipped for %s: %s", project_id, exc)

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
        from llmxive.execution.shared_contract import (
            accumulate_contract_issues,
            find_contract_issues,
        )

        contract_issues = find_contract_issues(project_dir, failures)
        # Carry every contract ever seen forward so a symbol satisfied in an
        # earlier round is not silently dropped (the fix-one-break-another thrash).
        contract_issues = accumulate_contract_issues(mem, project_dir, contract_issues)
    except Exception as exc:
        logger.warning("shared-contract analysis skipped: %s", exc)
        contract_issues = []
    # Cross-script DATA-schema contract analysis (sibling of shared_contract):
    # ground the implementer in the REAL artifacts so it can reconcile a
    # consumer's "missing columns" / KeyError / "FileNotFoundError: <csv>" against
    # what the producer actually wrote — instead of oscillating for 12 rounds on a
    # trivial column-rename (the live PROJ-262 metrics-CSV stall).
    try:
        from llmxive.execution.data_contract import (
            accumulate_data_contract_issues,
            find_data_contract_issues,
        )

        data_contract_issues = find_data_contract_issues(project_dir, failures)
        data_contract_issues = accumulate_data_contract_issues(
            mem, project_dir, data_contract_issues
        )
    except Exception as exc:
        logger.warning("data-contract analysis skipped: %s", exc)
        data_contract_issues = []
    _write_execution_feedback(
        mem, res, failures, contract_issues, regressions, data_contract_issues
    )
    reopened = _reopen_failing_tasks(
        project_dir, res, contract_issues, data_contract_issues
    )
    logger.info("re-opened %d task(s) for the auto-fix loop", reopened)
    return False


def _poll_offload(project_dir: Path, repo: Path) -> bool:
    """Poll an in-flight Kaggle GPU kernel (issue #367) instead of re-running the
    local analysis. Returns True iff retrieval landed real artifacts (the gate
    advances to research_complete); False keeps the project IN_PROGRESS.

    * running   → leave pending, return False (NO fix_rounds bump).
    * complete  → retrieve; re-verify the pulled files exist & are non-empty; on
      real artifacts record ok=True + mint receipts + clear offload + return
      True; if retrieve yields nothing real → mark the offload failed and fall
      through to ONE normal local-failure pass.
    * error / cancelAcknowledged → mark the offload failed and fall through to
      the normal local-failure path (which bumps fix_rounds once).
    """
    from llmxive.execution import offload

    project_id = project_dir.name
    off = execution_status.offload_state(project_id, repo_root=repo)
    kernel_ref = (off or {}).get("kernel_ref")
    if not kernel_ref:  # defensive: pending with no ref → drop & re-run locally
        execution_status.clear_offload(project_id, repo_root=repo)
        return execute_and_gate(project_dir, repo_root=repo)

    status = offload.poll(kernel_ref)
    if status == "running":
        execution_status.record_offload(
            project_id, status="running", kernel_ref=kernel_ref, repo_root=repo,
        )
        logger.info("offload %s still running on Kaggle (%s)", project_id, kernel_ref)
        return False

    if status == "complete":
        pulled = offload.retrieve(kernel_ref, project_dir)
        real = [
            rel for rel in pulled
            if (project_dir / rel).is_file() and (project_dir / rel).stat().st_size > 0
        ]
        if real:
            execution_status.record(
                project_id, ok=True,
                reason=f"GPU offload complete via Kaggle kernel {kernel_ref}",
                artifacts=real, failures=[], repo_root=repo,
            )
            res = AnalysisRunResult(ok=True, artifacts_produced=real, reason="offload ok")
            _mint_artifact_receipts(project_dir, res, repo)
            execution_status.clear_offload(project_id, repo_root=repo)
            (project_dir / ".specify" / "memory" / _FEEDBACK_FILENAME).unlink(missing_ok=True)
            logger.info("offload %s retrieved %d artifact(s) from Kaggle", project_id, len(real))
            return True
        logger.warning(
            "offload %s completed but retrieved no real artifacts; falling back", project_id
        )
        execution_status.record_offload(
            project_id, status="failed", kernel_ref=kernel_ref, repo_root=repo,
        )
        return _run_local_after_failed_offload(project_dir, repo)

    # error / cancelAcknowledged / unknown-terminal → failed, then local fallback.
    logger.warning("offload %s ended status=%s; falling back to local path", project_id, status)
    execution_status.record_offload(
        project_id, status="failed", kernel_ref=kernel_ref, repo_root=repo,
    )
    return _run_local_after_failed_offload(project_dir, repo)


def _run_local_after_failed_offload(project_dir: Path, repo: Path) -> bool:
    """After a failed offload, run the normal local execute-and-gate ONCE. The
    offload sub-record is marked ``failed`` (not pending) so this re-entry does
    NOT loop back into ``_poll_offload``; and because ``offload.is_available()``
    is still True the very same compute-infra failure would re-dispatch — so we
    leave the failed sub-record in place to record one honest local failure
    (bumping fix_rounds once) rather than thrash dispatch↔poll."""
    return execute_and_gate(project_dir, repo_root=repo)


def _write_execution_feedback(
    mem_dir: Path, res: AnalysisRunResult, failures: list[str],
    contract_issues: list | None = None,
    regressions: list[str] | None = None,
    data_contract_issues: list | None = None,
) -> None:
    mem_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Execution failures — fix these before the analysis can run",
        "",
    ]
    if regressions:
        lines += [
            "## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)",
            "",
            "These commands were NOT failing in the previous round and ARE failing "
            "now — your last edit broke previously-working code. REVERT or correct "
            "whatever change broke each one BEFORE touching anything else; do not "
            "trade one passing script for another (that oscillation is what burns "
            "the fix-round budget toward escalation):",
            "",
            *(f"- `{c}`" for c in regressions),
            "",
        ]
    infra = _compute_infra_failures(failures)
    if infra:
        lines += [
            "## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script",
            "",
            "These commands failed because the analysis needs hardware the FREE, "
            "CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via "
            "bitsandbytes, or more RAM than is available). This is NOT a code bug "
            "you can patch by tweaking the failing line — the analysis MUST run on "
            "a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop "
            "`load_in_8bit` / `device_map='cuda'` and load in default precision on "
            "CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch "
            "size; prefer a CPU-tractable method. Change the METHOD, not just the "
            "line that threw:",
            "",
            *(f"- `{c}`" for c in infra),
            "",
        ]
    lines += [
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

    # Run-book-repair guidance for declared deliverables that no command produced
    # (a script with a bug / wrong path, or a producer the quickstart never runs).
    try:
        repair = _deliverable_repair_feedback(mem_dir.parent.parent, res)
        if repair:
            lines.append(repair)
    except Exception as exc:
        logger.warning("deliverable-repair feedback skipped: %s", exc)

    # Cross-script DATA-contract guidance: per data file, the REAL columns/keys the
    # producer wrote vs what the consumers require, the exact rename diff, and the
    # producer/consumer scripts — so the implementer reconciles a consumer's
    # "missing columns" / KeyError / "FileNotFoundError: <csv>" against reality
    # instead of oscillating on the consumer's EXPECTATION alone (the live PROJ-262
    # metrics-CSV column stall). Grounded in the actual artifacts, never a guess.
    if data_contract_issues:
        try:
            from llmxive.execution.data_contract import render_data_contract_feedback

            block = render_data_contract_feedback(data_contract_issues)
            if block:
                lines.append(block)
        except Exception as exc:
            logger.warning("data-contract feedback skipped: %s", exc)

    (mem_dir / _FEEDBACK_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _reopen_failing_tasks(
    project_dir: Path, res: AnalysisRunResult, contract_issues: list | None = None,
    data_contract_issues: list | None = None,
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
    # Re-open the PRODUCER (and consumer) scripts behind a cross-script DATA-schema
    # mismatch, so the implementer fixes the canonical producer (not just the
    # failing consumer it happened to see this round).
    if data_contract_issues:
        try:
            from llmxive.execution.data_contract import reopen_targets

            targets |= reopen_targets(data_contract_issues)
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
