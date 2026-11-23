"""The verifier is shown a whole project script, not its first 12 KB.

Canary 6 (2026-10-11): the project was one 20 KB script. The task asked for a
figure; the function that draws it began 14 KB in. The verifier rejected the
task because "the provided excerpt of the script does not include the
implementation of `plot_tv`".
"""
from pathlib import Path

from llmxive.agents import task_verifier

FILLER = "def helper_{i}():\n    return {i}  # " + "x" * 60 + "\n\n\n"


def _script(size: int, marker: str) -> str:
    body = ""
    i = 0
    while len(body) < size:
        body += FILLER.format(i=i)
        i += 1
    return body + f"def {marker}():\n    return 'drawn'\n"


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "projects/PROJ-906-quote"
    (project / "code").mkdir(parents=True)
    return project


def test_a_function_past_12kb_of_a_script_is_quoted(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "code/run.py").write_text(_script(20_000, "plot_tv"), encoding="utf-8")
    evidence = task_verifier.gather_evidence(project, "T009 Generate the figure with `code/run.py`")
    assert "def plot_tv():" in evidence
    assert "(truncated)" not in evidence


def test_a_script_beyond_the_source_limit_is_still_marked_truncated(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "code/run.py").write_text(
        _script(task_verifier._MAX_BYTES_PER_SOURCE + 5_000, "plot_tv"), encoding="utf-8")
    evidence = task_verifier.gather_evidence(project, "T009 Generate the figure with `code/run.py`")
    assert "def plot_tv():" not in evidence
    assert "(truncated)" in evidence


def test_sources_share_one_budget_and_later_files_fall_back_to_the_base_limit(tmp_path: Path) -> None:
    project = _project(tmp_path)
    names = ["a.py", "b.py", "c.py"]
    for name in names:
        (project / "code" / name).write_text(_script(28_000, f"tail_of_{name[0]}"), encoding="utf-8")
    task = "T001 Implement " + ", ".join(f"`code/{name}`" for name in names)
    evidence = task_verifier.gather_evidence(project, task)
    assert "def tail_of_a():" in evidence and "def tail_of_b():" in evidence
    # The third would exceed the shared source budget: base limit, and marked.
    assert "def tail_of_c():" not in evidence
    assert evidence.count("(truncated)") == 1


def test_a_data_file_keeps_the_base_limit(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "data").mkdir()
    rows = "n,phi\n" + "".join(f"{i},{i}\n" for i in range(4000)) + "LAST,ROW\n"
    (project / "data/table.csv").write_text(rows, encoding="utf-8")
    evidence = task_verifier.gather_evidence(project, "T002 Export `data/table.csv`")
    assert "LAST,ROW" not in evidence.split("# Underlying data evidence")[0]
