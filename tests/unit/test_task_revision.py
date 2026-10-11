"""One repeatedly rejected task is rewritten in place; the others are untouched."""
import json
from pathlib import Path

import pytest

from llmxive.speckit import task_revision

TASKS = (
    "# Tasks\n\n- [X] T004 Write `code/lib.py`\n"
    "- [ ] T005 [US1] Run the small example and visually verify the plot\n"
    "  *Path*: `data/plots/tv.png`\n  *Verification*: the plot shows two series\n"
    "- [ ] T006 Write `paper.md`\n"
)
GOOD = "Run `code/run.py --n 1000` so it writes `data/plots/tv.png` and `data/plots/tv_series.json` with keys `labels`, `x`, `y`; the check is that `labels` holds two entries."


def test_apply_replaces_the_task_and_its_continuation_only() -> None:
    out = task_revision.apply(TASKS, "T005", [GOOD, GOOD.replace("tv", "tv2")])
    lines = out.splitlines()
    assert lines[2] == "- [X] T004 Write `code/lib.py`"
    assert lines[3] == f"- [ ] T005 {GOOD}"
    assert lines[4] == "- [ ] T005r2 " + GOOD.replace("tv", "tv2")
    assert lines[5] == "- [ ] T006 Write `paper.md`"
    assert "visually verify" not in out and "*Verification*" not in out and out.endswith("\n")
    with pytest.raises(ValueError, match="expected one task"):
        task_revision.apply(TASKS, "T099", [GOOD])


def test_only_a_reply_of_the_required_shape_is_used() -> None:
    assert task_revision.parse(f"TASK: {GOOD}\n") == [GOOD]
    assert task_revision.parse(f"Here you go:\n\nTASK: {GOOD}\nTASK: {GOOD}\n") == [GOOD, GOOD]
    assert task_revision.parse("I would split this task.") is None
    assert task_revision.parse("TASK: Make the plot better.\n") is None  # names no file
    assert task_revision.parse("\n".join(f"TASK: {GOOD}" for _ in range(4))) is None


def test_the_history_is_the_distinct_reasons_for_that_task(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    rows = [("T005", "judged", "no evidence the plot shows two series"), ("T006", "judged", "other task"),
            ("T005", "accepted", ""), ("T005", "judged", "no evidence the plot shows two series"),
            ("T005", "failed_run", "code/run.py exit=1")]
    ledger.write_text("".join(json.dumps({"task": t, "kind": k, "reason": r}) + "\n" for t, k, r in rows) + "{torn",
                      encoding="utf-8")
    assert task_revision.rejection_history(ledger, "T005") == [
        "no evidence the plot shows two series", "code/run.py exit=1"]
    assert task_revision.rejection_history(tmp_path / "absent.jsonl", "T005") == []


def test_the_prompt_carries_the_task_the_reasons_and_the_files() -> None:
    repo = Path(__file__).resolve().parents[2]
    system, user = task_revision.build_messages(repo, "T005 Run it", ["reason one"], "FR-001 spec", ["code/run.py"])
    assert system.content.startswith("# llmXive task reviser")
    for part in ("T005 Run it", "- reason one", "FR-001 spec", "- `code/run.py`"):
        assert part in user.content
