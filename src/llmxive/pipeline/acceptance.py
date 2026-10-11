"""Full-pipeline acceptance runner: real research and a paper, never a one-step proxy.

Run in an isolated repository with real backends. Completion stops before public
publication/sign-off; no DOI is minted by this runner. Rejection, no progress,
and exhausted budgets fail rather than count as successful E2E acceptance.

A model outage is none of those. A scheduled production run meets
``BackendUnavailable`` by trying the project again on its next tick; this runner
waits and runs the same step again. The wait is charged to the wall-clock
budget, not to the step limit, and every outage is recorded in the result.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from llmxive.backends.base import BackendUnavailable
from llmxive.pipeline import graph
from llmxive.state import project as store
from llmxive.types import Stage


def run(project_id: str, repo: Path, *, max_steps: int = 50, budget_s: float = 7200,
        outage_wait_s: float = 300.0) -> dict:
    # Match the production CLI's scientific safeguards; do not test an easier path.
    for flag in ("LLMXIVE_GROUNDING_GUARD", "LLMXIVE_CLAIM_LAYER", "LLMXIVE_CLAIM_FILL"):
        os.environ[flag] = "1"
    output = repo / "state" / "acceptance" / f"{project_id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    trail = json.loads(output.read_text()).get("steps", []) if output.exists() else []
    outages: list[dict] = []
    result = {"project_id": project_id, "status": "running", "steps": trail, "outages": outages}
    project_dir = repo / "projects" / project_id
    terminal_failures = {
        Stage.BLOCKED,
        Stage.AGENT_BLOCKED,
        Stage.VALIDATOR_REJECTED,
        Stage.HUMAN_INPUT_NEEDED,
        Stage.REVIEWED_PREPRINT,
    }
    try:
        step = 0
        announced = -1
        while True:
            if step >= max_steps:
                raise RuntimeError("full-pipeline acceptance step limit exhausted")
            if time.monotonic() - started > budget_s:
                raise RuntimeError("full-pipeline acceptance budget exhausted")
            project = store.load(project_id, repo_root=repo)
            if project.current_stage in terminal_failures:
                raise RuntimeError(f"canary stopped at {project.current_stage.value}")
            if project.current_stage in {Stage.PAPER_ACCEPTED, Stage.AWAITING_PUBLICATION_SIGNOFF}:
                source = project_dir / "paper/source/main.tex"
                pdf = project_dir / "paper/pdf/main.pdf"
                if not source.is_file() or not pdf.is_file() or pdf.stat().st_size < 1000:
                    raise RuntimeError(
                        "accepted state lacks paper source or a nonempty compiled PDF"
                    )
                stages = {t["after"] for t in trail}
                if not {"research_complete", "research_accepted", "paper_complete"} <= stages:
                    raise RuntimeError("canary did not traverse both research and paper gates")
                result.update(status="accepted", paper=str(pdf.relative_to(repo)))
                break
            before = project.current_stage.value
            if announced != step:
                print(f"[acceptance] {step + 1}: {before}", flush=True)
                announced = step
            tick = time.monotonic()
            try:
                updated = graph.run_one_step(project, repo_root=repo)
            except BackendUnavailable as exc:
                outages.append({"stage": before, "reason": str(exc),
                                "elapsed_s": round(time.monotonic() - tick, 3)})
                output.write_text(json.dumps(result, indent=2))
                remaining = budget_s - (time.monotonic() - started)
                if remaining <= 0:
                    raise RuntimeError("full-pipeline acceptance budget exhausted") from exc
                wait = min(outage_wait_s, remaining)
                print(f"[acceptance] outage at {before}; step {step + 1} runs again in "
                      f"{wait:.0f}s: {str(exc)[:300]}", flush=True)
                time.sleep(wait)
                continue
            step += 1
            trail.append(
                {
                    "step": len(trail) + 1,
                    "before": before,
                    "after": updated.current_stage.value,
                    "elapsed_s": round(time.monotonic() - tick, 3),
                }
            )
            output.write_text(json.dumps(result, indent=2))
    except KeyboardInterrupt:
        result.update(status="interrupted", reason="operator stopped the run; acceptance is unproven")
        raise
    except Exception as exc:
        result.update(status="failed", reason=str(exc))
        raise
    finally:
        result["elapsed_s"] = round(time.monotonic() - started, 3)
        output.write_text(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--max-steps", type=int, default=50)
    args = parser.parse_args()
    print(json.dumps(run(args.project, args.repo.resolve(), max_steps=args.max_steps)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
