"""Independent task-completion verifier (spec-contract consistency).

The verifier is a SEPARATE LLM call (outside the implementer's session) that judges
whether a claimed-done task's actual artifacts satisfy its requirements. These
tests pin the pure parsing / evidence-gathering / fail-closed behavior; the live
model call is exercised by the real-call suite.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents import task_verifier as tv


def test_parse_complete_and_incomplete() -> None:
    assert tv._parse("VERDICT: COMPLETE\nthe csv has the required columns").complete is True
    assert tv._parse("VERDICT: INCOMPLETE\nthe file is a stub").complete is False


def test_parse_uninterpretable_defers_not_accepts() -> None:
    """An unparseable / empty response must DEFER (None), never silently accept."""
    assert tv._parse("").complete is None
    assert tv._parse("I think it's probably fine").complete is None


def test_gather_evidence_reads_referenced_artifacts(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "results.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    ev = tv.gather_evidence(tmp_path, "T012 Produce data/results.csv with columns a,b")
    assert "data/results.csv" in ev and "a,b" in ev


def test_gather_evidence_flags_missing_artifact(tmp_path: Path) -> None:
    ev = tv.gather_evidence(tmp_path, "T013 Write data/missing.json")
    assert "data/missing.json" in ev and "MISSING" in ev


def test_verification_reads_repo_rooted_and_code_relative_files(tmp_path, monkeypatch):
    """Reproduce the live canary's false missing-file rejection through the pass."""
    project = tmp_path / "projects" / "PROJ-9999-totient-canary"
    code = project / "code"
    (code / "src/utils").mkdir(parents=True)
    (code / "src/utils/sieve.py").write_text("def phi(n):\n    return 0  # incorrect\n")
    (code / "requirements.txt").write_text("pytest\n")
    tasks = project / "tasks.md"
    tasks.write_text(
        "- [X] T001 Set up src/utils/sieve.py and requirements.txt\n"
        "- [X] T002 Implement projects/PROJ-9999-totient-canary/code/src/utils/sieve.py\n"
    )
    judged = []

    def judge(**kwargs):
        judged.append(kwargs)
        assert "def phi(n):" in kwargs["evidence"]
        assert "MISSING" not in kwargs["evidence"]
        # Finding the artifact must not bypass semantic review of bad science.
        return tv.TaskVerdict(False, "phi returns zero instead of the totient")

    monkeypatch.setattr(tv, "verify_task", judge)
    result = tv.run_verification_pass(
        project, tasks, already_verified=set(), notes_path=project / "notes.md",
        state_path=project / "verify.yaml",
    )
    assert len(judged) == 2
    assert "pytest" in judged[0]["evidence"]
    assert len(result["rejected"]) == 2
    assert "[X]" not in tasks.read_text()


def test_repo_rooted_spec_not_duplicated_or_replaced_by_bare_name(tmp_path):
    project = tmp_path / "PROJ-1"
    spec = project / "specs/001-study/spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("The actual study contract")
    task = "Read projects/PROJ-1/specs/001-study/spec.md and code/main.py"
    assert tv._declared_paths(task) == [
        "projects/PROJ-1/specs/001-study/spec.md", "code/main.py",
    ]
    assert "The actual study contract" in tv.gather_evidence(project, task)


def test_evidence_respects_explicit_paths_and_project_boundary(tmp_path):
    project = tmp_path / "PROJ-1"
    (project / "code/src").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "code/src/main.py").write_text("nested source")
    (project / "src/main.py").write_text("root source")
    (tmp_path / "secret.py").write_text("outside secret")
    (project / "code/leak.py").symlink_to(tmp_path / "secret.py")
    assert "root source" in tv.gather_evidence(project, "Implement src/main.py")
    assert "nested source" not in tv.gather_evidence(project, "Implement src/main.py")
    for rel in (
        "projects/PROJ-2/code/src/main.py", "../secret.py", str(tmp_path / "secret.py"),
        "code/leak.py",
    ):
        assert tv._evidence_path(project, rel) is None
        assert not tv._artifact_valid(project, rel)
    (project / "src/main.py").unlink()
    assert "nested source" in tv.gather_evidence(project, "Implement src/main.py")
    assert "MISSING" in tv.gather_evidence(project, "Implement projects/PROJ-1/src/main.py")


def test_nested_evidence_changes_invalidate_verdict_hash(tmp_path):
    path = tmp_path / "code/src/main.py"
    path.parent.mkdir(parents=True)
    path.write_text("wrong implementation")
    task = "Implement src/main.py"
    before = tv.gather_evidence(tmp_path, task)
    path.write_text("corrected implementation")
    after = tv.gather_evidence(tmp_path, task)
    assert before != after and "sha256=" in after


def test_setup_directory_evidence_includes_actual_layout(tmp_path):
    project = tmp_path / "PROJ-1"
    (project / "code/src/utils").mkdir(parents=True)
    task = "Create projects/PROJ-1/, src/, src/utils/, and tests/unit/."
    evidence = tv.gather_evidence(project, task)
    assert tv._declared_paths(task) == [
        "projects/PROJ-1/", "src/", "src/utils/", "tests/unit/",
    ]
    assert "`projects/PROJ-1/`: directory exists" in evidence
    assert "`src/`: directory exists" in evidence
    assert "`src/utils/`: directory exists" in evidence
    assert "`tests/unit/`: MISSING" in evidence
    assert "utils/" in evidence
    before = evidence
    (project / "code/src/new.py").write_text("new code")
    assert tv.gather_evidence(project, task) != before
    # Directory scaffolding must not crowd the dependency file out of review.
    for directory in ("data", "results", "contracts", "tests"):
        (project / directory).mkdir()
    (project / "requirements.txt").write_text("pytest>=8.0\n")
    setup = (
        "Create src/, src/utils/, data/, results/, contracts/, tests/, code/, "
        "and requirements.txt"
    )
    assert "pytest>=8.0" in tv.gather_evidence(project, setup)


def test_evidence_follows_implementer_feature_slug_canonicalization(tmp_path, monkeypatch):
    from llmxive.state import project as store

    feature = tmp_path / "specs/001-canonical"
    (feature / "contracts").mkdir(parents=True)
    (feature / "contracts/summary.schema.yaml").write_text("type: object\n")
    monkeypatch.setattr(store, "feature_dir_for", lambda *a, **kw: feature)
    task = "Write specs/001-invented/contracts/summary.schema.yaml"
    evidence = tv.gather_evidence(tmp_path, task)
    assert "type: object" in evidence
    assert "resolved: `specs/001-canonical/contracts/summary.schema.yaml`" in evidence
    # Live setup tasks can leave an empty contracts/ directory under the
    # invented slug; that scaffold must not hide the canonical artifact.
    (tmp_path / "specs/001-invented/contracts").mkdir(parents=True)
    assert "type: object" in tv.gather_evidence(tmp_path, task)
    # Never borrow evidence from another feature that actually exists.
    (tmp_path / "specs/001-invented/spec.md").write_text("A distinct real feature")
    assert "MISSING" in tv.gather_evidence(tmp_path, task)


def test_implementer_gets_same_existing_source_as_verifier(tmp_path):
    from llmxive.speckit.implement_cmd import _inline_referenced_files

    source = tmp_path / "code/src/sieve.py"
    source.parent.mkdir(parents=True)
    source.write_text("def phi(n):\n    return n  # must be repaired\n")
    task = "Fix src/sieve.py"
    assert source.read_text() in _inline_referenced_files(tmp_path, task)
    assert source.read_text() in tv.gather_evidence(tmp_path, task)
    outside = tmp_path.parent / "outside.py"
    outside.write_text("private contents")
    (tmp_path / "code/leak.py").symlink_to(outside)
    assert _inline_referenced_files(tmp_path, "Fix code/leak.py") == ""


def test_implementer_preserves_full_context_for_typical_analysis_module(tmp_path):
    from llmxive.speckit.implement_cmd import _inline_referenced_files

    source = tmp_path / "code/analysis.py"
    source.parent.mkdir()
    # The live canary's incrementally implemented driver exceeded the old 6k
    # ceiling, hiding all its prior behavior from later implementation tasks.
    contents = "# analysis context\n" * 700 + "def final_step():\n    return 1\n"
    source.write_text(contents)
    context = _inline_referenced_files(tmp_path, "Extend code/analysis.py")
    assert contents in context
    constrained = _inline_referenced_files(tmp_path, "Extend code/analysis.py", max_chars=100)
    assert "Do not replace this file blindly" in constrained
    assert "extend it on disk" not in constrained


def test_verify_task_defers_on_backend_failure(monkeypatch) -> None:
    """A transient backend outage DEFERS (complete=None) — an unverifiable task is
    never accepted as done (fail-closed, unlike the relevance judge's fail-open)."""
    def _boom(*a, **k):
        raise RuntimeError("backend down")

    monkeypatch.setattr(tv, "chat_with_fallback", _boom)
    v = tv.verify_task(task_text="T1 do thing", evidence="- `data/x.csv`: MISSING")
    assert v.complete is None and v.deferred


def test_verify_task_accepts_on_complete(monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(
        tv, "chat_with_fallback",
        lambda *a, **k: SimpleNamespace(text="VERDICT: COMPLETE\nartifact present and correct", model="m"),
    )
    v = tv.verify_task(task_text="T1 produce data/x.csv", evidence="- `data/x.csv` (10 bytes)")
    assert v.complete is True


def test_verify_task_rejects_on_incomplete(monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(
        tv, "chat_with_fallback",
        lambda *a, **k: SimpleNamespace(text="VERDICT: INCOMPLETE\nthe csv is empty", model="m"),
    )
    v = tv.verify_task(task_text="T1 produce data/x.csv", evidence="- `data/x.csv`: MISSING")
    assert v.complete is False and "empty" in v.reason


# --- Task identity must survive claim-marker churn (the in_progress doom loop) ---
#
# The claims layer RE-ANNOTATES artifacts (tasks.md included) on every tick, stamping
# ``[UNRESOLVED-CLAIM: <fresh-id> — …]`` markers whose ids are regenerated each pass.
# When a task's identity was its full line TEXT, that rewrite minted a NEW key every
# tick, so (a) the ``already_verified`` snapshot no longer matched a settled ``[X]``
# task — it was re-judged as "newly claimed" and could be un-checked back to ``[ ]``,
# and (b) ``reject_counts`` never accumulated, so REJECT_CAP never fired. Result: an
# unbreakable redo loop — every one of the 433 in_progress projects drifted BACKWARD
# (PROJ-492: done 64 -> 55 over 24h) and none ever reached research_complete.
# Identity is therefore the STABLE task id (T009 / PT005C), never the mutable line.

_CHURN_A = "T009 Set up logging in `src/utils/logger.py` (verify codes)."
_CHURN_B = (
    "T009 Set up logging in `src/utils/logger.py` "
    "(verify codes [UNRESOLVED-CLAIM: c_c3bf9b30 — status=not_enough_info])."
)


def test_task_key_is_stable_under_claim_marker_churn() -> None:
    """The same task, re-annotated with a fresh claim id, keeps ONE identity."""
    assert tv._task_key(_CHURN_A) == tv._task_key(_CHURN_B)


def test_task_key_distinguishes_distinct_ids() -> None:
    """Aliased-but-distinct tasks (T005C vs PT005C) must NOT collapse together."""
    assert tv._task_key("T005C **[P]** Implement checker") != tv._task_key(
        "PT005C **[P]** Implement checker"
    )


def test_duplicate_task_ids_get_distinct_keys() -> None:
    """18% of live projects (78/433, 240 lines) carry DUPLICATE task ids — two
    different tasks both numbered T001, from merged task lists. Keying on the bare
    id would collapse them: the second would inherit the first's ``[X]`` snapshot
    entry and silently ESCAPE independent verification, and their reject counts
    would share a counter (firing REJECT_CAP early). Disambiguate by occurrence."""
    text = (
        "- [X] T001 Set up GitHub Actions workflow\n"
        "- [X] T001 Create repository skeleton with src/\n"
        "- [ ] T002 Something else\n"
    )
    keys = tv.task_keys(text)
    assert len(set(keys.values())) == 3, keys
    # ...and the numbering is positional, so it survives claim-marker churn.
    churned = text.replace(
        "Set up GitHub Actions workflow",
        "Set up GitHub Actions workflow [UNRESOLVED-CLAIM: c_9f21 — status=x]",
    )
    assert list(tv.task_keys(churned).values()) == list(keys.values())


def test_second_duplicate_id_is_still_verified(tmp_path: Path, monkeypatch) -> None:
    """A newly-claimed task must be judged even when an EARLIER task shares its id."""
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# T\n\n- [X] T001 first task\n", encoding="utf-8")
    snapshot = tv.claimed_done_keys(tasks.read_text(encoding="utf-8"))
    # The implementer now claims a SECOND, different task that reuses id T001.
    tasks.write_text(
        "# T\n\n- [X] T001 first task\n- [X] T001 a different second task\n",
        encoding="utf-8",
    )
    judged: list[str] = []

    def _spy(**kw):
        from types import SimpleNamespace

        judged.append(kw["task_text"])
        return SimpleNamespace(complete=True, reason="ok", deferred=False)

    monkeypatch.setattr(tv, "verify_task", _spy)
    tv.run_verification_pass(
        tmp_path, tasks, already_verified=snapshot,
        notes_path=tmp_path / "n.md", state_path=tmp_path / "s.yaml",
    )
    assert len(judged) == 1 and "different second task" in judged[0], judged


def test_settled_task_not_rejudged_after_reannotation(tmp_path: Path, monkeypatch) -> None:
    """A verifier-accepted ``[X]`` task that the claims layer then re-annotates must
    stay ``[X]``: it is settled work and must never be re-judged (nor un-checked)."""
    tasks = tmp_path / "tasks.md"
    tasks.write_text(f"# Tasks\n\n- [X] {_CHURN_A}\n", encoding="utf-8")
    snapshot = tv.claimed_done_keys(tasks.read_text(encoding="utf-8"))

    # Claims layer rewrites the line with a fresh marker (identity must not change).
    tasks.write_text(f"# Tasks\n\n- [X] {_CHURN_B}\n", encoding="utf-8")

    def _never(*a, **k):  # the verifier must not spend a call on settled work
        raise AssertionError("settled task was re-judged")

    monkeypatch.setattr(tv, "verify_task", _never)
    result = tv.run_verification_pass(
        tmp_path, tasks, already_verified=snapshot,
        notes_path=tmp_path / "notes.md", state_path=tmp_path / "state.yaml",
    )
    assert result["accepted"] == 0 and not result["rejected"] and not result["deferred"]
    assert "- [X] " in tasks.read_text(encoding="utf-8")


def test_reject_cap_records_unverifiable_never_accepts(tmp_path: Path, monkeypatch) -> None:
    """REJECT_CAP consecutive INCOMPLETE verdicts must NEVER force-accept the task
    (the fail-open removed in issue #1139). Instead, after the cap the task is
    reopened ``[ ]`` AND recorded in :mod:`llmxive.state.unverifiable` — which both
    breaks the redo loop (a recorded task is not re-judged) and signals CORE to
    route the project to research_full_revision. Reject counts still accumulate
    across the claims layer's per-tick re-annotation of the line."""
    from types import SimpleNamespace

    from llmxive.state import unverifiable

    monkeypatch.setattr(
        tv, "verify_task",
        lambda **k: SimpleNamespace(complete=False, reason="stub only", deferred=False),
    )
    tasks = tmp_path / "tasks.md"
    state = tmp_path / "state.yaml"
    marks = []
    result: dict = {}
    for tick in range(tv.REJECT_CAP):
        # Each tick the claims layer stamps a DIFFERENT fresh claim id. The task has
        # NO artifact path, so it routes to the (forced-INCOMPLETE) semantic verifier.
        line = (
            f"T009 wire up the pipeline module "
            f"(verify codes [UNRESOLVED-CLAIM: c_tick{tick} — status=not_enough_info])."
        )
        tasks.write_text(f"# Tasks\n\n- [X] {line}\n", encoding="utf-8")
        result = tv.run_verification_pass(
            tmp_path, tasks, already_verified=set(),  # re-claimed by the implementer
            notes_path=tmp_path / "notes.md", state_path=state,
            project_id="PROJ-CAP", repo_root=tmp_path,
        )
        marks.append(tasks.read_text(encoding="utf-8").split("\n")[2][:6])

    # NEVER accepted — reopened [ ] every tick, and [X] appears at NO point.
    assert marks == ["- [ ] "] * tv.REJECT_CAP, marks
    assert "- [X]" not in tasks.read_text(encoding="utf-8")
    # The final tick recorded the task as unverifiable and flagged it in the result.
    assert result["unverifiable"] == ["T009"], result
    recorded = unverifiable.load("PROJ-CAP", repo_root=tmp_path)
    assert [t["task_key"] for t in recorded] == ["T009"], recorded
    assert unverifiable.has_unverifiable("PROJ-CAP", repo_root=tmp_path)
