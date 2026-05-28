#!/usr/bin/env python3
"""Run differential calibration for one stage against the spec-015
calibration set (T068 / FR-046).

Usage::

    python scripts/run_calibration.py --stage spec
    python scripts/run_calibration.py --stage tasks --model qwen.qwen3.5-122b
    python scripts/run_calibration.py --stage all --domain (unspecified)

Writes the adjudication report to
``specs/015-pipeline-convergence-protocol/calibration/reports/<stage>__<timestamp>.md``.

The script is designed to run in CI (GitHub Actions
``.github/workflows/spec015-calibration.yml``) — it consumes the
``DARTMOUTH_CHAT_API_KEY`` secret, runs against the on-disk calibration
set, and commits the produced report. Maintainer adjudication is done
afterward in the report file's checklist (FR-046 differential + manual
rule — no fixed over-flag threshold).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.calibration.differential import CalibrationRun, adjudicate
from llmxive.calibration.injectors import Injection
from llmxive.convergence.engine import run_convergence
from llmxive.convergence.llm_reviewer import build_panel
from llmxive.convergence.reviewspecs import (
    build_paper_implement_reviewspec,
    build_paper_plan_reviewspec,
    build_paper_spec_reviewspec,
    build_paper_tasks_reviewspec,
    build_plan_reviewspec,
    build_spec_reviewspec,
    build_tasks_reviewspec,
)
from llmxive.convergence.types import ConvergenceResult

REPO_ROOT = Path(__file__).resolve().parent.parent
CALIBRATION_ROOT = REPO_ROOT / "specs" / "015-pipeline-convergence-protocol" / "calibration"
REPORTS_DIR = CALIBRATION_ROOT / "reports"


# Stage → (build_*_reviewspec, panel-lens list, on-disk calibration-set subdir)
_STAGES: dict[str, tuple[object, list[str], str]] = {
    "spec": (
        build_spec_reviewspec,
        ["requirements_coverage", "internal_consistency", "testability", "scope"],
        "spec",
    ),
    "plan": (
        build_plan_reviewspec,
        ["methodology", "spec_coverage", "data_resources", "plan_consistency"],
        "plan",
    ),
    "tasks": (
        build_tasks_reviewspec,
        ["coverage", "ordering", "executability", "constraint_preservation"],
        "tasks",
    ),
    "paper_spec": (
        build_paper_spec_reviewspec,
        ["reader_scenario_coverage", "claims_supported",
         "required_sections_figures", "scope_vs_research"],
        "paper",  # paper-spec uses the same calibration positives as other paper steps
    ),
    "paper_plan": (
        build_paper_plan_reviewspec,
        ["paper_structure", "spec_section_coverage", "plan_constitution_consistency"],
        "paper",
    ),
    "paper_tasks": (
        build_paper_tasks_reviewspec,
        ["coverage", "ordering", "executability", "constraint_preservation"],
        "paper",
    ),
    "paper_implement": (
        build_paper_implement_reviewspec,
        # The paper_implement registry uses the 12-panel; we run a
        # subset relevant to the calibration negative (nonexistent_citation).
        ["claim_accuracy", "scientific_evidence", "writing_quality",
         "figure_critic"],
        "paper",
    ),
}


def _load_entries(stage_subdir: str) -> list[tuple[str, str, str | None]]:
    """Return ``[(label, text, expected_lens_or_None), ...]`` from the
    on-disk calibration set for ``stage_subdir``."""
    stage_dir = CALIBRATION_ROOT / stage_subdir
    if not stage_dir.is_dir():
        raise FileNotFoundError(f"calibration subdir not found: {stage_dir}")
    out: list[tuple[str, str, str | None]] = []
    for md in sorted(stage_dir.glob("*.md")):
        label = md.stem
        sidecar = md.with_suffix(".label.json")
        meta = json.loads(sidecar.read_text()) if sidecar.exists() else {}
        out.append((label, md.read_text(), meta.get("expected_lens")))
    return out


def _make_backend(model: str, max_tokens: int) -> DartmouthBackend:
    """Build a Dartmouth backend with per-call max_tokens injected."""
    b = DartmouthBackend()
    orig_chat = b.chat

    def chat_with_budget(messages, model=None, **kw):  # type: ignore[no-untyped-def]
        # Default kwargs the engine + reviser pass through.
        kw.setdefault("max_tokens", max_tokens)
        return orig_chat(messages, model=model, **kw)

    b.chat = chat_with_budget  # type: ignore[assignment]
    return b


@dataclass
class _Outcome:
    label: str
    expected_lens: str | None
    result: ConvergenceResult
    elapsed_s: float


def _run_one(
    *, stage: str, label: str, text: str, backend: object, model: str,
) -> ConvergenceResult:
    build_fn, lenses, _ = _STAGES[stage]
    spec = build_fn(  # type: ignore[operator]
        backend=backend, repo_root=REPO_ROOT, project_id="PROJ-000-calibration",
        model=model,
    )
    spec.reviewers = build_panel(
        stage=spec.stage, lenses=lenses, backend=backend, repo_root=REPO_ROOT,
        model=model,
    )
    artifacts_key = _artifact_key_for_stage(stage)
    artifacts = {artifacts_key: text}
    return run_convergence(spec, artifacts)


def _artifact_key_for_stage(stage: str) -> str:
    return {
        "spec": "specs/000-calib/spec.md",
        "plan": "specs/000-calib/plan.md",
        "tasks": "specs/000-calib/tasks.md",
        "paper_spec": "paper/specs/000-calib/spec.md",
        "paper_plan": "paper/specs/000-calib/plan.md",
        "paper_tasks": "paper/specs/000-calib/tasks.md",
        "paper_implement": "paper/source/main.tex",
    }[stage]


def run_stage(*, stage: str, model: str, domain: str, max_tokens: int,
              timeout_s: float) -> Path:
    """Run differential calibration for one stage; write report; return path."""
    if stage not in _STAGES:
        raise SystemExit(
            f"unknown stage {stage!r}; expected one of {list(_STAGES)!r}"
        )
    _, _, subdir = _STAGES[stage]
    entries = _load_entries(subdir)
    if not entries:
        raise SystemExit(f"no calibration entries found for stage {stage!r}")

    backend = _make_backend(model=model, max_tokens=max_tokens)
    outcomes: list[_Outcome] = []
    print(f"[calibration] stage={stage!r}  entries={len(entries)}  model={model!r}",
          flush=True)
    for label, text, expected_lens in entries:
        t0 = time.monotonic()
        try:
            result = _run_one(
                stage=stage, label=label, text=text, backend=backend, model=model,
            )
            elapsed = time.monotonic() - t0
            print(f"[calibration] {label!s:30}  converged={result.converged}  "
                  f"concerns={len(result.concern_history)}  ({elapsed:.1f}s)",
                  flush=True)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            print(f"[calibration] {label!s:30}  ERROR after {elapsed:.1f}s: {exc}",
                  flush=True)
            result = ConvergenceResult(
                stage=stage, converged=False, rounds_used=0,
            )
        outcomes.append(_Outcome(
            label=label, expected_lens=expected_lens,
            result=result, elapsed_s=elapsed,
        ))
        if elapsed > timeout_s:
            print(f"[calibration] timeout budget exceeded ({elapsed:.1f}s > "
                  f"{timeout_s}s); skipping remaining entries.", flush=True)
            break

    runs = _outcomes_to_calibration_runs(stage, outcomes)
    report = adjudicate(runs, domain=domain)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = REPORTS_DIR / f"{stage}__{ts}.md"
    out_path.write_text(report.to_markdown(domain=domain))
    print(f"[calibration] report → {out_path.relative_to(REPO_ROOT)}", flush=True)
    return out_path


def _outcomes_to_calibration_runs(
    stage: str, outcomes: list[_Outcome],
) -> list[CalibrationRun]:
    """Pair the positive with each negative to build CalibrationRuns."""
    positive = next((o for o in outcomes if o.label == "positive"), None)
    if positive is None:
        raise SystemExit(
            f"no `positive.md` entry found for stage {stage!r}; "
            "calibration requires a clean baseline."
        )
    runs: list[CalibrationRun] = []
    for o in outcomes:
        if o.label == "positive":
            continue
        injector_name = o.label.removeprefix("negative_")
        injection = Injection(
            text="<<from disk>>",
            expected_lens=o.expected_lens or "<unknown>",
            description=f"Injector: {injector_name}",
            original=positive.result.stage,
        )
        runs.append(CalibrationRun(
            injector_name=injector_name,
            injection=injection,
            clean_result=positive.result,
            injected_result=o.result,
        ))
    return runs


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", default="spec", choices=[*list(_STAGES), "all"],
                   help="which stage to calibrate (or 'all')")
    p.add_argument("--model", default="qwen.qwen3.5-122b",
                   help="Dartmouth model id")
    p.add_argument("--max-tokens", type=int, default=8192,
                   help="per-call max_tokens (reasoning models need ≥4096)")
    p.add_argument("--domain", default="(unspecified)",
                   help="domain label written into the report header")
    p.add_argument("--timeout", type=float, default=1800.0,
                   help="per-stage soft timeout in seconds (skip remaining "
                        "entries after this; default 30 min)")
    args = p.parse_args(argv)

    stages = list(_STAGES) if args.stage == "all" else [args.stage]
    for stage in stages:
        run_stage(
            stage=stage, model=args.model, domain=args.domain,
            max_tokens=args.max_tokens, timeout_s=args.timeout,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
