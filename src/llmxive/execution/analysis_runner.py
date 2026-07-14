"""Deterministic analysis execution from the quickstart run-book.

``quickstart.md`` (produced by ``/speckit-plan`` for every project) carries
the ordered shell commands that run the analysis — download → parse →
filter → analyze → visualize. This module extracts those commands and runs
them in the project's per-project venv (via :mod:`llmxive.sandbox`), then
reports which real artifacts (data files, figures) were produced.

It is INTENTIONALLY deterministic and does not rely on the implementer LLM
flagging individual scripts ``execute: true`` — a near-converged
implementation left every script unflagged, so nothing ran (the PROJ-552
hollow-implementation finding). Running the whole run-book once, after the
code is written, is the dedicated execution stage.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path

from llmxive import sandbox

# Directory NAMES whose (non-.gitkeep, non-empty) contents count as real produced
# research artifacts. Scanned at the project root AND under code/, because plans
# vary: most write to data/ or figures/, but some write to results/ or
# code/output/ (e.g. PROJ-492's code/output/summary_report.csv) — those are real
# computed outputs and must NOT be missed, else a genuine run is falsely gated
# "produced no data/figure artifacts" and the project stalls at in_progress.
# (offload.py keeps a parallel list for the Kaggle-kernel retrieval path.)
_ARTIFACT_DIRS = ("data", "figures", "results", "output", "outputs")
_FIGURE_SUFFIXES = (".png", ".pdf", ".jpg", ".jpeg", ".svg")
_DATA_SUFFIXES = (".csv", ".json", ".parquet", ".npy", ".npz", ".tsv", ".h5", ".feather")

# Shell builtins / no-data commands in quickstart blocks we deliberately skip
# (directory checks, navigation, prints) — only ``python`` lines do real work.
_SKIP_PREFIXES = ("#", "cd ", "ls", "cat ", "echo", "export ", "source ", "mkdir",
                  "pip install", "python -m venv", "tree", "find ", "head ", "tail ")

_BASH_BLOCK_RE = re.compile(r"```(?:bash|sh|console)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass
class RunCommandResult:
    """Outcome of one quickstart ``python`` command."""

    command: str
    ok: bool
    returncode: int
    duration_s: float
    timed_out: bool
    tail: str  # last chars of stdout+stderr, for diagnosis
    script_missing: bool = False
    advisory: bool = False  # `python -c` smoke-test — reported, but does not gate


@dataclass
class AnalysisRunResult:
    """Aggregate outcome of running the quickstart analysis run-book."""

    ok: bool
    commands: list[RunCommandResult] = field(default_factory=list)
    artifacts_produced: list[str] = field(default_factory=list)  # repo-rel-ish (project-rel) paths
    declared_missing: list[str] = field(default_factory=list)    # declared deliverables absent post-run
    deadline_exceeded: bool = False
    reason: str = ""
    fabrication: list[str] = field(default_factory=list)         # deterministic fabricated-result findings
    hollow: list[str] = field(default_factory=list)              # results that were never COMPUTED (null/NaN/empty)


def extract_run_commands(quickstart_text: str) -> list[str]:
    """Return the ordered ``python`` commands from quickstart's bash blocks.

    Only ``python``/``python3`` lines are kept (they do the real work);
    directory checks, navigation, prints, and the venv/pip setup lines are
    skipped (the venv + requirements are handled by :func:`sandbox.ensure_venv`).
    Line-continuations (trailing ``\\``) are joined.
    """
    commands: list[str] = []
    for block in _BASH_BLOCK_RE.findall(quickstart_text or ""):
        # Join backslash line-continuations within the block.
        joined = re.sub(r"\\\s*\n\s*", " ", block)
        for raw in joined.splitlines():
            line = raw.strip()
            if not line:
                continue
            if any(line.startswith(p) for p in _SKIP_PREFIXES):
                continue
            if line.startswith(("python ", "python3 ")):
                commands.append(line)
    return commands


def _resolve_script(project_dir: Path, rel_path: str) -> str | None:
    """Resolve a run-book ``code/...py`` path to the actual file on disk.

    The planner writes quickstart paths BEFORE the implementer writes code,
    so the two drift (``code/data/filter_hyperbolic.py`` in quickstart vs
    ``code/filter/hyperbolic_filter.py`` on disk — different dir AND word
    order). Resolve by underscore-token set so naming/dir drift doesn't read
    as a genuinely-missing script (the PROJ-552 auto-fix-loop dead-end):

    1. exact path,
    2. the UNIQUE file under code/ whose stem token-set EQUALS the needed
       stem's token-set (filter_hyperbolic == hyperbolic_filter),
    3. the UNIQUE file whose token-set is a SUPERSET (validation_status ⊆
       validation_status_generator),

    else ``None`` (genuinely missing — a real gap the implementer must fill).
    """
    if (project_dir / rel_path).is_file():
        return rel_path
    code = project_dir / "code"
    if not code.is_dir():
        return None
    want = set(Path(rel_path).stem.split("_"))
    if not want:
        return None
    cands = [p for p in code.rglob("*.py") if "/.venv/" not in str(p)]
    exact = [p for p in cands if set(p.stem.split("_")) == want]
    if len(exact) == 1:
        return str(exact[0].relative_to(project_dir))
    superset = [p for p in cands if want < set(p.stem.split("_"))]
    if len(superset) == 1:
        return str(superset[0].relative_to(project_dir))
    return None


def _snapshot_artifacts(project_dir: Path) -> dict[str, float]:
    """Map of project-relative artifact path -> mtime for non-empty data/figure
    files (excluding .gitkeep and venv)."""
    snap: dict[str, float] = {}
    roots: list[Path] = []
    for sub in _ARTIFACT_DIRS:
        roots.append(project_dir / sub)           # <proj>/data, <proj>/results, …
        roots.append(project_dir / "code" / sub)  # <proj>/code/output, …
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.name == ".gitkeep" or "/.venv/" in str(p):
                continue
            try:
                if p.stat().st_size == 0:
                    continue
                snap[str(p.relative_to(project_dir))] = p.stat().st_mtime
            except OSError:
                continue
    return snap


def _is_research_artifact(rel_path: str) -> bool:
    suffix = Path(rel_path).suffix.lower()
    return suffix in _FIGURE_SUFFIXES or suffix in _DATA_SUFFIXES


def declared_deliverables(tasks_md: str) -> set[str]:
    """Project-relative file paths a task explicitly says to produce.

    Matches data/figure file paths (``data/...``, ``figures/...``, or any
    ``*.png``/``*.csv``/… token) named in task lines. Used to verify the
    run-book actually created what the tasks promised.
    """
    out: set[str] = set()
    # data/ or figures/ rooted paths with a real file extension
    for m in re.finditer(r"\b((?:data|figures)/[\w./-]+\.\w+)", tasks_md or ""):
        out.add(m.group(1))
    return {
        p for p in out
        if _is_research_artifact(p) and not p.endswith(".gitkeep")
    }


def run_analysis(
    project_dir: Path,
    *,
    quickstart_path: Path | None = None,
    per_cmd_timeout_s: int = 1200,
    overall_deadline_s: float | None = None,
) -> AnalysisRunResult:
    """Run the quickstart analysis run-book in the project venv and verify
    real artifacts were produced.

    ``ok`` is True iff EVERY run-book command exited 0 AND at least one real
    research artifact (data file or figure) was produced. A missing script,
    a non-zero exit, a timeout, or a zero-artifact run all yield ``ok=False``
    with a diagnostic ``reason`` (the gate kicks back to the implementer).
    """
    import os
    import time

    # Cap a single execute_and_gate so it can't blow the CI job timeout. By
    # default this tracks LLMXIVE_RUN_WALL_BUDGET_S (the run-loop wall budget,
    # 2400s in CI) — a single analysis fitting one wall-budget window keeps the
    # implement lane safe. ``LLMXIVE_ANALYSIS_DEADLINE_S`` OVERRIDES it to DECOUPLE
    # the two: if a lane ever raises its wall budget for more task-implementation
    # throughput, it can pin the analysis deadline smaller here so worst-case
    # (wall_budget + analysis_deadline + commit) still clears the job timeout.
    # (Today no lane sets it, so behavior is unchanged.) Sane 2700s when neither
    # is set (local).
    if overall_deadline_s is None:
        _dl = (os.environ.get("LLMXIVE_ANALYSIS_DEADLINE_S")
               or os.environ.get("LLMXIVE_RUN_WALL_BUDGET_S"))
        try:
            overall_deadline_s = float(_dl) if _dl else 2700.0
        except ValueError:
            overall_deadline_s = 2700.0

    project_dir = Path(project_dir)
    if quickstart_path is None:
        quickstart_path = _find_quickstart(project_dir)
    if quickstart_path is None or not quickstart_path.is_file():
        return AnalysisRunResult(
            ok=False, reason="no quickstart.md run-book found for the project",
        )
    qtext = quickstart_path.read_text(encoding="utf-8", errors="replace")
    commands = extract_run_commands(qtext)
    if not commands:
        return AnalysisRunResult(
            ok=False,
            reason="quickstart.md contains no runnable `python` commands",
        )

    before = _snapshot_artifacts(project_dir)
    results: list[RunCommandResult] = []
    deadline_exceeded = False
    t0 = time.monotonic()

    for command in commands:
        if time.monotonic() - t0 > overall_deadline_s:
            deadline_exceeded = True
            break
        try:
            args = shlex.split(command)[1:]  # drop the leading `python`
        except ValueError:
            results.append(RunCommandResult(
                command=command, ok=False, returncode=-1, duration_s=0.0,
                timed_out=False, tail="unparseable command (shlex)",
            ))
            continue
        # A `python code/x.py` line whose script is absent: try to resolve
        # planner-vs-implementer naming/dir drift to the real file; only a
        # genuinely-unresolvable path is a real missing-script failure.
        script_missing = False
        if args and not args[0].startswith("-") and args[0].endswith(".py"):
            resolved = _resolve_script(project_dir, args[0])
            if resolved is None:
                script_missing = True
            elif resolved != args[0]:
                args = [resolved, *args[1:]]
                command = "python " + " ".join(shlex.quote(a) for a in args)
        # Put BOTH the project's code/ dir AND the project root on PYTHONPATH.
        # Generated analysis code mixes two absolute-import conventions, often
        # within one project: bare sibling imports (`from data_loader import ...`,
        # `from reproducibility.logs import ...`) need code/ on the path, while
        # package-qualified imports (`from code.data_loader import ...`, natural
        # when code/ has an __init__.py) need the project ROOT on the path. With
        # only code/ on PYTHONPATH the `code.`-prefixed form ModuleNotFErrors and
        # the execution fix-loop can't converge it (the PROJ-261 7-round thrash
        # that never reached research_complete). Carrying both makes either style
        # run without a rewrite. code/ goes first so a bare sibling import always
        # wins over a same-named top-level module.
        pythonpath = os.pathsep.join((
            str((project_dir / "code").resolve()),
            str(project_dir.resolve()),
        ))
        res = sandbox.run_in_venv(
            project_dir=project_dir, args=args, timeout_s=per_cmd_timeout_s,
            extra_env={"PYTHONPATH": pythonpath},
        )
        tail = ((res.stdout or "") + "\n" + (res.stderr or ""))[-1200:]
        # `python -c "..."` lines are quickstart SMOKE-TESTS (import checks),
        # not artifact producers. The gate is "did the real scripts run and
        # produce real artifacts" — a failing smoke-test (often a quickstart
        # authoring slip like `from code.x import ...` when scripts use
        # `from x import ...`) is reported but must NOT block research_complete.
        advisory = bool(args and args[0] == "-c")
        results.append(RunCommandResult(
            command=command, ok=res.ok, returncode=res.returncode,
            duration_s=res.duration_s, timed_out=res.timed_out,
            tail=tail, script_missing=script_missing, advisory=advisory,
        ))

    after = _snapshot_artifacts(project_dir)
    produced = sorted(
        rel for rel, mt in after.items()
        if _is_research_artifact(rel) and (rel not in before or before[rel] != mt)
    )

    # Verify declared deliverables (best-effort: only those the run-book
    # SHOULD have produced; missing ones are gate failures).
    tasks_md = _read_tasks(project_dir)
    declared = declared_deliverables(tasks_md) if tasks_md else set()
    # Phantom-deliverable guard: a declared deliverable the project's code never
    # references is a PLANNER/TASKER phantom, not an output the code intends to
    # write — endemic to reprocessed code papers, where the back-filled tasks.md
    # invents deliverable filenames independently of the adapted code's real
    # outputs (the code RUNS and writes real artifacts, e.g. data/results.json,
    # yet the gate fails on a never-written data/results_subset.csv). Gate only on
    # deliverables the code actually writes — verified by the code referencing the
    # path. `bool(produced)` below still requires real artifacts, so this can
    # never pass a project that produced nothing.
    if declared:
        code_dir = project_dir / "code"
        code_blob = (
            "\n".join(
                p.read_text(encoding="utf-8", errors="ignore")
                for p in sorted(code_dir.rglob("*.py"))
            )
            if code_dir.is_dir()
            else ""
        )
        if code_blob:
            declared = {d for d in declared if d in code_blob}
    declared_missing = sorted(
        d for d in declared if not (project_dir / d).is_file()
        or (project_dir / d).stat().st_size == 0
    )

    # Advisory (`python -c` smoke-test) failures are reported but do not gate.
    cmd_failures = [r for r in results if not r.ok and not r.advisory]
    # DETERMINISTIC anti-fabrication gate (PROJ-604): the code can RUN and write
    # real files while its reported numbers are fabricated — drawn from random.*,
    # forced by a tautological constant, or openly labelled "simulated metrics"
    # because the real (GPU) computation could not run. "code ran + a file
    # appeared" is satisfied by fabrication, so without this a faked benchmark
    # reaches research_complete and only the LLM panel catches it. A non-empty
    # finding hard-fails the gate → kickback to implementation for a REAL run.
    from llmxive.execution.fabrication_guard import find_fabrication
    from llmxive.execution.hollow_guard import (
        find_hollow_results,
        find_no_durable_evidence,
    )

    fabrication = find_fabrication(project_dir)
    # DETERMINISTIC hollow-results gate: `bool(produced)` only asks "did a file
    # appear?" — it never looks INSIDE. fabrication_guard catches numbers that were
    # FAKED; this catches numbers that were never COMPUTED. PROJ-179 (metacognitive
    # awareness, run on the IRIS FLOWER dataset) reached research_complete having
    # written correlation=null, p=null, d_prime=NaN, robustness=[] and its own
    # {"status": "PASS"}. Every headline number was missing and the gate said ok.
    hollow = find_hollow_results(project_dir, produced)
    # ...and a run whose every artifact is gitignored leaves nothing a reviewer can
    # open or a paper can cite (PROJ-256 advanced on ONE data/processed/*.json).
    # project_dir is <repo>/projects/<id>, so parents[1] is the repo whose .gitignore
    # decides durability (the .gitignore is the SSoT — never re-encode its patterns).
    undurable = find_no_durable_evidence(
        project_dir, produced, repo_root=project_dir.parents[1]
    )
    ok = (
        not deadline_exceeded
        and not cmd_failures
        and bool(produced)
        and not declared_missing
        and not fabrication
        and not hollow
        and not undurable
    )
    reason_parts: list[str] = []
    if fabrication:
        reason_parts.append(
            f"{len(fabrication)} fabricated/simulated-result signal(s) — results are "
            "not real measurements: " + "; ".join(fabrication[:3])
        )
    if hollow:
        reason_parts.append(
            f"{len(hollow)} hollow-result signal(s) — the analysis ran but computed "
            "nothing: " + "; ".join(hollow[:3])
        )
    if undurable:
        reason_parts.append(undurable[0])
    if deadline_exceeded:
        reason_parts.append(f"overall deadline {overall_deadline_s:.0f}s exceeded")
    if cmd_failures:
        miss = [r.command for r in cmd_failures if r.script_missing]
        if miss:
            reason_parts.append(
                f"{len(miss)} run-book script(s) missing (plan/impl path mismatch): "
                + "; ".join(miss[:3])
            )
        other = [r for r in cmd_failures if not r.script_missing]
        if other:
            reason_parts.append(
                f"{len(other)} command(s) failed: "
                + "; ".join(f"{r.command} (rc={r.returncode})" for r in other[:3])
            )
    if not produced and not cmd_failures and not deadline_exceeded:
        reason_parts.append("run-book completed but produced no data/figure artifacts")
    if declared_missing:
        reason_parts.append(
            f"{len(declared_missing)} declared deliverable(s) absent: "
            + "; ".join(declared_missing[:3])
        )
    return AnalysisRunResult(
        ok=ok,
        commands=results,
        artifacts_produced=produced,
        declared_missing=declared_missing,
        deadline_exceeded=deadline_exceeded,
        reason="; ".join(reason_parts) or "ok",
        fabrication=fabrication,
        hollow=[*hollow, *undurable],
    )


def _find_quickstart(project_dir: Path) -> Path | None:
    """Locate the project's quickstart.md via the speckit feature dir.

    Pointer-first (the project's speckit_research_dir), else newest specs/*/.
    """
    # pointer-first
    try:
        from llmxive.state import project as project_store
        repo = project_dir.parent.parent
        proj = project_store.load(project_dir.name, repo_root=repo)
        ptr = proj.speckit_research_dir
        if ptr:
            q = repo / ptr / "quickstart.md"
            if q.is_file():
                return q
    except Exception:
        pass
    candidates = sorted((project_dir / "specs").glob("*/quickstart.md"))
    return candidates[-1] if candidates else None


def _read_tasks(project_dir: Path) -> str:
    for tasks in sorted((project_dir / "specs").glob("*/tasks.md"), reverse=True):
        try:
            return tasks.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return ""
