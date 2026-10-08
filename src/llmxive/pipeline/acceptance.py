"""Full-pipeline acceptance runner: real research and a paper, never a one-step proxy.

Run in an isolated repository with real backends. Completion stops before public
publication/sign-off; no DOI is minted by this runner. Rejection, no progress,
and exhausted budgets fail rather than count as successful E2E acceptance.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from llmxive.pipeline import graph
from llmxive.state import project as store
from llmxive.types import Stage


def run(project_id: str, repo: Path, *, max_steps: int = 50, budget_s: float = 7200) -> dict:
    # Match the production CLI's scientific safeguards; do not test an easier path.
    for flag in ("LLMXIVE_GROUNDING_GUARD", "LLMXIVE_CLAIM_LAYER", "LLMXIVE_CLAIM_FILL"):
        os.environ[flag] = "1"
    output = repo / "state" / "acceptance" / f"{project_id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    trail = json.loads(output.read_text()).get("steps", []) if output.exists() else []
    result = {"project_id": project_id, "status": "running", "steps": trail}
    project_dir = repo / "projects" / project_id
    terminal_failures = {
        Stage.BLOCKED,
        Stage.AGENT_BLOCKED,
        Stage.VALIDATOR_REJECTED,
        Stage.HUMAN_INPUT_NEEDED,
        Stage.REVIEWED_PREPRINT,
    }
    try:
        for step in range(max_steps):
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
            print(f"[acceptance] {step + 1}: {project.current_stage.value}", flush=True)
            before = project.current_stage.value
            tick = time.monotonic()
            updated = graph.run_one_step(project, repo_root=repo)
            trail.append(
                {
                    "step": len(trail) + 1,
                    "before": before,
                    "after": updated.current_stage.value,
                    "elapsed_s": round(time.monotonic() - tick, 3),
                }
            )
            output.write_text(json.dumps(result, indent=2))
        else:
            raise RuntimeError("full-pipeline acceptance step limit exhausted")
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
