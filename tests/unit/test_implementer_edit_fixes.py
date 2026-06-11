"""Regressions for three defects the FIRST real revision-implementer round
surfaced (spec 023 / T009 on PROJ-565: 39 of 39 tasks skipped).

1. ``agents/prompts/implementer_edit.md`` used single-brace ``{token}``
   placeholders while ``substitute()`` implements ``{{token}}`` — every
   per-task edit prompt since spec 013 reached the LLM UNRENDERED (18 of
   39 real tasks: the model literally replied
   "the prompt contains unfilled template placeholders").
2. ``_validate_edit_path`` rejected PROJECT-relative paths
   ("paper/source/main.tex" — exactly how the prompt names the
   manuscript); 21 of 39 real edits were discarded solely for this.
3. ``_read_tasks_md`` captured the revision adapter's ``[REV]`` category
   tag as the task severity, breaking the severity-dependent path rules
   for every adapter-written round.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents.implementer import _read_tasks_md, _validate_edit_path
from llmxive.agents.prompts import render_prompt

REAL_REPO = Path(__file__).resolve().parents[2]


def test_edit_prompt_renders_with_no_unfilled_placeholders() -> None:
    values = {
        "project_id": "PROJ-565-x",
        "round_number": "1",
        "revision_spec_path": "specs/auto-revisions/PROJ-565-x/round-1",
        "task_id": "001",
        "severity": "writing",
        "action_item_text": "Fix the typo in section 2.",
        "manuscript_window": "1: \\section{Intro}",
        "science_note": "",
        "primary_tex": "main-llmxive.tex",
    }
    rendered = render_prompt(
        "agents/prompts/implementer_edit.md", values, repo_root=REAL_REPO
    )
    for key, val in values.items():
        assert "{" + key + "}" not in rendered, (
            f"single-brace placeholder {{{key}}} reached the prompt unrendered"
        )
        assert "{{" + key + "}}" not in rendered
        if val:
            assert val in rendered, f"value for {key} missing from the prompt"
    # Defect #10: the manuscript file must be the project's REAL primary
    # tex, never a hard-coded main.tex.
    assert "paper/source/main-llmxive.tex" in rendered
    assert "`paper/source/main.tex`" not in rendered


def test_validate_edit_path_accepts_project_relative(tmp_path: Path) -> None:
    src = tmp_path / "projects" / "PROJ-1-x" / "paper" / "source"
    src.mkdir(parents=True)
    (src / "main.tex").write_text("x", encoding="utf-8")

    for form in (
        "paper/source/main.tex",                  # project-relative (the LLM's natural form)
        "projects/PROJ-1-x/paper/source/main.tex",  # repo-relative
        "./paper/source/main.tex",
    ):
        resolved = _validate_edit_path(
            form, project_id="PROJ-1-x", severity="writing", repo_root=tmp_path
        )
        assert resolved == (src / "main.tex").resolve(), form


def test_validate_edit_path_still_rejects_escapes(tmp_path: Path) -> None:
    (tmp_path / "projects" / "PROJ-1-x" / "paper" / "source").mkdir(parents=True)
    for bad in ("", "../../etc/passwd", "projects/PROJ-2-y/paper/source/main.tex",
                "code/run.py"):  # code/ requires science severity
        assert _validate_edit_path(
            bad, project_id="PROJ-1-x", severity="writing", repo_root=tmp_path
        ) is None, bad
    # science severity unlocks code/ and data/ (project-relative too).
    (tmp_path / "projects" / "PROJ-1-x" / "code").mkdir()
    assert _validate_edit_path(
        "code/run.py", project_id="PROJ-1-x", severity="science",
        repo_root=tmp_path,
    ) is not None


def test_read_tasks_md_parses_adapter_rev_tag(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.md"
    tasks.write_text(
        "- [ ] T001 [REV] Address action item **[77be4dbe5505]** "
        "(severity: writing): Correct arithmetic in Table 3.\n"
        "- [ ] T002 [REV] Address action item **[9497d8b83225]** "
        "(severity: science): Re-run the baseline.\n"
        "- [ ] T003 [science] Direct severity tag still honored\n",
        encoding="utf-8",
    )
    parsed = _read_tasks_md(tasks)
    assert [t["severity"] for t in parsed] == ["writing", "science", "science"]
    assert parsed[0]["id"] == "001"
