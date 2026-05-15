#!/usr/bin/env python3
"""Extract E2 GRPO phase timing evidence from local run artifacts.

The script intentionally reads only local artifacts recorded under
/root/docs/paper/MinT-Closing and writes compact CSV/JSONL summaries next to
itself. It does not query live services.
"""

from __future__ import annotations

import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROVENANCE_IN = Path(
    "/root/code/mindlab_paper/papers/mint/raw_data/"
    "e2_grpo_population_scaling/provenance.csv"
)

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
HMS_RE = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})$")
HTTP_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)Z"
    r".*?\[http\.request\] completed method=\S+ route=(\S+)"
    r" status_code=(\d+) elapsed_ms=([0-9.]+)"
)

TRAIN_START_RE = re.compile(r"^>> train step=(\d+)/(\d+).* total_elapsed=([0-9:]+)")
ROLLOUT_DONE_RE = re.compile(r"^\+\+ train step=(\d+)/(\d+).* step_elapsed=([0-9:]+)")
STEP_DONE_RE = re.compile(
    r"^== train step=(\d+)/(\d+).* step_time=([0-9.]+)s.* total_elapsed=([0-9:]+)"
)
CHECKPOINT_RE = re.compile(r"^@@ checkpoint step=(\d+)/(\d+)")
EVAL_START_RE = re.compile(r"^>> eval_start step=(\d+)/(\d+)")
BG_EVAL_DONE_RE = re.compile(r"^== bg_eval_step_\d+_pool complete=.* elapsed=([0-9:]+)")
EVAL_POOL_RE = re.compile(r"^>> eval_pool submit=.* elapsed=([0-9:]+)")
EVAL_PROGRESS_RE = re.compile(r"^(?:\+\+|!!) eval\[.* done=(\d+)/(\d+) elapsed=([0-9:]+)")

ROUTES_OF_INTEREST = (
    "/api/v1/asample",
    "/api/v1/forward_backward",
    "/api/v1/optim_step",
    "/api/v1/save_weights",
    "/api/v1/save_weights_for_sampler",
)


def parse_hms(value: str) -> float | None:
    match = HMS_RE.search(value.strip())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    return float(hours * 3600 + minutes * 60 + seconds)


def iso(ts: float | None) -> str:
    if ts is None or (isinstance(ts, float) and math.isnan(ts)):
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def duration(start: float | None, end: float | None) -> float | None:
    if start is None or end is None:
        return None
    return round(end - start, 3)


def read_measured_provenance() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with PROVENANCE_IN.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["baseline_type"] == "measured":
                rows.append(row)
    return rows


def parse_task(task_dir: Path) -> dict[str, object] | None:
    run_json = task_dir / "run.json"
    console = task_dir / "console.log"
    if not run_json.exists() or not console.exists():
        return None

    data = json.loads(run_json.read_text())
    start = float(data["started_at_unix"])
    end = float(data["ended_at_unix"]) if data.get("ended_at_unix") else None
    steps: dict[int, dict[str, float]] = {}
    checkpoint_after: float | None = None
    eval_start: float | None = None
    eval_done: float | None = None
    final_eval_pool_start: float | None = None
    final_eval_done: float | None = None
    last_step_done: float | None = None
    in_final_eval = False

    for raw in console.read_text(errors="ignore").splitlines():
        line = raw.strip()

        match = TRAIN_START_RE.match(line)
        if match:
            step = int(match.group(1))
            elapsed = parse_hms(match.group(3))
            if elapsed is not None:
                steps.setdefault(step, {})["start"] = start + elapsed

        match = ROLLOUT_DONE_RE.match(line)
        if match:
            step = int(match.group(1))
            elapsed = parse_hms(match.group(3))
            if elapsed is not None and step in steps and "start" in steps[step]:
                steps[step]["rollout_done"] = steps[step]["start"] + elapsed

        match = STEP_DONE_RE.match(line)
        if match:
            step = int(match.group(1))
            elapsed = parse_hms(match.group(4))
            if elapsed is not None:
                done = start + elapsed
                steps.setdefault(step, {})["done"] = done
                last_step_done = done

        if CHECKPOINT_RE.match(line):
            checkpoint_after = last_step_done

        if EVAL_START_RE.match(line):
            eval_start = checkpoint_after or last_step_done

        match = BG_EVAL_DONE_RE.match(line)
        if match and eval_start:
            elapsed = parse_hms(match.group(1))
            if elapsed is not None:
                eval_done = eval_start + elapsed

        if line.startswith(">> periodic_eval_final_step_cached"):
            in_final_eval = True

        match = EVAL_POOL_RE.match(line)
        if match and in_final_eval:
            final_eval_pool_start = eval_done

        match = EVAL_PROGRESS_RE.match(line)
        if match and in_final_eval and final_eval_pool_start:
            elapsed = parse_hms(match.group(3))
            if elapsed is not None:
                final_eval_done = final_eval_pool_start + elapsed

    metrics = task_dir / "eval" / "metrics.jsonl"
    if metrics.exists():
        lines = [line for line in metrics.read_text().splitlines() if line.strip()]
        if lines:
            try:
                last = json.loads(lines[-1])
                if last.get("completed_at_unix"):
                    eval_done = float(last["completed_at_unix"])
            except json.JSONDecodeError:
                pass

    step_rows = []
    rollout_sum = 0.0
    update_sum = 0.0
    for step in sorted(steps):
        item = steps[step]
        step_start = item.get("start")
        rollout_done = item.get("rollout_done")
        step_done = item.get("done")
        if step_start is not None and rollout_done is not None:
            rollout_sum += rollout_done - step_start
        if rollout_done is not None and step_done is not None:
            update_sum += step_done - rollout_done
        step_rows.append(
            {
                "step": step,
                "step_start_unix": step_start,
                "rollout_done_unix": rollout_done,
                "step_done_unix": step_done,
            }
        )

    train_starts = [v["start"] for v in steps.values() if "start" in v]
    train_ends = [v["done"] for v in steps.values() if "done" in v]

    return {
        "task": task_dir.name,
        "task_start_unix": start,
        "task_end_unix": end,
        "train_start_unix": min(train_starts) if train_starts else start,
        "train_end_unix": max(train_ends) if train_ends else None,
        "rollout_sum_s": round(rollout_sum, 3),
        "update_sum_s": round(update_sum, 3),
        "export_start_unix": checkpoint_after,
        "eval_start_unix": eval_start,
        "eval_done_unix": eval_done,
        "final_eval_done_unix": final_eval_done,
        "step_rows": step_rows,
        "rollout_update_split_available": rollout_sum > 0 or update_sum > 0,
    }


def parse_server_api(run_dir: Path) -> dict[str, dict[str, object]]:
    server_log = run_dir / "server.log"
    result: dict[str, dict[str, object]] = {}
    if not server_log.exists():
        return result

    for raw in server_log.read_text(errors="ignore").splitlines():
        line = ANSI_RE.sub("", raw)
        match = HTTP_RE.search(line)
        if not match:
            continue
        timestamp, route, status, elapsed_ms_text = match.groups()
        if route not in ROUTES_OF_INTEREST:
            continue
        elapsed_ms = float(elapsed_ms_text)
        end = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc).timestamp()
        start = end - elapsed_ms / 1000.0
        item = result.setdefault(
            route,
            {
                "route": route,
                "count": 0,
                "first_start_unix": None,
                "last_end_unix": None,
                "sum_elapsed_s": 0.0,
                "max_elapsed_s": 0.0,
            },
        )
        item["count"] = int(item["count"]) + 1
        item["sum_elapsed_s"] = float(item["sum_elapsed_s"]) + elapsed_ms / 1000.0
        item["max_elapsed_s"] = max(float(item["max_elapsed_s"]), elapsed_ms / 1000.0)
        current_start = item["first_start_unix"]
        current_end = item["last_end_unix"]
        item["first_start_unix"] = start if current_start is None else min(float(current_start), start)
        item["last_end_unix"] = end if current_end is None else max(float(current_end), end)

    for item in result.values():
        item["sum_elapsed_s"] = round(float(item["sum_elapsed_s"]), 3)
        item["max_elapsed_s"] = round(float(item["max_elapsed_s"]), 3)
    return result


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> None:
    provenance = read_measured_provenance()
    run_rows: list[dict[str, object]] = []
    task_rows: list[dict[str, object]] = []
    step_rows: list[dict[str, object]] = []
    api_rows: list[dict[str, object]] = []

    for prov in provenance:
        run_dir = Path(prov["source_run_dir"])
        task_items = []
        for task_dir in sorted((run_dir / "tasks").glob("grpo_*")):
            parsed = parse_task(task_dir)
            if parsed:
                task_items.append(parsed)

        if not task_items:
            continue

        run_start = min(float(t["task_start_unix"]) for t in task_items)
        run_end = max(float(t["task_end_unix"]) for t in task_items if t["task_end_unix"] is not None)
        train_start = min(float(t["train_start_unix"]) for t in task_items)
        train_end_values = [float(t["train_end_unix"]) for t in task_items if t["train_end_unix"] is not None]
        train_end = max(train_end_values) if train_end_values else None
        export_values = [float(t["export_start_unix"]) for t in task_items if t["export_start_unix"] is not None]
        eval_start_values = [float(t["eval_start_unix"]) for t in task_items if t["eval_start_unix"] is not None]
        eval_done_values = [float(t["eval_done_unix"]) for t in task_items if t["eval_done_unix"] is not None]

        run_base = {
            "model": prov["model"],
            "num_policies": int(prov["num_policies"]),
            "schedule": prov["schedule"],
            "baseline_type": prov["baseline_type"],
            "run_id": prov["source_run_id"],
            "source_run_dir": prov["source_run_dir"],
        }

        run_rows.append(
            {
                **run_base,
                "task_count": len(task_items),
                "run_start_utc": iso(run_start),
                "run_end_utc": iso(run_end),
                "run_wall_s": duration(run_start, run_end),
                "train_start_utc": iso(train_start),
                "train_end_utc": iso(train_end),
                "train_window_s": duration(train_start, train_end),
                "rollout_sum_task_s": round(sum(float(t["rollout_sum_s"]) for t in task_items), 3),
                "update_sum_task_s": round(sum(float(t["update_sum_s"]) for t in task_items), 3),
                "rollout_update_split_available": all(
                    bool(t["rollout_update_split_available"]) for t in task_items
                ),
                "export_start_utc": iso(min(export_values) if export_values else None),
                "eval_start_utc": iso(min(eval_start_values) if eval_start_values else None),
                "eval_done_utc": iso(max(eval_done_values) if eval_done_values else None),
                "eval_window_s": duration(
                    min(eval_start_values) if eval_start_values else None,
                    max(eval_done_values) if eval_done_values else None,
                ),
            }
        )

        for task in task_items:
            task_base = {
                **run_base,
                "task": task["task"],
                "task_start_utc": iso(task["task_start_unix"]),
                "task_end_utc": iso(task["task_end_unix"]),
                "task_wall_s": duration(task["task_start_unix"], task["task_end_unix"]),
                "train_start_utc": iso(task["train_start_unix"]),
                "train_end_utc": iso(task["train_end_unix"]),
                "train_window_s": duration(task["train_start_unix"], task["train_end_unix"]),
                "rollout_sum_s": task["rollout_sum_s"],
                "update_sum_s": task["update_sum_s"],
                "rollout_update_split_available": task["rollout_update_split_available"],
                "export_start_utc": iso(task["export_start_unix"]),
                "eval_start_utc": iso(task["eval_start_unix"]),
                "eval_done_utc": iso(task["eval_done_unix"]),
                "eval_window_s": duration(task["eval_start_unix"], task["eval_done_unix"]),
                "final_eval_done_utc": iso(task["final_eval_done_unix"]),
            }
            task_rows.append(task_base)
            for step in task["step_rows"]:
                step_rows.append(
                    {
                        **run_base,
                        "task": task["task"],
                        "step": step["step"],
                        "step_start_utc": iso(step["step_start_unix"]),
                        "rollout_done_utc": iso(step["rollout_done_unix"]),
                        "step_done_utc": iso(step["step_done_unix"]),
                        "rollout_s": duration(step["step_start_unix"], step["rollout_done_unix"]),
                        "update_s": duration(step["rollout_done_unix"], step["step_done_unix"]),
                        "step_wall_s": duration(step["step_start_unix"], step["step_done_unix"]),
                    }
                )

        for route, item in parse_server_api(run_dir).items():
            api_rows.append(
                {
                    **run_base,
                    "route": route,
                    "count": item["count"],
                    "first_start_utc": iso(item["first_start_unix"]),
                    "last_end_utc": iso(item["last_end_unix"]),
                    "window_s": duration(item["first_start_unix"], item["last_end_unix"]),
                    "sum_elapsed_s": item["sum_elapsed_s"],
                    "max_elapsed_s": item["max_elapsed_s"],
                }
            )

    provenance_out = HERE / "provenance.csv"
    with provenance_out.open("w", newline="") as handle:
        fieldnames = list(provenance[0].keys()) if provenance else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(provenance)

    write_csv(
        HERE / "run_phase_summary.csv",
        run_rows,
        [
            "model",
            "num_policies",
            "schedule",
            "baseline_type",
            "task_count",
            "run_start_utc",
            "run_end_utc",
            "run_wall_s",
            "train_start_utc",
            "train_end_utc",
            "train_window_s",
            "rollout_sum_task_s",
            "update_sum_task_s",
            "rollout_update_split_available",
            "export_start_utc",
            "eval_start_utc",
            "eval_done_utc",
            "eval_window_s",
            "run_id",
            "source_run_dir",
        ],
    )
    write_csv(
        HERE / "task_phase_summary.csv",
        task_rows,
        [
            "model",
            "num_policies",
            "schedule",
            "baseline_type",
            "task",
            "task_start_utc",
            "task_end_utc",
            "task_wall_s",
            "train_start_utc",
            "train_end_utc",
            "train_window_s",
            "rollout_sum_s",
            "update_sum_s",
            "rollout_update_split_available",
            "export_start_utc",
            "eval_start_utc",
            "eval_done_utc",
            "eval_window_s",
            "final_eval_done_utc",
            "run_id",
            "source_run_dir",
        ],
    )
    write_csv(
        HERE / "step_phase_summary.csv",
        step_rows,
        [
            "model",
            "num_policies",
            "schedule",
            "baseline_type",
            "task",
            "step",
            "step_start_utc",
            "rollout_done_utc",
            "step_done_utc",
            "rollout_s",
            "update_s",
            "step_wall_s",
            "run_id",
            "source_run_dir",
        ],
    )
    write_csv(
        HERE / "api_phase_summary.csv",
        api_rows,
        [
            "model",
            "num_policies",
            "schedule",
            "baseline_type",
            "route",
            "count",
            "first_start_utc",
            "last_end_utc",
            "window_s",
            "sum_elapsed_s",
            "max_elapsed_s",
            "run_id",
            "source_run_dir",
        ],
    )

    for name, rows in {
        "run_phase_summary.jsonl": run_rows,
        "task_phase_summary.jsonl": task_rows,
        "step_phase_summary.jsonl": step_rows,
        "api_phase_summary.jsonl": api_rows,
    }.items():
        with (HERE / name).open("w") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
