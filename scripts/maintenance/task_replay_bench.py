#!/usr/bin/env python3
"""Replay one implementer attempt on the task a finished run was stuck on.

A fresh acceptance run takes three hours and changes many things at once. This
takes the project exactly as a finished run left it, and for the first open
task asks the implementer model for N independent attempts. Each attempt is
applied to its own copy of the project by the real implementer (sandboxed
execution, ratchet and all), then judged by the real task verifier. The
variants compared on the same task are numbers of candidate replies per retry
(``LLMXIVE_RETRY_CANDIDATES``).

It is a measurement of single attempts, not an acceptance run: nothing it
produces is evidence that a project passes the pipeline.

    python scripts/maintenance/task_replay_bench.py RUN_DIR [RUN_DIR ...] \
        --samples 6 --variants 1,3 --out bench.json

RUN_DIR is the data directory of a finished acceptance run (it holds
``projects/<id>/`` and ``state/``). Needs the Dartmouth key and the receipt
signing key that the pipeline itself uses. Model calls are real.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLATFORM / "src"))


def _copy_run(run: Path, project_id: str, dest: Path) -> Path:
    """A private repo root holding the project, its state, and this platform's agents."""
    shutil.copytree(run / "projects" / project_id, dest / "projects" / project_id,
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"), symlinks=True)
    if (run / "state").is_dir():
        shutil.copytree(run / "state", dest / "state", symlinks=True)
    shutil.copytree(PLATFORM / "agents", dest / "agents")
    if (run / ".llmxive-venvs" / project_id).is_dir():  # reuse the built environment
        shutil.copytree(run / ".llmxive-venvs" / project_id, dest / ".llmxive-venvs" / project_id, symlinks=True)
    return dest / "projects" / project_id


def _attempt(run: Path, project_id: str, variant: str, model: str, keep: Path | None = None) -> dict:
    from llmxive.agents import task_verifier
    from llmxive.backends.router import chat_with_fallback
    from llmxive.speckit import scorecard
    from llmxive.speckit.implement_cmd import ImplementerAgent
    from llmxive.speckit.slash_command import SlashCommandContext
    from llmxive.types import BackendName

    root = Path(tempfile.mkdtemp(prefix="llmxive-bench-"))
    try:
        project = _copy_run(run, project_id, root)
        os.environ["LLMXIVE_REPO_ROOT"] = str(root)
        os.environ["LLMXIVE_RETRY_CANDIDATES"] = variant
        ctx = SlashCommandContext(
            project_id=project_id, project_dir=project, run_id="bench", task_id="bench", inputs=[],
            expected_outputs=[], prompt_template_path=root / "agents/prompts/implementer_research.md",
            default_backend=BackendName.DARTMOUTH, fallback_backends=[], default_model=model,
            prompt_version="bench", agent_name="implementer")
        agent = ImplementerAgent()
        mech = agent.mechanical_step(ctx)
        task = mech.get("next_task_id")
        if not task:
            return {"task": None}
        tasks_path = Path(mech["tasks_path"])
        memory = task_verifier.task_verification_state_path(project, tasks_path).parent
        before = scorecard.current(memory, task)
        messages = agent.build_prompt(ctx, mech)
        started = time.monotonic()
        reply = chat_with_fallback(messages, default_backend="dartmouth", fallback_backends=[], model=model)
        seconds = time.monotonic() - started
        agent.write_artifacts(ctx, mech, reply)
        after = scorecard.current(memory, task)
        improved, regressed = scorecard.delta(before, after)
        line = next((row for row in tasks_path.read_text(encoding="utf-8").splitlines()
                     if row.lstrip().startswith("- [") and task in row.split()[:4]), "")
        claimed = line.lstrip().startswith("- [X]")
        verdict = None
        if claimed:  # judged only when the implementer's own runs did not fail
            result = task_verifier.run_verification_pass(
                project, tasks_path,
                already_verified=task_verifier.verified_done_keys(project, tasks_path),
                spec_context=(tasks_path.parent / "spec.md").read_text(encoding="utf-8")
                if (tasks_path.parent / "spec.md").is_file() else "",
                notes_path=memory / "task_verifier_notes.md", state_path=memory / "task_verify.yaml",
                project_id=project_id, repo_root=root, model=model)
            row = next((r for r in reversed(scorecard.history(memory, task)) if "judge" in r["values"]), None)
            verdict = None if row is None else row["values"]["judge"]
            reason = next((why for key, why in result["rejected"] if key == task), "")
        else:
            reason = line[-200:]
        return {
            "task": task, "variant": variant, "model": reply.model,
            "prompt_chars": sum(len(m.content) for m in messages), "reply_chars": len(reply.text),
            "seconds": round(seconds, 1), "claimed": claimed, "kept": after.get("kept"),
            "improved": improved, "regressed": regressed, "accepted": verdict == 1,
            "reason": " ".join(str(reason).split())[:300],
            "candidates": after.get("candidates", 1), "candidates_claimed": after.get("candidates_claimed"),
        }
    finally:
        if keep is not None:  # the attempt's records, for reading why it went as it did
            keep.mkdir(parents=True, exist_ok=True)
            tag = f"{run.name}-{variant}-{time.time_ns()}"
            for kept_dir in ("code/.tasks", ".specify/memory"):
                source = root / "projects" / project_id / kept_dir
                if source.is_dir():
                    shutil.copytree(source, keep / tag / kept_dir)
        shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--variants", default="1,3", help="candidate replies per retry, comma-separated")
    parser.add_argument("--model", default="openai.gpt-oss-120b")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--keep", type=Path, help="directory to keep each attempt's logs and memory in")
    args = parser.parse_args()

    from llmxive.credentials import load_dartmouth_key
    from llmxive.results.receipt import load_signing_key
    os.environ["DARTMOUTH_CHAT_API_KEY"] = load_dartmouth_key()
    os.environ["LLMXIVE_RECEIPT_KEY"] = load_signing_key().decode()
    os.environ["LLMXIVE_PAID_OPT_IN"] = "0"

    rows = []
    for run in args.runs:
        projects = sorted(p.name for p in (run / "projects").iterdir() if p.is_dir() and p.name.startswith("PROJ-"))
        for project_id in projects:
            for variant in args.variants.split(","):
                for sample in range(args.samples):
                    try:
                        row = _attempt(run.resolve(), project_id, variant, args.model, args.keep)
                    except Exception as exc:  # one failed trial must not lose the others
                        row = {"task": "?", "variant": variant, "error": f"{type(exc).__name__}: {exc}"[:300]}
                    row.update(run=run.name, sample=sample)
                    rows.append(row)
                    print(json.dumps(row), flush=True)
                    if args.out:
                        args.out.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    print("\nrun | task | variant | n | claimed | kept | accepted | median prompt chars")
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        groups.setdefault((row["run"], row.get("task"), row.get("variant")), []).append(row)
    for (run_name, task, variant), items in groups.items():
        ok = [r for r in items if "error" not in r and r.get("task")]
        sizes = sorted(r["prompt_chars"] for r in ok) or [0]
        print(f"{run_name[-6:]} | {task} | {variant} | {len(items)} | {sum(r['claimed'] for r in ok)} | "
              f"{sum(r['kept'] != 0 for r in ok)} | {sum(r['accepted'] for r in ok)} | {sizes[len(sizes) // 2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
