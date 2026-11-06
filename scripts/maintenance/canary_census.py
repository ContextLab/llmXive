#!/usr/bin/env python3
"""Tabulate acceptance (canary) runs so fixes are judged against all of them.

    python scripts/maintenance/canary_census.py /private/tmp/llmxive-canary-fresh-*

For each run directory this reads only what the run left behind:

* ``state/acceptance/<project>.json`` -- the step trail, outcome and outages;
* ``projects/<project>/specs/*/tasks.md`` -- tasks accepted at the end;
* ``projects/<project>/.specify/memory/task_verify.ledger.jsonl`` -- what each
  verification decision was (present for runs made after the ledger existed).

It prints one row per run and then totals: how runs ended, how often a run
left implementation for planning, where the time went, and what the strikes
against tasks were. Nothing is written.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

_TASK_RE = re.compile(r"^- \[(.)\]", re.M)


def read_run(run: Path) -> dict | None:
    """One run's facts, or ``None`` when the directory holds no acceptance result."""
    results = sorted(run.glob("state/acceptance/*.json"))
    if not results:
        return None
    result = json.loads(results[0].read_text(encoding="utf-8"))
    project = run / "projects" / results[0].stem
    steps = result.get("steps", [])
    minutes: collections.Counter[str] = collections.Counter()
    for step in steps:
        minutes[step["before"]] += step["elapsed_s"] / 60
    marks: list[str] = []
    for tasks in project.glob("specs/*/tasks.md"):
        marks = _TASK_RE.findall(tasks.read_text(encoding="utf-8", errors="replace"))
    kinds: collections.Counter[str] = collections.Counter()
    ledger = project / ".specify/memory/task_verify.ledger.jsonl"
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                kinds[json.loads(line)["kind"]] += 1
            except (ValueError, KeyError, TypeError):
                continue
    stages = [step["after"] for step in steps]
    return {
        "run": run.name,
        "steps": len(steps),
        "minutes": round(sum(minutes.values())),
        "status": result.get("status", "?"),
        "reason": (result.get("reason") or "")[:48],
        "research_complete": "research_complete" in stages,
        "paper_complete": "paper_complete" in stages,
        "kickbacks": sum(1 for step in steps if step["before"] == "in_progress"
                         and step["after"] not in ("in_progress", "research_complete")),
        "idle_steps": sum(1 for step in steps if step["before"] == "in_progress" and step["elapsed_s"] < 30),
        "outages": len(result.get("outages", [])),
        "tasks": f"{sum(mark in 'xX' for mark in marks)}/{len(marks)}",
        "last": stages[-1] if stages else "",
        "stage_minutes": minutes,
        "ledger": kinds,
    }


def render(runs: list[dict]) -> str:
    out = ["run|steps|min|status|research|paper|kickbacks|idle|outages|tasks|last|reason", "|-|-|-|-|-|-|-|-|-|-|-|-|"]
    for run in runs:
        out.append("|".join(str(value) for value in (
            run["run"], run["steps"], run["minutes"], run["status"],
            "yes" if run["research_complete"] else "no", "yes" if run["paper_complete"] else "no",
            run["kickbacks"], run["idle_steps"], run["outages"], run["tasks"], run["last"], run["reason"])))
    total = len(runs)
    out.append("")
    out.append(f"runs: {total}; reached research_complete: {sum(r['research_complete'] for r in runs)}; "
               f"reached paper_complete: {sum(r['paper_complete'] for r in runs)}; "
               f"kicked back at least once: {sum(r['kickbacks'] > 0 for r in runs)}")
    stage_minutes: collections.Counter[str] = collections.Counter()
    ledger: collections.Counter[str] = collections.Counter()
    for run in runs:
        stage_minutes.update(run["stage_minutes"])
        ledger.update(run["ledger"])
    spent = sum(stage_minutes.values()) or 1
    out.append("time by stage: " + ", ".join(
        f"{stage} {100 * minutes / spent:.0f}%" for stage, minutes in stage_minutes.most_common(6)))
    out.append("verification decisions: " + (", ".join(f"{kind} {count}" for kind, count in ledger.most_common())
                                              or "no ledger in these runs"))
    return "\n".join(out)


def main(argv: list[str]) -> int:
    runs = [facts for facts in (read_run(Path(arg)) for arg in argv if Path(arg).is_dir()) if facts]
    if not runs:
        print("no acceptance results found; pass run directories", file=sys.stderr)
        return 2
    print(render(runs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
