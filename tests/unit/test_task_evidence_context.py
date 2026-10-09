"""Task verification sees the relevant data and actual task execution record."""

from pathlib import Path

from llmxive.agents import task_verifier as tv
from llmxive.speckit.implement_cmd import _current_data_context
from tests.unit.test_task_execution_gate import setup, write


def test_declared_output_directory_precedes_unrelated_small_summaries(tmp_path):
    (tmp_path / "data/results").mkdir(parents=True)
    for n in range(40):
        (tmp_path / f"data/old-{n}.json").write_text('{"old":1}')
    csv = "N,residue,count\n1000,0,400\n1000,1,600\n"
    (tmp_path / "data/results/counts.csv").write_text(csv)
    evidence = tv.gather_evidence(tmp_path, "T001 Produce data/results/ and verify count sums")
    assert csv in evidence
    preferred = _current_data_context(tmp_path, preferred_paths=("data/results/",), max_files=1)
    assert csv in preferred and "old-" not in preferred


def test_real_successful_shell_execution_reaches_verifier_evidence(tmp_path):
    project, tasks, mechanical = setup(tmp_path)
    write(project, mechanical, 'printf "computed successfully\\n"\n')
    evidence = tv.gather_evidence(project, "T001 Execute scripts/study.sh")
    assert "(exit 0," in evidence and "ok=True" in evidence
    assert "computed successfully" in evidence
    assert "Historical execution records" in evidence
    assert "do not prove later edits were executed" in evidence
    before = tv._evidence_hash(evidence)
    write(project, mechanical, 'printf "new execution\\n"\n')
    assert tv._evidence_hash(tv.gather_evidence(project, "T001 Execute scripts/study.sh")) != before


def test_dotted_task_does_not_lend_its_log_to_parent_id(tmp_path):
    logs = tmp_path / "code/.tasks"
    logs.mkdir(parents=True)
    (logs / "T001.1.scripts_study.sh.log").write_text(
        "# scripts/study.sh (exit 0, 1s, ok=True)\nCHILD_ONLY\n"
    )
    assert "CHILD_ONLY" not in tv.gather_evidence(tmp_path, "T001 Produce data/")
    assert "CHILD_ONLY" in tv.gather_evidence(tmp_path, "T001.1 Produce data/")


def test_preferred_data_and_logs_do_not_read_external_symlinks(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private.json").write_text("PRIVATE_SENTINEL")
    (project / "data").symlink_to(outside, target_is_directory=True)
    logs = project / "code/.tasks"
    logs.mkdir(parents=True)
    (logs / "T001.scripts_study.sh.log").symlink_to(outside / "private.json")
    assert "PRIVATE_SENTINEL" not in tv.gather_evidence(project, "T001 Produce data/")
    assert _current_data_context(project, preferred_paths=("../outside/",)) == ""


def test_execution_context_is_bounded(tmp_path):
    logs = tmp_path / "code/.tasks"
    logs.mkdir(parents=True)
    for n in range(5):
        (logs / f"T001.code_script{n}.py.log").write_text(
            f"# code/script{n}.py (exit 0, 1s, ok=True)\n" + "x" * 20000
        )
    evidence = tv._task_execution_evidence(tmp_path, "T001 Produce data/")
    assert len(evidence) < 19000
    assert evidence.count("[Log truncated]") == 3
