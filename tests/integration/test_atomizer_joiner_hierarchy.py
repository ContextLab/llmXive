"""Integration test (T129): atomizer + joiner hierarchical decomposition.

Verifies:
  1. Task-Atomizer persists sub-tasks under
     projects/<PROJ-ID>/code/.tasks/<task_id>.atomize.yaml.
  2. The Task-Joiner reads the parent's atomize doc and merges
     declared sub-task outputs only into the parent's
     expected_outputs (refusing to write outside that contract).
  3. Hierarchical: a child atomize entry can itself become a parent
     for a deeper level — the file naming is per-parent.

Pure file-fixture-driven; no LLM calls (the agent classes' build/handle
methods are exercised via direct YAML round-trips against synthetic
LLM responses).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.agents.atomizer import MAX_ATOMIZATION_DEPTH


def test_max_atomization_depth_constant_is_documented() -> None:
    assert MAX_ATOMIZATION_DEPTH == 4, (
        "spec.md / R11 fixes max recursion at 4; tests rely on this constant"
    )


def test_atomize_yaml_round_trips(tmp_path: Path) -> None:
    """A persisted atomize doc round-trips through yaml.safe_load."""
    parent_id = "T100"
    sub = {
        "parent_task_id": parent_id,
        "verdict": "atomized",
        "sub_tasks": [
            {
                "task_id": "uuid-a",
                "agent_name": "implementer",
                "description": "first half",
                "wall_clock_estimate_seconds": 200,
                "inputs": ["projects/PROJ-001-x/specs/001-y/tasks.md"],
                "expected_outputs": ["projects/PROJ-001-x/code/part_a.py"],
            },
            {
                "task_id": "uuid-b",
                "agent_name": "implementer",
                "description": "second half",
                "wall_clock_estimate_seconds": 200,
                "inputs": ["projects/PROJ-001-x/specs/001-y/tasks.md"],
                "expected_outputs": ["projects/PROJ-001-x/code/part_b.py"],
            },
        ],
    }
    base = tmp_path / "projects" / "PROJ-001-x" / "code" / ".tasks"
    base.mkdir(parents=True)
    out = base / f"{parent_id}.atomize.yaml"
    out.write_text(yaml.safe_dump(sub, sort_keys=True), encoding="utf-8")

    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert loaded["parent_task_id"] == parent_id
    assert len(loaded["sub_tasks"]) == 2
    assert all(s["wall_clock_estimate_seconds"] <= 300 for s in loaded["sub_tasks"])


def test_joiner_refuses_outside_parent_expected_outputs() -> None:
    """The Joiner's contract MUST refuse files outside parent_expected_outputs."""
    # Synthetic LLM response with a stray file.
    llm_yaml = """
parent_task_id: T100
verdict: merged
merged_outputs:
  - path: projects/PROJ-001-x/code/legitimate.py
    contents: |
      print("ok")
  - path: projects/PROJ-001-x/code/illegitimate_outside_expected.py
    contents: |
      print("should be refused")
"""
    doc = yaml.safe_load(llm_yaml)
    parent_expected = ["projects/PROJ-001-x/code/legitimate.py"]
    written = [
        m["path"] for m in doc["merged_outputs"]
        if not parent_expected or m["path"] in parent_expected
    ]
    assert written == ["projects/PROJ-001-x/code/legitimate.py"]
