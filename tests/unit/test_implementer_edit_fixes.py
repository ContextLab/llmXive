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


def test_validate_edit_path_research_track_allows_all_research_bases(tmp_path: Path) -> None:
    """A RESEARCH revision has no manuscript — it edits the project's own
    artifacts. code/specs/docs/data are allowed for ANY severity (incl. the
    default 'writing'); paper/ is NOT (no paper exists). Pins PROJ-552's
    agent_blocked: writing-severity edits to code/ were rejected -> 0 success."""
    proj = tmp_path / "projects" / "PROJ-9-z"
    for sub in ("code", "specs", "docs", "data"):
        (proj / sub).mkdir(parents=True)
    for ok in (
        "code/analysis/regression.py",
        "specs/001-x/tasks.md",
        "docs/reproducibility/licenses.md",
        "data/processed/notes.md",
        "projects/PROJ-9-z/code/analysis/regression.py",  # repo-relative form
    ):
        assert _validate_edit_path(
            ok, project_id="PROJ-9-z", severity="writing", repo_root=tmp_path,
            track="research",
        ) is not None, ok
    for bad in ("", "../../etc/passwd", "paper/source/main.tex",
                "projects/PROJ-OTHER/code/x.py"):
        assert _validate_edit_path(
            bad, project_id="PROJ-9-z", severity="writing", repo_root=tmp_path,
            track="research",
        ) is None, bad


def test_validate_edit_path_research_allows_project_root_excludes_specify(tmp_path: Path) -> None:
    """Research revisions may create top-level project files (README/LICENSE) the
    reviewers ask for, but must NEVER touch .specify/ state internals."""
    proj = tmp_path / "projects" / "PROJ-9-z"
    (proj / ".specify" / "memory").mkdir(parents=True)
    (proj / "docs").mkdir()
    assert _validate_edit_path("README.md", project_id="PROJ-9-z", severity="writing",
                               repo_root=tmp_path, track="research") is not None
    assert _validate_edit_path("LICENSE.md", project_id="PROJ-9-z", severity="writing",
                               repo_root=tmp_path, track="research") is not None
    assert _validate_edit_path(".specify/memory/x.yaml", project_id="PROJ-9-z",
                               severity="writing", repo_root=tmp_path, track="research") is None


def test_apply_unified_diff_creates_new_file(tmp_path: Path) -> None:
    """Research reviewers frequently ask for a doc that doesn't exist yet; the
    LLM emits a /dev/null diff. Pins PROJ-552's 12 file-not-found failures."""
    from llmxive.agents.implementer import apply_unified_diff

    target = tmp_path / "docs" / "reproducibility" / "licenses.md"
    diff = (
        "--- /dev/null\n+++ b/docs/reproducibility/licenses.md\n"
        "@@ -0,0 +1,2 @@\n+# Data licenses\n+Knot Atlas: CC-BY.\n"
    )
    res = apply_unified_diff(target, diff)
    assert res.applied and target.is_file()
    assert "Data licenses" in target.read_text() and "CC-BY" in target.read_text()

    # gpt-oss emits the a/ b/-prefixed form (`--- a/dev/null`); the a/ strip
    # leaves "dev/null", which must also be treated as new-file (not rejected).
    target2 = tmp_path / "docs" / "reproducibility" / "layout.md"
    diff2 = (
        "--- a/dev/null\n+++ b/docs/reproducibility/layout.md\n"
        "@@ -0,0 +1,1 @@\n+Layout confirmed.\n"
    )
    res2 = apply_unified_diff(target2, diff2)
    assert res2.applied and target2.is_file() and "Layout confirmed" in target2.read_text()


def test_apply_unified_diff_existing_relative_path_and_scope(tmp_path: Path) -> None:
    """Existing-file diffs name the target with a PROJECT-relative path; the
    apply cwd must resolve it. An unrelated declared file is rejected."""
    import subprocess

    from llmxive.agents.implementer import apply_unified_diff

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=False)
    ex = tmp_path / "code" / "a.py"
    ex.parent.mkdir(parents=True)
    ex.write_text("x = 1\n", encoding="utf-8")
    ok = apply_unified_diff(ex, "--- a/code/a.py\n+++ b/code/a.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n")
    assert ok.applied and ex.read_text().strip() == "x = 2"
    bad = apply_unified_diff(ex, "--- a/code/a.py\n+++ b/code/OTHER.py\n@@ -1 +1 @@\n-x\n+y\n")
    assert not bad.applied


def test_research_target_window_finds_named_file_else_directive(tmp_path: Path) -> None:
    from llmxive.agents.implementer import _research_target_window

    proj = tmp_path / "projects" / "PROJ-9-z"
    (proj / "code" / "data").mkdir(parents=True)
    (proj / "code" / "data" / "validator.py").write_text(
        "def validate():\n    return True\n", encoding="utf-8"
    )
    win = _research_target_window(proj, "code/data/validator.py should expose two columns")
    assert "validator.py" in win and "def validate" in win
    # No named file -> a directive, never a crash.
    assert "does not name a specific" in _research_target_window(proj, "improve code quality")


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


def test_feature_dir_for_honors_project_pointer(tmp_path: Path) -> None:
    """Spec 023 defect #17: after an idea-root kickback cycle a project
    accumulates feature dirs; the content heuristic (first dir with
    tasks.md) resolved the STALE cycle while agents worked the new one.
    The project state's speckit_*_dir pointer is the SSoT."""
    import yaml

    from llmxive.state.project import feature_dir_for

    pid = "PROJ-942-pointer"
    proj = tmp_path / "projects" / pid
    old = proj / "specs" / "004-old"
    new = proj / "specs" / "005-new"
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    (old / "tasks.md").write_text("- [X] T001 stale\n", encoding="utf-8")
    (new / "spec.md").write_text("# fresh spec\n", encoding="utf-8")
    state = tmp_path / "state" / "projects"
    state.mkdir(parents=True)
    (state / f"{pid}.yaml").write_text(
        yaml.safe_dump({"speckit_research_dir": f"projects/{pid}/specs/005-new"}),
        encoding="utf-8",
    )

    assert feature_dir_for(proj, track="research").name == "005-new"

    # Without a pointer, the content heuristic still applies (ghost-dir
    # protection for arXiv-intake projects).
    (state / f"{pid}.yaml").write_text(yaml.safe_dump({}), encoding="utf-8")
    assert feature_dir_for(proj, track="research").name == "004-old"


def test_flexible_replace_handles_whitespace_and_indent_drift() -> None:
    """~62% of real edit failures are 'search string not found' from whitespace/
    indent drift. The flexible matcher must locate a UNIQUE multi-line block under
    looser normalization, while still refusing ambiguous / absent searches."""
    from llmxive.agents.implementer import _flexible_replace

    # Multi-line block: LLM dedented the nested line (indentation drift) -> no
    # exact substring, but a unique line-based match under strip-normalization.
    text = "def f():\n    if x:\n        return 1\n"
    out, why = _flexible_replace(text, "if x:\n    return 1", "if x:\n    return 2")
    assert out is not None and "return 2" in out and "return 1" not in out

    # Internal-whitespace drift on a single line.
    out2, _ = _flexible_replace("a\ny   =    1\nb\n", "y = 1", "y = 99")
    assert out2 is not None and "y = 99" in out2

    # Ambiguous -> refuse (never silently edit the wrong place).
    out3, why3 = _flexible_replace("p=1\np=1\n", "p=1", "q")
    assert out3 is None and "ambiguous" in why3

    # Genuinely absent -> refuse.
    out4, why4 = _flexible_replace("nothing here\n", "absent multi\nline block", "z")
    assert out4 is None and "no-match" in why4

    # Exact still wins and is preserved verbatim.
    out5, why5 = _flexible_replace("alpha\nbeta\n", "beta", "BETA")
    assert out5 == "alpha\nBETA\n" and why5 == "exact"


def test_apply_search_and_replace_uses_flexible_matching(tmp_path: Path) -> None:
    from llmxive.agents.implementer import apply_search_and_replace

    f = tmp_path / "m.py"
    f.write_text("class C:\n        value =  1\n", encoding="utf-8")  # odd indent + double space
    res = apply_search_and_replace(f, "value = 1", "value = 2")
    assert res.applied and "value = 2" in f.read_text()
