#!/usr/bin/env python3
"""Phase 3 (Spec Kit Specify → Clarify) validation harness.

Drives the two Phase 3 agents (`specifier`, `clarifier`) end-to-end on
the two carry-forward canonicals from spec 004 (PROJ-261 + PROJ-262),
captures verbatim per-agent I/O to ``specs/011-…/inspections/`` via
``llmxive.speckit._inspection.capture`` (triggered by the env-gated hook
in :mod:`llmxive.speckit.slash_command`), checks post-conditions, and
emits ``specs/011-…/carry-forward.yaml`` per the spec-011 contracts.

See ``specs/011-phase3-specify-clarify-testing/contracts/regression-tests.md``
for the formal CLI contract this script implements.

Usage:
    python scripts/validate_phase3.py --project PROJ-261-…
    python scripts/validate_phase3.py --all
    python scripts/validate_phase3.py --emit-carry-forward
    python scripts/validate_phase3.py --all --no-reset

Exit codes:
    0 — all selected projects reached `clarified` and passed all post-conditions
    1 — at least one project failed validation (carry-forward.yaml still written)
    2 — preflight failed (no state changes attempted)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = REPO_ROOT / "specs" / "011-phase3-specify-clarify-testing"
INSPECTIONS_DIR = SPEC_DIR / "inspections"

CANONICAL_PROJECTS = (
    "PROJ-261-evaluating-the-impact-of-code-duplicatio",
    "PROJ-262-predicting-molecular-dipole-moments-with",
)


# ──────────────────────────────────────────────────────────────────────
# T009 — preflight
# ──────────────────────────────────────────────────────────────────────

def _preflight(project_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Run the 7 preflight checks from plan.md Section V.

    Exits 2 with a clear stderr message on any failure. Returns a per-
    project metadata dict the rest of the harness threads through.
    """
    # (a) Dartmouth key resolvable + populate env for subprocess inheritance
    from llmxive.credentials import load_dartmouth_key
    key = load_dartmouth_key()
    if not key:
        _exit_2("preflight (a): Dartmouth key not in env or ~/.config/llmxive/credentials.toml")
    # Make sure os.environ carries it so the subprocess in T013 sees it.
    from llmxive.backends.dartmouth import _ensure_api_key_env
    _ensure_api_key_env()

    # (b) llmxive runner importable
    rc = subprocess.run(
        [sys.executable, "-m", "llmxive", "run", "--help"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if rc.returncode != 0:
        _exit_2(f"preflight (b): `python -m llmxive run --help` failed (rc={rc.returncode})\n{rc.stderr}")

    # (c)(d)(e)(f) per-project checks
    metadata: dict[str, dict[str, Any]] = {}
    for pid in project_ids:
        proj_state = REPO_ROOT / "state" / "projects" / f"{pid}.yaml"
        if not proj_state.is_file():
            _exit_2(f"preflight (c) [{pid}]: state YAML not found at {proj_state}")
        ydata = yaml.safe_load(proj_state.read_text(encoding="utf-8"))
        stage = (ydata or {}).get("current_stage")
        if stage != "project_initialized":
            _exit_2(
                f"preflight (c) [{pid}]: current_stage={stage!r}, expected 'project_initialized'. "
                "If you want to re-run validation, roll the project back manually."
            )

        proj_dir = REPO_ROOT / "projects" / pid
        idea_files = list((proj_dir / "idea").glob("*.md")) if (proj_dir / "idea").is_dir() else []
        if not idea_files or not any(f.stat().st_size > 0 for f in idea_files):
            _exit_2(f"preflight (d) [{pid}]: no non-empty idea/*.md under {proj_dir / 'idea'}")

        cnf = proj_dir / ".specify" / "scripts" / "bash" / "create-new-feature.sh"
        if not cnf.is_file() or not os.access(cnf, os.X_OK):
            _exit_2(
                f"preflight (e) [{pid}]: {cnf.relative_to(REPO_ROOT)} missing or not executable "
                "(Phase 2 contract violation — re-run project_initializer)"
            )

        gitstat = subprocess.run(
            ["git", "status", "--porcelain", "--", f"projects/{pid}/"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        if gitstat.returncode != 0:
            _exit_2(f"preflight (f) [{pid}]: `git status` failed: {gitstat.stderr}")
        if gitstat.stdout.strip():
            _exit_2(
                f"preflight (f) [{pid}]: uncommitted maintainer changes under projects/{pid}/:\n"
                f"{gitstat.stdout}"
                "Commit or stash before re-running validation."
            )

        metadata[pid] = {
            "state_yaml_pre": ydata,
            "idea_files": [str(f.relative_to(REPO_ROOT)) for f in idea_files],
        }

    # (g) inspections dir writable
    INSPECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    probe = INSPECTIONS_DIR / ".preflight_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        _exit_2(f"preflight (g): inspections dir not writable: {exc}")

    print(f"[validate_phase3] preflight ok (7/7 checks) for {len(project_ids)} project(s)",
          file=sys.stderr)
    return metadata


def _exit_2(msg: str) -> None:
    print(f"[validate_phase3] STOP: {msg}", file=sys.stderr)
    sys.exit(2)


# ──────────────────────────────────────────────────────────────────────
# T010 — reset (FR-015)
# ──────────────────────────────────────────────────────────────────────

def _reset_project_specs(project_id: str) -> list[str]:
    """Wipe pre-existing ``projects/<id>/specs/<n>-<slug>/`` directories.

    Returns the project-relative paths removed. Also clears
    ``state/projects/<id>.yaml::speckit_research_dir`` if it pointed at
    any removed path.
    """
    proj_dir = REPO_ROOT / "projects" / project_id
    specs_dir = proj_dir / "specs"
    if not specs_dir.is_dir():
        return []
    removed: list[str] = []
    for sub in sorted(specs_dir.iterdir()):
        if sub.is_dir() and re.match(r"^\d{3}-", sub.name):
            shutil.rmtree(sub)
            removed.append(str(sub.relative_to(REPO_ROOT)))

    if removed:
        # Clear speckit_research_dir if it pointed at a removed path.
        from llmxive.state import project as project_store
        try:
            project = project_store.load(project_id, repo_root=REPO_ROOT)
            current_pointer = project.speckit_research_dir
            if current_pointer and any(current_pointer.startswith(p) for p in removed):
                project = project.model_copy(update={
                    "speckit_research_dir": None,
                    "updated_at": datetime.now(timezone.utc),
                })
                project_store.save(project, repo_root=REPO_ROOT)
        except Exception as exc:  # noqa: BLE001 — log and continue
            print(f"[validate_phase3] WARN: couldn't clear speckit_research_dir for {project_id}: {exc}",
                  file=sys.stderr)
    return removed


# ──────────────────────────────────────────────────────────────────────
# T013 — single-agent orchestrator
# ──────────────────────────────────────────────────────────────────────

def _snapshot_spec_md(project_id: str) -> dict[str, str]:
    """Return {relpath: content} for every spec.md currently under projects/<id>/specs/."""
    proj_dir = REPO_ROOT / "projects" / project_id
    out: dict[str, str] = {}
    for spec_md in proj_dir.glob("specs/*/spec.md"):
        out[str(spec_md.relative_to(REPO_ROOT))] = spec_md.read_text(encoding="utf-8")
    return out


def _run_one_agent(
    project_id: str,
    agent_label: str,
    reset_artifacts: list[str],
) -> dict[str, Any]:
    """Drive one agent (specifier OR clarifier) via the production CLI.

    Sets LLMXIVE_INSPECTION_DIR so the env-gated hook in slash_command.py
    writes the verbatim-IO record. Snapshots spec.md before+after to
    compute file_diffs, then augments the record on disk.

    Returns: dict with outcome, duration_s, inspection_path, error.
    """
    started = datetime.now(timezone.utc)
    before_snapshot = _snapshot_spec_md(project_id)

    insp_subdir = INSPECTIONS_DIR / project_id
    insp_subdir.mkdir(parents=True, exist_ok=True)

    env = {**os.environ, "LLMXIVE_INSPECTION_DIR": str(insp_subdir)}
    proc = subprocess.run(
        [sys.executable, "-m", "llmxive", "run", "--project", project_id, "--max-tasks", "1"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), env=env, timeout=900,
    )
    ended = datetime.now(timezone.utc)
    after_snapshot = _snapshot_spec_md(project_id)

    # Read the state YAML to determine outcome.
    from llmxive.state import project as project_store
    project = project_store.load(project_id, repo_root=REPO_ROOT)
    new_stage = project.current_stage.value if hasattr(project.current_stage, "value") else str(project.current_stage)

    insp_path = insp_subdir / f"{agent_label}.json"
    record: dict[str, Any] | None = None
    if insp_path.is_file():
        record = json.loads(insp_path.read_text(encoding="utf-8"))
        # Augment with host-side file_diffs and reset_artifacts.
        file_diffs: list[dict[str, str]] = []
        all_paths = set(before_snapshot) | set(after_snapshot)
        for p in sorted(all_paths):
            b = before_snapshot.get(p, "")
            a = after_snapshot.get(p, "")
            if b != a:
                file_diffs.append({"path": p, "before": b, "after": a})
        record["file_diffs"] = file_diffs
        record["reset_artifacts"] = list(reset_artifacts) if agent_label == "specifier" else []
        insp_path.write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return {
        "agent": agent_label,
        "stage_after": new_stage,
        "duration_s": (ended - started).total_seconds(),
        "inspection_path": str(insp_path.relative_to(REPO_ROOT)) if insp_path.exists() else None,
        "subprocess_rc": proc.returncode,
        "subprocess_stderr_tail": (proc.stderr or "").splitlines()[-10:],
        "record_outcome": (record or {}).get("outcome"),
    }


# ──────────────────────────────────────────────────────────────────────
# T014 — per-project orchestrator
# ──────────────────────────────────────────────────────────────────────

def _run_one_project(project_id: str, *, reset: bool) -> dict[str, Any]:
    """End-to-end Phase 3 for one project: reset → Specifier → Clarifier → post-conditions."""
    reset_artifacts = _reset_project_specs(project_id) if reset else []
    print(f"[validate_phase3] {project_id}: reset {len(reset_artifacts)} pre-existing spec dir(s)",
          file=sys.stderr)

    agents_run: list[dict[str, Any]] = []
    # Specifier
    spec_result = _run_one_agent(project_id, "specifier", reset_artifacts)
    agents_run.append(spec_result)
    print(f"[validate_phase3] {project_id}: specifier {spec_result['record_outcome'] or 'unknown'} "
          f"({spec_result['duration_s']:.1f}s), stage={spec_result['stage_after']}",
          file=sys.stderr)

    final_state = spec_result["stage_after"]
    # Clarifier — only run if Specifier succeeded (stage advanced to 'specified')
    if final_state == "specified":
        clar_result = _run_one_agent(project_id, "clarifier", [])
        agents_run.append(clar_result)
        print(f"[validate_phase3] {project_id}: clarifier {clar_result['record_outcome'] or 'unknown'} "
              f"({clar_result['duration_s']:.1f}s), stage={clar_result['stage_after']}",
              file=sys.stderr)
        final_state = clar_result["stage_after"]

    # T015 — post-conditions
    passed, failures, warnings = _check_postconditions(project_id, agents_run)
    if passed:
        print(f"[validate_phase3] {project_id}: post-conditions PASS", file=sys.stderr)
    else:
        print(f"[validate_phase3] {project_id}: post-conditions FAIL — {failures}", file=sys.stderr)
    for w in warnings:
        print(f"[validate_phase3] {project_id}: WARNING — {w}", file=sys.stderr)

    return {
        "project_id": project_id,
        "final_state": final_state,
        "agents_run": agents_run,
        "passed": passed,
        "failures": failures,
        "warnings": warnings,
    }


# ──────────────────────────────────────────────────────────────────────
# T015 — post-conditions
# ──────────────────────────────────────────────────────────────────────

def _check_postconditions(
    project_id: str, agents_run: list[dict[str, Any]]
) -> tuple[bool, list[str], list[str]]:
    """Return (passed, failures, warnings). See task T015 for the 6 checks."""
    failures: list[str] = []
    warnings: list[str] = []

    # (a) current_stage == clarified
    from llmxive.state import project as project_store
    project = project_store.load(project_id, repo_root=REPO_ROOT)
    stage = project.current_stage.value if hasattr(project.current_stage, "value") else str(project.current_stage)
    if stage != "clarified":
        failures.append(f"current_stage is {stage!r}, expected 'clarified'")

    # (b) spec.md exists
    proj_dir = REPO_ROOT / "projects" / project_id
    spec_files = list(proj_dir.glob("specs/*/spec.md"))
    if not spec_files:
        failures.append("no spec.md found under projects/<id>/specs/*/")
        return False, failures, warnings
    spec_md = spec_files[0]
    spec_text = spec_md.read_text(encoding="utf-8")

    # (c) SC-002 counts
    fr_count = len(re.findall(r"^\s*[-*]\s*\*\*FR-\d+\*\*", spec_text, re.MULTILINE))
    sc_count = len(re.findall(r"^\s*[-*]\s*\*\*SC-\d+\*\*", spec_text, re.MULTILINE))
    story_count = len(re.findall(r"^###\s+User Story", spec_text, re.MULTILINE))
    if fr_count < 4:
        failures.append(f"SC-002 violation: spec.md has {fr_count} FR-NNN bullets, expected ≥4")
    if sc_count < 3:
        failures.append(f"SC-002 violation: spec.md has {sc_count} SC-NNN bullets, expected ≥3")
    if story_count < 2:
        failures.append(f"SC-002 violation: spec.md has {story_count} user stories, expected ≥2")

    # (d) SC-003 zero NEEDS CLARIFICATION markers
    marker_count = len(re.findall(r"\[NEEDS CLARIFICATION", spec_text))
    if marker_count > 0:
        failures.append(f"SC-003 violation: spec.md has {marker_count} [NEEDS CLARIFICATION] marker(s) remaining")

    # (e) FR-010 — run-log entries present
    log_root = REPO_ROOT / "state" / "run-log"
    if log_root.is_dir():
        found_agents: set[str] = set()
        for jsonl in log_root.rglob("*.jsonl"):
            try:
                for line in jsonl.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if entry.get("project_id") == project_id and entry.get("agent_name") in {"specifier", "clarifier"}:
                        found_agents.add(entry["agent_name"])
            except OSError:
                continue
        expected_agents = {a["agent"] for a in agents_run}
        missing = expected_agents - found_agents
        if missing:
            failures.append(f"FR-010 violation: no run-log entries for agents: {sorted(missing)}")

    # (f) FR-006 cap-flag — count markers in Specifier's spec.md (pre-Clarifier)
    spec_inspection = INSPECTIONS_DIR / project_id / "specifier.json"
    if spec_inspection.is_file():
        rec = json.loads(spec_inspection.read_text(encoding="utf-8"))
        # Find the spec.md "after" content from file_diffs
        for diff in rec.get("file_diffs", []):
            if diff.get("path", "").endswith("/spec.md"):
                pre_clarifier_text = diff.get("after", "")
                pre_count = len(re.findall(r"\[NEEDS CLARIFICATION", pre_clarifier_text))
                if pre_count > 3:
                    warnings.append(
                        f"FR-006: Specifier produced {pre_count} [NEEDS CLARIFICATION] markers "
                        f"(cap is 3); Clarifier resolved them but the cap is meant to be enforced upstream"
                    )
                break

    return len(failures) == 0, failures, warnings


# ──────────────────────────────────────────────────────────────────────
# T023/T024 — carry-forward manifest
# ──────────────────────────────────────────────────────────────────────

def _emit_carry_forward(results: list[dict[str, Any]]) -> Path:
    """Write specs/011-…/carry-forward.yaml per contracts/carry-forward.md."""
    git_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    head = git_sha.stdout.strip() if git_sha.returncode == 0 else "HEAD"
    # Detect uncommitted changes — if any, fall back to "HEAD" sentinel
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if dirty.returncode == 0 and dirty.stdout.strip():
        print(f"[validate_phase3] WARN: working tree has uncommitted changes; using 'HEAD' sentinel in carry-forward.yaml",
              file=sys.stderr)
        head = "HEAD"

    manifest: dict[str, Any] = {
        "spec": "011-phase3-specify-clarify-testing",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "final_commit": head,
        "projects": [],
    }
    for r in results:
        agent_entries = []
        for a in r["agents_run"]:
            agent_entries.append({
                "name": a["agent"],
                "iterations": 1,
                "final_outcome": a.get("record_outcome") or "unknown",
            })
        # Build justification
        if r["passed"]:
            j = (
                f"Phase 3 ran cleanly on {r['project_id']}. Both agents committed; final state {r['final_state']}. "
                f"Inspection records at specs/011-…/inspections/{r['project_id']}/. "
                f"Ready for Phase 4."
            )
            if r["warnings"]:
                j += f" Warnings: {'; '.join(r['warnings'])}"
        else:
            j = (
                f"Phase 3 FAILED on {r['project_id']}. Final state: {r['final_state']}. "
                f"Failures: {'; '.join(r['failures'])}. "
                f"Inspection records at specs/011-…/inspections/{r['project_id']}/ for diagnostic."
            )
        manifest["projects"].append({
            "project_id": r["project_id"],
            "final_state": r["final_state"],
            "final_commit": head,
            "audited_iter_id": r["project_id"],
            "agents_run": agent_entries,
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
# T008 — CLI entry point
# ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="validate_phase3.py", description=__doc__.splitlines()[0])
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--project", help="Run Phase 3 on a single canonical (PROJ-261-… or PROJ-262-…)")
    grp.add_argument("--all", action="store_true", help="Run Phase 3 on both canonicals (sequentially)")
    ap.add_argument("--emit-carry-forward", action="store_true",
                    help="Also emit carry-forward.yaml (implicit with --all)")
    ap.add_argument("--no-reset", action="store_true",
                    help="Skip the FR-015 reset (preserves any pre-existing specs/<n>-<slug>/)")
    args = ap.parse_args(argv)

    if not args.project and not args.all:
        ap.error("must specify either --project <id> or --all")

    project_ids = list(CANONICAL_PROJECTS) if args.all else [args.project]
    _preflight(project_ids)

    reset = not args.no_reset
    results: list[dict[str, Any]] = []
    for pid in project_ids:
        results.append(_run_one_project(pid, reset=reset))

    if args.all or args.emit_carry_forward:
        cf_path = _emit_carry_forward(results)
        print(f"[validate_phase3] carry-forward → {cf_path.relative_to(REPO_ROOT)}",
              file=sys.stderr)

    passed_count = sum(1 for r in results if r["passed"])
    failed_count = len(results) - passed_count
    print(f"[validate_phase3] validated {len(results)} project(s): {passed_count} passed, {failed_count} failed",
          file=sys.stderr)
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
