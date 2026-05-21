#!/usr/bin/env python3
"""Phase 4 (Spec Kit Plan → Tasks, with Analyze loop) validation harness.

Drives the two Phase-4 agents (`planner`, `tasker`) end-to-end on the two
carry-forward canonicals from spec 011 (PROJ-261 + PROJ-262), via the
production CLI (`python -m llmxive run --project <id> --max-tasks 2`) with
``LLMXIVE_INSPECTION_DIR`` set so the env-gated hook in
:mod:`llmxive.speckit.slash_command` writes verbatim per-agent inspection
records (including the Tasker's per-round sub-records). It then checks
post-conditions and emits ``specs/014-…/carry-forward.yaml`` +
``specs/014-…/phase-report.md`` per the spec-014 contracts.

This driver implements:
- T008 preflight (Principle V, fail-fast <10s)
- T009 FR-018 reset (delete Phase-4 outputs, PRESERVE spec.md)
- T010 run invocation
- T011 post-run verification (stage chain, artifact presence, FR-009/FR-010
  ordering, FR-012 constraint-non-deletion, FR-020 Constitution Check)
- T022 carry-forward.yaml
- T023 phase-report.md

Pure helper functions (``check_task_ordering``, ``fr_sc_counts``,
``constitution_check_ok``) are importable by the regression tests.

Usage:
    python scripts/validate_phase4.py --project PROJ-261-…
    python scripts/validate_phase4.py --all
    python scripts/validate_phase4.py --no-reset --project PROJ-262-…

Exit codes:
    0 — selected project(s) reached `analyzed` and passed all post-conditions
    1 — at least one project failed validation (carry-forward.yaml still written)
    2 — preflight failed / FR-019 decline (no state changes attempted)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = REPO_ROOT / "specs" / "014-phase4-plan-tasks-testing"
INSPECTIONS_DIR = SPEC_DIR / "inspections"

CANONICAL_PROJECTS = (
    "PROJ-261-evaluating-the-impact-of-code-duplicatio",
    "PROJ-262-predicting-molecular-dipole-moments-with",
)

# FR-018: the Phase-4 OUTPUT artifacts (deleted on reset; spec.md PRESERVED).
PHASE4_OUTPUT_FILES = (
    "plan.md",
    "research.md",
    "data-model.md",
    "quickstart.md",
    "tasks.md",
)
PHASE4_OUTPUT_DIRS = ("contracts",)
PHASE4_MEMORY_FILES = ("tasker_rounds.yaml", "human_input_needed.yaml")

# The five plan artifacts the Planner must produce (FR-005 / SC-002).
PLAN_PLAIN_ARTIFACTS = ("plan.md", "research.md", "data-model.md", "quickstart.md")

# Stages that count as a successful (or accepted-hold) Phase-4 terminus.
TERMINAL_OK_STAGES = {"analyzed", "human_input_needed", "held"}

_TASK_LINE_RE = re.compile(r"^- \[[ Xx]\] T\d+", re.MULTILINE)


def _exit_2(msg: str) -> None:
    print(f"[validate_phase4] STOP: {msg}", file=sys.stderr)
    sys.exit(2)


def _feature_dir(project_id: str) -> Path | None:
    """Return the canonical 001-<slug> feature dir for a project, or None."""
    specs_dir = REPO_ROOT / "projects" / project_id / "specs"
    if not specs_dir.is_dir():
        return None
    for sub in sorted(specs_dir.iterdir()):
        if sub.is_dir() and re.match(r"^\d{3}-", sub.name):
            return sub
    return None


# ──────────────────────────────────────────────────────────────────────
# Pure helpers (importable by tests)
# ──────────────────────────────────────────────────────────────────────

def fr_sc_counts(spec_md_text: str) -> tuple[int, int]:
    """Return (FR-NNN count, SC-NNN count) in a spec.md (FR-012)."""
    fr = len(re.findall(r"\bFR-\d+\b", spec_md_text))
    sc = len(re.findall(r"\bSC-\d+\b", spec_md_text))
    return fr, sc


def check_task_ordering(tasks_md_text: str) -> list[str]:
    """FR-010 data-flow ordering check on a tasks.md document.

    Returns a list of human-readable findings (empty == ordering OK). Checks
    at least the two spec-mandated invariants:
      - a task that USES/trains-on a dataset must come after the task that
        DOWNLOADS/fetches it (download-before-use);
      - a task that WRITES INTO a directory must come after the task that
        CREATES that directory (dir-before-write).

    The heuristic operates on the ``- [ ] T### … <path>`` task lines in
    document order. A consumer that references a path/dataset token also
    produced later in the file is flagged.
    """
    findings: list[str] = []
    lines: list[tuple[int, str]] = []
    for m in re.finditer(r"^- \[[ Xx]\] (T\d+[a-z]?)\b(.*)$", tasks_md_text, re.MULTILINE):
        lines.append((m.start(), m.group(0)))

    # Index each producer kind to its first-occurrence task position.
    download_pos: dict[str, int] = {}
    mkdir_pos: dict[str, int] = {}
    path_token_re = re.compile(r"[\w./-]+/[\w./-]+|[\w-]+\.\w+")

    produce_download = re.compile(r"\b(download|fetch|retrieve|pull|acquire)\b", re.IGNORECASE)
    consume_use = re.compile(r"\b(train|use|load|read|process|evaluate|analyze)\b", re.IGNORECASE)
    produce_mkdir = re.compile(r"\b(create|mkdir|initialize|scaffold|set up|setup)\b.*\b(dir|directory|folder)\b", re.IGNORECASE)
    write_into = re.compile(r"\b(write|save|store|output|emit|generate)\b", re.IGNORECASE)

    def _tokens(text: str) -> set[str]:
        return {t.strip("./").lower() for t in path_token_re.findall(text)}

    # First pass: record producer positions.
    for idx, (_pos, line) in enumerate(lines):
        if produce_download.search(line):
            for tok in _tokens(line):
                download_pos.setdefault(tok, idx)
        if produce_mkdir.search(line):
            for tok in _tokens(line):
                mkdir_pos.setdefault(tok, idx)

    # Second pass: a consumer referencing a producer token must come after it.
    for idx, (_pos, line) in enumerate(lines):
        toks = _tokens(line)
        if consume_use.search(line) and not produce_download.search(line):
            for tok in toks:
                p = download_pos.get(tok)
                if p is not None and p > idx:
                    findings.append(
                        f"FR-010: task #{idx} uses {tok!r} before its "
                        f"download at task #{p} (consumer-before-producer)"
                    )
        if write_into.search(line) and not produce_mkdir.search(line):
            for tok in toks:
                p = mkdir_pos.get(tok)
                if p is not None and p > idx:
                    findings.append(
                        f"FR-010: task #{idx} writes into {tok!r} before its "
                        f"directory is created at task #{p}"
                    )
    return findings


def constitution_check_ok(plan_md_text: str, constitution_md_text: str) -> tuple[bool, list[str]]:
    """FR-020 / SC-002: plan.md MUST have a Constitution Check section that
    references every numbered principle in the constitution.

    Returns (ok, unaddressed_principles).
    """
    # Locate a "Constitution Check" section in plan.md.
    if not re.search(r"(?im)^#{1,6}.*constitution\s+check", plan_md_text):
        return False, ["<no Constitution Check section>"]

    principles = re.findall(
        r"(?im)^#{1,6}\s*(?:principle\s+)?([IVXLCDM]+|\d+)\b|^\s*[-*]?\s*\*\*(?:principle\s+)?([IVXLCDM]+|\d+)[.:)]",
        constitution_md_text,
    )
    nums = {a or b for a, b in principles if (a or b)}
    if not nums:
        # Fall back to "Principle X" mentions anywhere in the constitution.
        nums = set(re.findall(r"(?i)\bprinciple\s+([IVXLCDM]+|\d+)\b", constitution_md_text))
    if not nums:
        return True, []  # nothing numbered to check against

    unaddressed = [n for n in sorted(nums) if not re.search(rf"(?i)\b{re.escape(n)}\b", plan_md_text)]
    return (not unaddressed), unaddressed


# ──────────────────────────────────────────────────────────────────────
# T008 — preflight
# ──────────────────────────────────────────────────────────────────────

def _preflight(project_id: str) -> dict[str, Any]:
    """Fail-fast preflight (<10s). Exits 2 on any failure (FR-019 decline too)."""
    # (a) Dartmouth key resolvable + populate env for the subprocess.
    from llmxive.credentials import load_dartmouth_key
    if not load_dartmouth_key():
        _exit_2("preflight (a): Dartmouth key not in env or "
                "~/.config/llmxive/credentials.toml; populate it and re-run")
    from llmxive.backends.dartmouth import _ensure_api_key_env
    _ensure_api_key_env()

    # (b) llmxive runner importable.
    rc = subprocess.run(
        [sys.executable, "-m", "llmxive", "run", "--help"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if rc.returncode != 0:
        _exit_2(f"preflight (b): `python -m llmxive run --help` failed "
                f"(rc={rc.returncode}); fix the import error:\n{rc.stderr[-1500:]}")

    # (c) state YAML exists with current_stage == clarified (FR-019 decline).
    proj_state = REPO_ROOT / "state" / "projects" / f"{project_id}.yaml"
    if not proj_state.is_file():
        _exit_2(f"preflight (c) [{project_id}]: state YAML not found at {proj_state}")
    ydata = yaml.safe_load(proj_state.read_text(encoding="utf-8")) or {}
    stage = ydata.get("current_stage")
    if stage != "clarified":
        if stage in TERMINAL_OK_STAGES or stage in {
            "planned", "tasked", "analyze_in_progress", "in_progress",
        }:
            _exit_2(
                f"preflight (c) [{project_id}]: current_stage={stage!r} — already "
                f"past this phase (FR-019). Phase 4 entry stage is 'clarified'; "
                f"decline to re-run. Roll the project back to 'clarified' to re-validate."
            )
        _exit_2(
            f"preflight (c) [{project_id}]: current_stage={stage!r}, expected "
            f"'clarified'. The project has not completed Phase 3."
        )

    # (d) spec.md exists and is real (not a template).
    fdir = _feature_dir(project_id)
    if fdir is None:
        _exit_2(f"preflight (d) [{project_id}]: no projects/{project_id}/specs/001-*/ dir")
    spec_md = fdir / "spec.md"
    if not spec_md.is_file():
        _exit_2(f"preflight (d) [{project_id}]: spec.md missing at {spec_md}")
    from llmxive.speckit._real_only_guard import is_real
    if not is_real(spec_md, repo_root=REPO_ROOT / "projects" / project_id):
        _exit_2(f"preflight (d) [{project_id}]: spec.md at {spec_md} classifies as "
                f"TEMPLATE (Phase-3 output is not real); re-run Phase 3 first")

    # (e) inspections dir writable.
    insp = INSPECTIONS_DIR / project_id
    insp.mkdir(parents=True, exist_ok=True)
    probe = insp / ".preflight_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        _exit_2(f"preflight (e): inspections dir not writable: {exc}")

    print(f"[validate_phase4] preflight ok (5/5) for {project_id} (stage={stage})",
          file=sys.stderr)
    return {"feature_dir": fdir, "state_yaml_pre": ydata}


# ──────────────────────────────────────────────────────────────────────
# T009 — FR-018 reset
# ──────────────────────────────────────────────────────────────────────

def reset_phase4_outputs(project_id: str) -> list[str]:
    """FR-018: delete Phase-4 outputs under specs/001-*/, PRESERVE spec.md.

    Also clears the .specify/memory tasker/human-input markers. Returns the
    repo-relative paths removed (for the inspection ``reset_artifacts`` field).
    """
    removed: list[str] = []
    fdir = _feature_dir(project_id)
    if fdir is not None:
        for name in PHASE4_OUTPUT_FILES:
            p = fdir / name
            if p.is_file():
                p.unlink()
                removed.append(str(p.relative_to(REPO_ROOT)))
        for dname in PHASE4_OUTPUT_DIRS:
            d = fdir / dname
            if d.is_dir():
                shutil.rmtree(d)
                removed.append(str(d.relative_to(REPO_ROOT)))
    memdir = REPO_ROOT / "projects" / project_id / ".specify" / "memory"
    for name in PHASE4_MEMORY_FILES:
        p = memdir / name
        if p.is_file():
            p.unlink()
            removed.append(str(p.relative_to(REPO_ROOT)))
    return removed


# ──────────────────────────────────────────────────────────────────────
# T010 — run invocation
# ──────────────────────────────────────────────────────────────────────

def _snapshot_spec_md(project_id: str) -> str:
    fdir = _feature_dir(project_id)
    spec = (fdir / "spec.md") if fdir else None
    return spec.read_text(encoding="utf-8") if (spec and spec.is_file()) else ""


def _run_pipeline(project_id: str) -> dict[str, Any]:
    """Run `python -m llmxive run --project <id> --max-tasks 2`.

    Sets LLMXIVE_INSPECTION_DIR so the planner+tasker write inspection records.
    --max-tasks 2 = one Planner step + one Tasker step (the Tasker's internal
    analyze loop runs within its single invocation).
    """
    insp_subdir = INSPECTIONS_DIR / project_id
    insp_subdir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "LLMXIVE_INSPECTION_DIR": str(insp_subdir)}
    started = datetime.now(UTC)
    proc = subprocess.run(
        [sys.executable, "-m", "llmxive", "run", "--project", project_id, "--max-tasks", "2"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), env=env, timeout=1900,
    )
    ended = datetime.now(UTC)
    run_id = None
    m = re.search(r"run[_-]?id[=: ]+([0-9a-fA-F-]{8,})", (proc.stdout or "") + (proc.stderr or ""))
    if m:
        run_id = m.group(1)
    return {
        "returncode": proc.returncode,
        "run_id": run_id,
        "duration_s": (ended - started).total_seconds(),
        "stderr_tail": (proc.stderr or "").splitlines()[-15:],
        "stdout_tail": (proc.stdout or "").splitlines()[-15:],
    }


# ──────────────────────────────────────────────────────────────────────
# T011 — post-run verification
# ──────────────────────────────────────────────────────────────────────

def _read_state_stage(project_id: str) -> str:
    proj_state = REPO_ROOT / "state" / "projects" / f"{project_id}.yaml"
    ydata = yaml.safe_load(proj_state.read_text(encoding="utf-8")) or {}
    return ydata.get("current_stage", "<unknown>")


def _tasker_rounds_from_inspection(project_id: str) -> list[dict[str, Any]]:
    rec_path = INSPECTIONS_DIR / project_id / "tasker.json"
    if not rec_path.is_file():
        return []
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    return rec.get("rounds", []) or []


def _verify(project_id: str, spec_md_before: str) -> tuple[list[str], dict[str, Any]]:
    """Return (findings, evidence). Empty findings == passed."""
    findings: list[str] = []
    evidence: dict[str, Any] = {}

    stage = _read_state_stage(project_id)
    evidence["final_state"] = stage
    if stage not in TERMINAL_OK_STAGES:
        findings.append(
            f"stage chain did not reach a terminal Phase-4 stage: current={stage!r} "
            f"(expected one of {sorted(TERMINAL_OK_STAGES)})"
        )

    fdir = _feature_dir(project_id)
    if fdir is None:
        findings.append("no specs/001-*/ feature dir after run")
        return findings, evidence

    # Five plan artifacts + tasks.md present (only enforced when not held).
    if stage == "analyzed":
        for name in PLAN_PLAIN_ARTIFACTS:
            if not (fdir / name).is_file():
                findings.append(f"missing plan artifact: {name}")
        contracts_dir = fdir / "contracts"
        has_contract = contracts_dir.is_dir() and (
            any(contracts_dir.glob("*.yaml")) or any(contracts_dir.glob("*.yml"))
        )
        if not has_contract:
            findings.append("missing contracts/*.yaml")
        tasks = fdir / "tasks.md"
        if not tasks.is_file():
            findings.append("missing tasks.md")
        else:
            n_tasks = len(_TASK_LINE_RE.findall(tasks.read_text(encoding="utf-8")))
            evidence["task_count"] = n_tasks
            if n_tasks < 10:
                findings.append(f"FR-009/SC-004: tasks.md has {n_tasks} T### lines (need >=10)")

    # FR-018: spec.md preserved.
    spec_md_after = _snapshot_spec_md(project_id)
    # The Tasker's Mode-B may legitimately rewrite spec.md to resolve a
    # finding; FR-018 only protects the reset step (before the run). We assert
    # spec.md still exists and is non-empty; the FR-012 check below guards
    # against weakening rewrites.
    if not spec_md_after.strip():
        findings.append("FR-018: spec.md is empty/missing after run")

    # FR-010 ordering.
    tasks = fdir / "tasks.md"
    if tasks.is_file():
        ordering = check_task_ordering(tasks.read_text(encoding="utf-8"))
        evidence["ordering_findings"] = ordering
        findings.extend(ordering)

    # FR-012 constraint-non-deletion across Mode-B spec.md rewrites.
    rounds = _tasker_rounds_from_inspection(project_id)
    evidence["analyze_rounds"] = len(rounds)
    before_fr, before_sc = fr_sc_counts(spec_md_before)
    running_fr, running_sc = before_fr, before_sc
    for r in rounds:
        if "spec.md" in (r.get("files_rewritten") or []):
            # The round's diff tells us the new spec.md; recompute from after.
            after_text = spec_md_after  # final state is the cumulative result
            af_fr, af_sc = fr_sc_counts(after_text)
            if af_fr < running_fr or af_sc < running_sc:
                findings.append(
                    f"FR-012: Mode-B round {r.get('round_index')} reduced spec.md "
                    f"FR/SC count ({running_fr}/{running_sc} -> {af_fr}/{af_sc}); "
                    f"a constraint was weakened/deleted. Inspection: "
                    f"specs/014-…/inspections/{project_id}/tasker.json"
                )
            running_fr, running_sc = af_fr, af_sc

    # FR-020 Constitution Check.
    plan_md = fdir / "plan.md"
    constitution = REPO_ROOT / "projects" / project_id / ".specify" / "memory" / "constitution.md"
    if stage == "analyzed" and plan_md.is_file() and constitution.is_file():
        ok, unaddressed = constitution_check_ok(
            plan_md.read_text(encoding="utf-8"),
            constitution.read_text(encoding="utf-8"),
        )
        if not ok:
            findings.append(
                f"FR-020/SC-002: plan.md Constitution Check missing or leaves "
                f"principles unaddressed: {unaddressed}"
            )

    return findings, evidence


# ──────────────────────────────────────────────────────────────────────
# Per-project orchestration
# ──────────────────────────────────────────────────────────────────────

def _rollback_to_clarified(project_id: str) -> bool:
    """--force re-validation helper: roll a project that has advanced past
    'clarified' (e.g. a prior partial run left it at 'planned') back to the
    Phase-4 entry stage so the FULL planner→tasker chain can be re-validated
    from the canonical starting state. The transition is logged to the
    project's history.jsonl by ``project_store.save``. Returns True if a
    rollback was performed. Does NOT weaken the default FR-019 decline — it is
    an explicit, opt-in re-validation action.
    """
    from llmxive.state import project as project_store

    proj = project_store.load(project_id, repo_root=REPO_ROOT)
    if proj.current_stage.value == "clarified":
        return False
    prev = proj.current_stage.value
    project_store.update(
        project_id,
        {"current_stage": "clarified", "failed_stage": None},
        repo_root=REPO_ROOT,
    )
    print(f"[validate_phase4] {project_id}: --force rolled back {prev} -> clarified "
          f"for re-validation", file=sys.stderr)
    return True


def _run_one_project(project_id: str, *, reset: bool, force: bool = False) -> dict[str, Any]:
    if force:
        _rollback_to_clarified(project_id)
    _preflight(project_id)
    reset_artifacts = reset_phase4_outputs(project_id) if reset else []
    print(f"[validate_phase4] {project_id}: reset removed {len(reset_artifacts)} Phase-4 output(s)",
          file=sys.stderr)

    spec_md_before = _snapshot_spec_md(project_id)
    run_info = _run_pipeline(project_id)
    print(f"[validate_phase4] {project_id}: pipeline rc={run_info['returncode']} "
          f"({run_info['duration_s']:.1f}s)", file=sys.stderr)

    findings, evidence = _verify(project_id, spec_md_before)

    # Augment inspection records with reset_artifacts (host-side knowledge).
    for agent in ("planner", "tasker"):
        rec_path = INSPECTIONS_DIR / project_id / f"{agent}.json"
        if rec_path.is_file():
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            if agent == "planner":
                rec["reset_artifacts"] = list(reset_artifacts)
            rec_path.write_text(
                json.dumps(rec, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    passed = len(findings) == 0 and evidence.get("final_state") == "analyzed"
    return {
        "project_id": project_id,
        "final_state": evidence.get("final_state", "<unknown>"),
        "status": "passed" if passed else ("held" if evidence.get("final_state") in {"human_input_needed", "held"} else "failed"),
        "findings": findings,
        "evidence": evidence,
        "reset_artifacts": reset_artifacts,
        "run_info": run_info,
    }


# ──────────────────────────────────────────────────────────────────────
# T022 — carry-forward.yaml
# ──────────────────────────────────────────────────────────────────────

def _git_head() -> str:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(REPO_ROOT))
    head = sha.stdout.strip() if sha.returncode == 0 else "HEAD"
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(REPO_ROOT))
    if dirty.returncode == 0 and dirty.stdout.strip():
        return "HEAD"
    return head


def emit_carry_forward(results: list[dict[str, Any]]) -> Path:
    """Write specs/014-…/carry-forward.yaml per contracts/carry-forward.md."""
    head = _git_head()
    manifest: dict[str, Any] = {
        "spec": "014-phase4-plan-tasks-testing",
        "generated_at": datetime.now(UTC).isoformat(),
        "final_commit": head,
        "projects": [],
    }
    for r in results:
        rounds = r["evidence"].get("analyze_rounds", 0)
        insp = f"specs/014-…/inspections/{r['project_id']}/tasker.json"
        if r["status"] == "passed":
            j = (
                f"Phase 4 ran cleanly on {r['project_id']}; final state "
                f"{r['final_state']} in {rounds} analyze round(s)."
            )
        else:
            j = (
                f"Phase 4 {r['status']} on {r['project_id']}: final state "
                f"{r['final_state']}. {('; '.join(r['findings']) or 'see inspection')}. "
                f"Inspection: {insp}"
            )
        planner_outcome = "committed" if r["final_state"] in {"analyzed", "human_input_needed", "held"} else "failed"
        tasker_outcome = (
            "committed" if r["final_state"] == "analyzed"
            else ("escalated" if r["final_state"] in {"human_input_needed", "held"} else "failed")
        )
        manifest["projects"].append({
            "project_id": r["project_id"],
            "final_state": r["final_state"],
            "status": r["status"],
            "final_commit": head,
            "agents_run": [
                {"name": "planner", "iterations": 1, "final_outcome": planner_outcome},
                {"name": "tasker", "iterations": 1, "final_outcome": tasker_outcome, "analyze_rounds": rounds},
            ],
            "justification": j,
        })

    out_path = SPEC_DIR / "carry-forward.yaml"
    tmp = out_path.with_suffix(".yaml.tmp")
    tmp.write_text(
        yaml.safe_dump(manifest, sort_keys=False, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )
    os.replace(tmp, out_path)
    return out_path


# ──────────────────────────────────────────────────────────────────────
# T023 — phase-report.md
# ──────────────────────────────────────────────────────────────────────

def emit_phase_report(results: list[dict[str, Any]]) -> Path:
    """Write specs/014-…/phase-report.md per contracts/phase-report.md."""
    lines: list[str] = ["# Phase 4 Validation Report", ""]

    # 1. Summary
    lines.append("## Summary")
    lines.append("")
    for r in results:
        rounds = r["evidence"].get("analyze_rounds", 0)
        lines.append(
            f"- `{r['project_id']}`: clarified → {r['final_state']} "
            f"(planner: {'committed' if r['final_state'] != 'failed' else 'failed'}, "
            f"tasker: {r['status']}, {rounds} analyze round(s))"
        )
    lines.append("")

    # 2. FR → evidence
    lines.append("## FR → evidence")
    lines.append("")
    lines.append("|FR|Evidence|")
    lines.append("|-|-|")
    fr_evidence = {
        "FR-005": "PlannerAgent.write_artifacts → assert_artifact_set_complete; test_phase4_plan_tasks.py::TestArtifactSet",
        "FR-006": "assert_urls_reachable (local http.server test); plan-time gate in write_artifacts",
        "FR-007": "assert_data_model_contracts_consistent; TestDataModelConsistency",
        "FR-009": "tasks.md ≥10 T### lines (see per-project task_count)",
        "FR-010": "check_task_ordering on produced tasks.md",
        "FR-012": "fr_sc_counts non-decrease across Mode-B spec.md rewrites",
        "FR-013": "tasker analyze loop bounded by TASKER_MAX_REVISION_ROUNDS",
        "FR-018": "reset_phase4_outputs preserves spec.md",
        "FR-020": "constitution_check_ok over plan.md",
    }
    for fr, ev in fr_evidence.items():
        lines.append(f"|{fr}|{ev}|")
    lines.append("")

    # 3. Quality-gate findings
    lines.append("## Quality-gate findings")
    lines.append("")
    any_findings = False
    for r in results:
        if r["findings"]:
            any_findings = True
            lines.append(f"### {r['project_id']}")
            for f in r["findings"]:
                lines.append(f"- {f} (inspection: `specs/014-…/inspections/{r['project_id']}/tasker.json`)")
            lines.append("")
    if not any_findings:
        lines.append("No findings — every quality gate passed on every canonical.")
        lines.append("")

    # 4. Mode-B coverage (SC-011)
    lines.append("## Mode-B coverage (SC-011)")
    lines.append("")
    for r in results:
        rounds = r["evidence"].get("analyze_rounds", 0)
        mode_b_real = any(
            (rd.get("verdict") not in (None, "clean")) or rd.get("files_rewritten")
            for rd in _tasker_rounds_from_inspection(r["project_id"])
        )
        if mode_b_real:
            lines.append(
                f"- `{r['project_id']}`: Mode-B exercised on REAL content "
                f"({rounds} round(s)); see `specs/014-…/inspections/{r['project_id']}/tasker.json`."
            )
        else:
            lines.append(
                f"- `{r['project_id']}`: clean in {rounds} round(s) (no real Mode-B). "
                f"Mode-B is covered by the synthetic regression tests "
                f"`tests/integration/test_phase4_plan_tasks.py` (FR-016 d/e/f)."
            )
    lines.append("")
    lines.append(
        "Regardless of the real runs, the synthetic-input regression tests "
        "(`test_phase4_plan_tasks.py`, FR-016 d/e/f) cover the Mode-B diff-leak, "
        "header-preservation, and analyze-loop-cap escalation paths."
    )
    lines.append("")

    # 5. Carry-forward
    lines.append("## Carry-forward")
    lines.append("")
    for r in results:
        lines.append(f"- `{r['project_id']}`: {r['status']} (final_state: {r['final_state']}). See `carry-forward.yaml`.")
    lines.append("")

    out_path = SPEC_DIR / "phase-report.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="validate_phase4.py", description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--project", help="Run Phase 4 on a single canonical")
    grp.add_argument("--all", action="store_true", help="Run Phase 4 on both canonicals")
    ap.add_argument("--no-reset", action="store_true", help="Skip the FR-018 reset")
    ap.add_argument("--force", action="store_true",
                    help="Roll a project that advanced past 'clarified' (e.g. a prior "
                         "partial run) back to 'clarified' before validating — for "
                         "reproducible re-validation. Does not change default FR-019 behavior.")
    ap.add_argument("--emit-carry-forward", action="store_true",
                    help="Also emit carry-forward.yaml + phase-report.md (implicit with --all)")
    args = ap.parse_args(argv)

    if not args.project and not args.all:
        ap.error("must specify either --project <id> or --all")

    project_ids = list(CANONICAL_PROJECTS) if args.all else [args.project]
    reset = not args.no_reset
    results: list[dict[str, Any]] = []
    for pid in project_ids:
        results.append(_run_one_project(pid, reset=reset, force=args.force))

    if args.all or args.emit_carry_forward:
        cf = emit_carry_forward(results)
        pr = emit_phase_report(results)
        print(f"[validate_phase4] carry-forward → {cf.relative_to(REPO_ROOT)}", file=sys.stderr)
        print(f"[validate_phase4] phase-report → {pr.relative_to(REPO_ROOT)}", file=sys.stderr)

    passed = sum(1 for r in results if r["status"] == "passed")
    failed = len(results) - passed
    for r in results:
        print(f"[validate_phase4] {r['project_id']}: {r['status']} (final={r['final_state']})"
              + (f" findings={r['findings']}" if r["findings"] else ""), file=sys.stderr)
    print(f"[validate_phase4] {len(results)} project(s): {passed} passed, {failed} not-passed",
          file=sys.stderr)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
