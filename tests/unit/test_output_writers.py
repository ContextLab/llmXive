"""A run that replaces a file another script wrote says so in its log.

Canary 12 (2026-10-11): `code/write_methods_doc.py` (T008) wrote
`data/results.md` with the methods text and the citation. The clean rerun for
T009 executed `code/run_analysis.py`, which regenerates `data/results.md` as a
table only. T008 was then rejected three times for a document with "no
citation", and nothing either model was shown said why the text had gone.
"""
from pathlib import Path
from types import SimpleNamespace

import yaml

from llmxive.backends.base import ChatResponse
from llmxive.speckit import output_writers
from llmxive.speckit.implement_cmd import ImplementerAgent

METHODS = (
    "from llmxive_toolkit import paths\n"
    "paths.data('results.md').write_text('# Methods\\n\\nLebowitz-Lockard et al. (2021).\\n', encoding='utf-8')\n"
    "paths.data('methods_only.txt').write_text('kept\\n', encoding='utf-8')\n"
)
DRIVER = (
    "from llmxive_toolkit import paths\n"
    "paths.data('results.md').write_text('| N | p |\\n|-|-|\\n| 1000 | 5 |\\n', encoding='utf-8')\n"
    "paths.data('summary.json').write_text('{}\\n', encoding='utf-8')\n"
)


def _send(tmp_path: Path, task_id: str, path: str, contents: str | None) -> Path:
    project = tmp_path / "projects/PROJ-912-writers"
    feature = project / "specs/001-study"
    feature.mkdir(parents=True, exist_ok=True)
    tasks = feature / "tasks.md"
    tasks.write_text("- [ ] T008 Write `data/results.md`\n- [ ] T009 Rerun the analysis\n", encoding="utf-8")
    artifact = {"path": path, "execute": True}
    if contents is not None:
        artifact["contents"] = contents
    document = {"task_id": task_id, "verdict": "completed", "artifacts": [artifact]}
    ImplementerAgent().write_artifacts(
        SimpleNamespace(project_dir=project, project_id=project.name),
        {"tasks_path": str(tasks), "feature_dir": str(feature),
         "next_task_id": task_id, "all_complete": False},
        ChatResponse(text=yaml.safe_dump(document), model="test", backend="dartmouth"))
    return project


def _log(project: Path, task_id: str, script: str) -> str:
    return (project / "code/.tasks" / f"{task_id}.{script.replace('/', '_')}.log").read_text(encoding="utf-8")


def test_a_run_lists_the_files_it_wrote(tmp_path: Path) -> None:
    project = _send(tmp_path, "T008", "code/write_methods_doc.py", METHODS)
    log = _log(project, "T008", "code/write_methods_doc.py")
    assert "## files written by this run" in log
    assert "- `data/methods_only.txt`" in log and "- `data/results.md`" in log
    # Nothing was replaced, and the platform's own files are not outputs.
    assert "replaces" not in log and ".tasks" not in log.split("## files written by this run")[1]


def test_replacing_another_scripts_file_is_named_in_the_log(tmp_path: Path) -> None:
    _send(tmp_path, "T008", "code/write_methods_doc.py", METHODS)
    project = _send(tmp_path, "T009", "code/run_analysis.py", DRIVER)
    log = _log(project, "T009", "code/run_analysis.py")
    assert ("- `data/results.md` — replaces the version written by "
            "`code/write_methods_doc.py` (T008)") in log
    assert "- `data/summary.json`\n" in log
    assert "Lebowitz" not in (project / "data/results.md").read_text(encoding="utf-8")


def test_a_script_rewriting_its_own_file_is_not_a_replacement(tmp_path: Path) -> None:
    _send(tmp_path, "T008", "code/write_methods_doc.py", METHODS)
    project = _send(tmp_path, "T009", "code/write_methods_doc.py", None)
    assert "replaces" not in _log(project, "T009", "code/write_methods_doc.py")


def test_the_record_follows_the_latest_writer(tmp_path: Path) -> None:
    _send(tmp_path, "T008", "code/write_methods_doc.py", METHODS)
    _send(tmp_path, "T009", "code/run_analysis.py", DRIVER)
    project = _send(tmp_path, "T008", "code/write_methods_doc.py", None)
    assert ("- `data/results.md` — replaces the version written by "
            "`code/run_analysis.py` (T009)") in _log(project, "T008", "code/write_methods_doc.py")


def test_snapshot_ignores_environments_caches_and_planning(tmp_path: Path) -> None:
    for rel in ("data/a.csv", "figures/x.png", "code/lib.py", ".venv/bin/python", "code/.tasks/T1.log",
                "code/__pycache__/lib.pyc", "specs/001-x/tasks.md", "idea/idea.md", ".specify/memory/n.md"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x", encoding="utf-8")
    assert sorted(output_writers.snapshot(tmp_path)) == ["code/lib.py", "data/a.csv", "figures/x.png"]


def test_a_long_list_is_cut_but_every_takeover_is_named() -> None:
    files = [f"data/part_{i:03d}.csv" for i in range(100)] + ["data/results.md"]
    section = output_writers.log_section(
        "code/run.py", files, {"data/results.md": ("code/write_methods_doc.py", "T008")})
    assert section.count("- `data/part_") == 40
    assert "- ... and 60 more" in section
    assert "`data/results.md` — replaces the version written by `code/write_methods_doc.py` (T008)" in section


def test_the_verifier_is_told_which_run_last_wrote_the_file_it_judges(tmp_path: Path) -> None:
    from llmxive.agents import task_verifier

    _send(tmp_path, "T008", "code/write_methods_doc.py", METHODS)
    project = _send(tmp_path, "T009", "code/run_analysis.py", DRIVER)
    evidence = task_verifier.gather_evidence(project, "T008 Write `data/results.md` with the citation.")
    assert "last written by a run of `code/run_analysis.py` for T009" in evidence
    # A file no run is recorded for carries no such note.
    (project / "data/by_hand.md").write_text("x\n", encoding="utf-8")
    assert "last written" not in task_verifier.gather_evidence(project, "T010 Check `data/by_hand.md`.")


TEST_THAT_RUNS_THE_SCRIPT = (
    "import subprocess, sys\n"
    "def test_methods_doc_is_written():\n"
    "    assert subprocess.run([sys.executable, 'code/write_methods_doc.py']).returncode == 0\n"
)


def test_a_test_that_runs_the_script_does_not_take_the_file_over(tmp_path: Path) -> None:
    """Batch 1 run 2 (2026-10-11): `tests/benchmark_test.py` ran the benchmark
    script, and its log told the implementer the test "replaces the version
    written by `scripts/benchmark_full_run.py` (T016) ... one script should
    write the whole file". The script was the only writer."""
    _send(tmp_path, "T008", "code/write_methods_doc.py", METHODS)
    project = _send(tmp_path, "T009", "tests/test_methods_doc.py", TEST_THAT_RUNS_THE_SCRIPT)
    log = _log(project, "T009", "tests/test_methods_doc.py")
    assert "passed" in log and "- `data/results.md`\n" in log
    assert "replaces" not in log
    # The script is still the recorded writer, for the verifier and for later runs.
    assert output_writers.last_writer(project, "data/results.md") == ("code/write_methods_doc.py", "T008")
    project = _send(tmp_path, "T008", "code/write_methods_doc.py", None)
    assert "replaces" not in _log(project, "T008", "code/write_methods_doc.py")
