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
        "operation_hint": "",
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
    # No placeholder of ANY name may survive unrendered (e.g. a newly-added
    # {{operation_hint}} the caller forgot to supply).
    assert "{{" not in rendered
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
    for sub in ("code", "specs", "docs", "data", "tests"):
        (proj / sub).mkdir(parents=True)
    for ok in (
        "code/analysis/regression.py",
        "specs/001-x/tasks.md",
        "docs/reproducibility/licenses.md",
        "data/processed/notes.md",
        "tests/integration/test_edge_cases.py",  # reviewers ask to add tests
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


def test_resolve_edit_target_fixes_wrong_filename(tmp_path: Path) -> None:
    """16.4% of failures: the LLM targets a venue-template name / wrong path.
    A MODIFY edit's nonexistent .tex resolves to the real primary manuscript;
    a wrong-dir code path resolves to the unique same-basename file."""
    from llmxive.agents.implementer import _resolve_edit_target

    proj = tmp_path / "projects" / "PROJ-1"
    src = proj / "paper" / "source"
    src.mkdir(parents=True)
    (src / "main-llmxive.tex").write_text(
        "\\documentclass{article}\\begin{document}\\end{document}", encoding="utf-8"
    )
    wrong_tex = src / "neurips_2026.tex"  # doesn't exist
    assert _resolve_edit_target(
        wrong_tex, project_id="PROJ-1", repo_root=tmp_path, track="paper"
    ).name == "main-llmxive.tex"

    (proj / "code" / "analysis").mkdir(parents=True)
    real = proj / "code" / "analysis" / "regression.py"
    real.write_text("x = 1\n", encoding="utf-8")
    assert _resolve_edit_target(
        proj / "code" / "regression.py", project_id="PROJ-1", repo_root=tmp_path,
        track="research",
    ) == real

    # An existing file is returned unchanged; an unresolvable name stays put.
    assert _resolve_edit_target(real, project_id="PROJ-1", repo_root=tmp_path, track="research") == real
    ghost = proj / "code" / "does_not_exist_anywhere.py"
    assert _resolve_edit_target(ghost, project_id="PROJ-1", repo_root=tmp_path, track="research") == ghost


def test_apply_unified_diff_flexible_fallback_on_bad_context(tmp_path: Path) -> None:
    """LLM diffs often carry wrong @@ line numbers / context that `git apply`
    rejects. The flexible fallback re-applies each hunk as a tolerant
    search/replace; a genuinely non-matching hunk still fails."""
    import subprocess

    from llmxive.agents.implementer import apply_unified_diff, _diff_hunks_to_replacements

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=False)
    f = tmp_path / "code" / "f.txt"
    f.parent.mkdir(parents=True)
    f.write_text("a\nb\nc\nd\ne\n", encoding="utf-8")
    bad = "--- a/code/f.txt\n+++ b/code/f.txt\n@@ -10,3 +10,3 @@\n b\n-c\n+C\n d\n"
    assert _diff_hunks_to_replacements(bad) == [("b\nc\nd", "b\nC\nd")]
    res = apply_unified_diff(f, bad)
    assert res.applied and f.read_text() == "a\nb\nC\nd\ne\n"

    g = tmp_path / "code" / "g.txt"
    g.write_text("nothing relevant here\n", encoding="utf-8")
    res2 = apply_unified_diff(
        g, "--- a/code/g.txt\n+++ b/code/g.txt\n@@ -1,2 +1,2 @@\n totally\n-absent\n+X\n"
    )
    assert not res2.applied


def test_research_target_window_gives_exact_content_for_named_files(tmp_path: Path) -> None:
    """The #1 root cause of no-match/corrupt-patch is the LLM never seeing the
    file's exact text. The implementer prompt must surface FULL current content
    for any file the action item names — dir-prefixed OR bare (resolved by unique
    basename) — so search strings/diffs match verbatim."""
    from llmxive.agents.implementer import _research_target_window

    proj = tmp_path
    (proj / "code" / "data").mkdir(parents=True)
    (proj / "code" / "data" / "validator.py").write_text("def validate(df):\n    return df\n", encoding="utf-8")
    (proj / "data").mkdir(exist_ok=True)
    (proj / "data" / "checksums.json").write_text('{"a.csv": "abc123"}\n', encoding="utf-8")

    # bare filename anywhere under the project -> resolved + FULL content
    w1 = _research_target_window(proj, "Consolidate the checksums.json manifest")
    assert "checksums.json" in w1 and "abc123" in w1 and "FULL current content" in w1
    # dir-prefixed path -> FULL content
    w2 = _research_target_window(proj, "code/data/validator.py needs two flag columns")
    assert "def validate" in w2
    # no named file -> directive, never a crash
    assert "does not name a specific" in _research_target_window(proj, "improve code quality")


def test_apply_move_and_delete_file(tmp_path: Path) -> None:
    """Structural edits let the implementer satisfy 'relocate logs->docs' /
    'prune redundant manifests' concerns that content edits cannot."""
    from llmxive.agents.implementer import apply_delete_file, apply_move_file

    # delete
    f = tmp_path / "redundant.md"
    f.write_text("dup", encoding="utf-8")
    res = apply_delete_file(f)
    assert res.applied and not f.exists()
    # A deleted file must carry NO after-hash. Recording an empty string there
    # violated ImplementerLogEntry.after_hashes's Sha256Field pattern and crashed
    # the whole revision run with a ValidationError — turning a reviewer-requested
    # deletion ("remove the redundant checksums.csv") into a zero-success round
    # (the PROJ-552 research-review stall). The deletion is captured by
    # files_modified + before_hashes; absence from after_hashes signals removal.
    assert res.after_hashes == {}
    assert "" not in res.after_hashes.values()
    from llmxive.types import ImplementerLogEntry
    # Must construct without a Sha256Field ValidationError.
    entry = ImplementerLogEntry(
        task_id="T001", status="done", action_item_text="remove redundant.md",
        files_modified=res.files_modified, before_hashes=res.before_hashes,
        after_hashes=res.after_hashes, duration_s=0.1,
    )
    assert entry.after_hashes == {} and entry.files_modified == res.files_modified
    assert not apply_delete_file(tmp_path / "ghost.md").applied  # absent -> refused

    # move (creates dest parents); refuses if dest exists
    src = tmp_path / "logs" / "run.log"
    src.parent.mkdir()
    src.write_text("log", encoding="utf-8")
    dst = tmp_path / "docs" / "reproducibility" / "run.log"
    assert apply_move_file(src, dst).applied and dst.is_file() and not src.exists()
    a = tmp_path / "a.txt"; a.write_text("x", encoding="utf-8")
    b = tmp_path / "b.txt"; b.write_text("y", encoding="utf-8")
    assert not apply_move_file(a, b).applied  # dest exists -> refused
    assert a.is_file()  # source untouched on refusal


def test_verify_changed_python_rolls_back_broken_edits(tmp_path: Path) -> None:
    """A research code edit must never leave un-importable Python."""
    from llmxive.agents.implementer import _verify_changed_python

    good = tmp_path / "g.py"; good.write_text("x = 1\n", encoding="utf-8")
    bad = tmp_path / "b.py"; bad.write_text("def f(:\n    pass\n", encoding="utf-8")
    doc = tmp_path / "d.md"; doc.write_text("not python", encoding="utf-8")
    assert _verify_changed_python([str(good), str(doc)]) is None
    assert _verify_changed_python([str(bad)]) is not None  # syntax error reported


def test_parse_llm_edit_accepts_structural_kinds() -> None:
    from llmxive.agents.implementer import _parse_llm_edit

    assert _parse_llm_edit('{"kind":"move_file","file":"logs/a.log","to":"docs/a.log"}')["kind"] == "move_file"
    assert _parse_llm_edit('{"kind":"delete_file","file":"checksums.csv"}')["kind"] == "delete_file"
    assert _parse_llm_edit('{"kind":"nonsense","file":"x"}') is None


def test_system_prompt_documents_all_four_edit_kinds() -> None:
    from llmxive.agents.prompts import render_prompt

    sys = render_prompt("agents/prompts/implementer.md", {}, repo_root=REAL_REPO)
    for kind in ("search_and_replace", "unified_diff", "move_file", "delete_file"):
        assert kind in sys, kind


def test_classify_edit_operation_steers_kind_from_intent() -> None:
    """The concern's verbs pick the edit KIND so the implementer stops answering
    consolidate/relocate concerns with an additive new file. Conservative: only
    clear prune/relocate/missing intents steer; 'fix X' / 'complete existing X'
    stay None (modify/default)."""
    from llmxive.agents.implementer import _classify_edit_operation as clf

    assert clf("Retain one authoritative checksums.json, remove checksums.csv and .sha256.") == "prune"
    assert clf("Consolidate the three checksum manifests into one.") == "prune"
    assert clf("Move plan.md and tasks.md into specs/001-knot/.") == "relocate"
    assert clf("logs/ is misplaced; it belongs under docs/reproducibility/.") == "relocate"
    assert clf("Add a LICENSE.md citing each external data source.") == "create"
    # Modify/default — must NOT be steered toward create/prune/relocate:
    assert clf("Fix the off-by-one in code/data/loader.py.") is None
    assert clf("Complete hyperbolic_volume_validation.md with the measured coverage %.") is None


def test_force_blocker_rereview_clears_only_non_accept(tmp_path: Path) -> None:
    """After a successful revision round, only the NON-ACCEPT specialists' review
    records are cleared so coverage re-dispatches exactly those blockers — the
    missing link in research convergence (staleness is keyed on tasks.md, which a
    research revision never touches, so a blocker would otherwise never be
    re-judged and the panel loops to the round cap). Accepts are preserved."""
    import yaml
    from llmxive.agents.implementer import _force_blocker_rereview

    proj = "PROJ-901-converge"
    d = tmp_path / "projects" / proj / "reviews" / "research"
    d.mkdir(parents=True)

    def _write(name: str, verdict: str) -> None:
        rec = {
            "reviewer_name": name, "reviewer_kind": "llm",
            "artifact_path": f"projects/{proj}/specs/x/tasks.md",
            "artifact_hash": "a" * 64,
            "score": 0.5 if verdict == "accept" else 0.0, "verdict": verdict,
            "reviewed_at": "2026-06-18T00:00:00Z", "prompt_version": "1.0.0",
            "model_name": "m", "backend": "dartmouth",
        }
        (d / f"{name}__2026-06-18__research.md").write_text(
            "---\n" + yaml.safe_dump(rec) + "---\n\nbody\n", encoding="utf-8"
        )

    accepts = [
        "research_reviewer_idea_quality", "research_reviewer_creativity",
        "research_reviewer_code_quality_research",
        "research_reviewer_implementation_correctness",
        "research_reviewer_implementation_completeness",
        "research_reviewer_filesystem_hygiene",
    ]
    for n in accepts:
        _write(n, "accept")
    _write("research_reviewer_data_quality_research", "minor_revision")

    cleared = _force_blocker_rereview(proj, track="research", repo=tmp_path)
    remaining = sorted(p.name for p in d.glob("*.md"))
    assert cleared == 1
    assert not any("data_quality" in n for n in remaining)
    assert len(remaining) == 6  # the 6 accepts are untouched
    # Idempotent once everything accepts: nothing left to clear.
    assert _force_blocker_rereview(proj, track="research", repo=tmp_path) == 0


def test_compute_and_fill_context_and_trace_guard(tmp_path: Path) -> None:
    """Compute-and-fill: (1) detect 'fill the computed value' tasks; (2) summarize
    the project's REAL execution artifacts into computed values + a traceability
    whitelist; (3) guard rejects any result-like number the edit introduces that
    traces to no artifact (no hallucinated empirical values)."""
    import json
    from llmxive.agents.implementer import (
        _is_compute_required, _computation_context, _untraceable_result_numbers,
    )
    from llmxive.state import execution_status

    # detection — including phrasings a live run exposed ("insert/report/state
    # the exact/total count") that an earlier narrower cue missed.
    assert _is_compute_required("Fill in the actual per-crossing counts")
    assert _is_compute_required("Populate multicollinearity.md with real VIF values")
    assert _is_compute_required("Replace TBD placeholders with computed coverage %")
    assert _is_compute_required("Insert the exact excluded-knot count (e.g., 342)")
    assert _is_compute_required("report the number of excluded knots")
    assert _is_compute_required("state the total excluded knots")
    assert not _is_compute_required("Fix the typo in the abstract")
    assert not _is_compute_required("Rename the helper for clarity")

    proj = "PROJ-903-compute"
    pdir = tmp_path / "projects" / proj
    (pdir / "data" / "processed").mkdir(parents=True)
    # a real CSV artifact: 3 data rows, a partially-populated column
    (pdir / "data" / "processed" / "knots.csv").write_text(
        "name,volume,braid_index\nk1,2.5,3\nk2,3.1,\nk3,4.0,5\n", encoding="utf-8"
    )
    (pdir / "data" / "outliers.json").write_text(json.dumps([1, 2, 3, 4, 5]), encoding="utf-8")
    execution_status.record(
        proj, ok=True, reason="ok",
        artifacts=["data/processed/knots.csv", "data/outliers.json"],
        failures=[], repo_root=tmp_path,
    )

    ctx, traceable = _computation_context(pdir, project_id=proj, repo=tmp_path)
    assert "3 data rows" in ctx                       # real row count
    assert "2/3 non-empty" in ctx                     # braid_index real coverage
    assert "JSON array of 5 items" in ctx             # real array length
    assert "3" in traceable and "5" in traceable and "2" in traceable

    # guard: a real count passes; a fabricated statistic is flagged
    before = "Coverage is TBD; VIF is TBD."
    ok = "The dataset has 5 outliers across 3 rows."   # both trace to artifacts
    assert _untraceable_result_numbers(before, ok, traceable=traceable, allow=set()) == set()
    bad = "The VIF is 4.73 and coverage is 87.6%."     # invented
    assert _untraceable_result_numbers(before, bad, traceable=traceable, allow=set()) == {"4.73", "87.6"}
    # numbers already in the file are allowed (not "introduced"); a reviewer's
    # illustrative example number (NOT in artifacts, NOT in the file) must still
    # be flagged — the guard is fed allow=_result_numbers(before) only, never the
    # action item, so a fabricated "e.g., 342" can never be laundered into a doc.
    assert _untraceable_result_numbers(
        "old value 999.9", "old value 999.9 plus 4.73", traceable=set(), allow={"999.9"}
    ) == {"4.73"}
    assert _untraceable_result_numbers(
        "count: TBD", "count: 342", traceable={"12967"}, allow={""}
    ) == {"342"}  # reviewer example, untraceable -> flagged


def test_rerun_analysis_after_code_revision_records_and_never_crashes(tmp_path: Path) -> None:
    """A research revision that edits analysis CODE must RE-RUN the run-book so
    the change executes (the revision loop's 'write AND run' step). The helper
    runs the analysis, records execution_status (so reviewers + the next round
    see the result), and never crashes the tick — even with no run-book."""
    from llmxive.agents.implementer import _rerun_analysis_after_code_revision
    from llmxive.state import execution_status

    proj = "PROJ-905-rerun"
    (tmp_path / "projects" / proj / "code").mkdir(parents=True)  # no quickstart.md
    ok = _rerun_analysis_after_code_revision(proj, repo=tmp_path)
    rec = execution_status.load(proj, repo_root=tmp_path)
    assert ok is False                       # nothing to run -> not ok
    assert rec is not None and rec["ok"] is False
    assert "quickstart" in rec["reason"]     # the run error is RECORDED for review
