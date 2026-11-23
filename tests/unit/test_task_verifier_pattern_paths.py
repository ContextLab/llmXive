"""Outputs a task names by pattern are evidence too.

PROJ-9999 canary, 2026-10-11: ``data/counts_N{N}_p{p}.csv`` "for all 12
combinations". The 24 files existed; the collector resolved literal paths only;
the verifier was told nothing matched and rejected correct work three times.
"""

from pathlib import Path

import pytest

from llmxive.agents.task_verifier import gather_evidence
from llmxive.project_paths import declared_paths, declared_patterns, resolve_pattern

TASK = (
    "- [X] T004 **Count residues for every (N, p) pair** - `src/analysis.py`\n"
    "  *Inputs*: `data/phi.npy`.\n"
    "  *Outputs*: `data/counts_N{N}_p{p}.csv` and `data/counts_N{N}_p{p}.json` for all 12 combinations.\n"
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    proj = tmp_path / "projects" / "PROJ-901-patterns"
    (proj / "data").mkdir(parents=True)
    (proj / "src").mkdir()
    (proj / "src" / "analysis.py").write_text("print('x')\n", encoding="utf-8")
    for n in (1000, 10000, 100000, 1000000):
        for p in (5, 7, 11):
            (proj / "data" / f"counts_N{n}_p{p}.csv").write_text(
                f"residue,count\n0,{n // p}\n1,{n - n // p}\n", encoding="utf-8")
            (proj / "data" / f"counts_N{n}_p{p}.json").write_text(
                f'{{"N": {n}, "p": {p}}}\n', encoding="utf-8")
    return proj


def test_the_literal_detector_does_not_see_a_templated_path() -> None:
    """The premise: these are invisible to `declared_paths`, which is unchanged."""
    assert declared_paths(TASK) == ["src/analysis.py", "data/phi.npy"]


@pytest.mark.parametrize(("written", "glob"), [
    ("data/counts_N{N}_p{p}.csv", "data/counts_N*_p*.csv"),
    ("figures/<model>_loss.png", "figures/*_loss.png"),
    ("data/raw/*.json", "data/raw/*.json"),
    ("data/results/run_{i}.json", "data/results/run_*.json"),
    ("data/artifacts/model_{model_type}_seed_{seed_id}_final.pt", "data/artifacts/model_*_seed_*_final.pt"),
])
def test_placeholders_become_single_segment_wildcards(written: str, glob: str) -> None:
    assert declared_patterns(f"Writes `{written}` for every case.") == [(written, glob)]


@pytest.mark.parametrize("text", [
    "plain `data/summary.csv` only",
    "a set {5, 7, 11} and a formula f(x) = x * 2 in prose",
    "escape `data/../../etc/*.conf`",
])
def test_prose_and_literal_paths_are_not_patterns(text: str) -> None:
    assert declared_patterns(text) == []


def test_every_matching_file_is_listed_and_the_ends_are_quoted(project: Path) -> None:
    evidence = gather_evidence(project, TASK)
    assert "`data/counts_N{N}_p{p}.csv` (pattern `data/counts_N*_p*.csv`): 12 matching file(s) exist" in evidence
    assert "`data/counts_N{N}_p{p}.json` (pattern `data/counts_N*_p*.json`): 12 matching file(s) exist" in evidence
    for n in (1000, 10000, 100000, 1000000):
        for p in (5, 7, 11):
            assert f"`data/counts_N{n}_p{p}.csv` (" in evidence
    # Contents, not just names: the first and last of the family.
    assert "contents of `data/counts_N1000000_p11.csv`" in evidence
    assert "residue,count\n0,90909\n1,909091" in evidence
    assert "contents of `data/counts_N1000_p7.csv`" in evidence
    assert "NO MATCHING FILE" not in evidence


def test_the_evidence_changes_when_any_one_file_changes(project: Path) -> None:
    """The verdict cache is keyed on evidence; an unquoted file must still count."""
    before = gather_evidence(project, TASK)
    (project / "data" / "counts_N10000_p7.csv").write_text("residue,count\n0,1\n", encoding="utf-8")
    assert gather_evidence(project, TASK) != before


def test_a_pattern_with_no_file_says_so(project: Path) -> None:
    evidence = gather_evidence(project, "- [X] T008 plots `figures/tv_p{p}.png` per modulus")
    assert "`figures/tv_p{p}.png` (pattern `figures/tv_p*.png`): NO MATCHING FILE exists" in evidence


def test_a_pattern_cannot_reach_outside_the_project(project: Path, tmp_path: Path) -> None:
    (tmp_path / "outside").mkdir()
    (tmp_path / "outside" / "secret_1.csv").write_text("SECRET SENTINEL\n", encoding="utf-8")
    (project / "data" / "link").symlink_to(tmp_path / "outside", target_is_directory=True)
    (project / "data" / "leak_1.csv").symlink_to(tmp_path / "outside" / "secret_1.csv")
    assert resolve_pattern(project, "data/link/secret_*.csv") == []
    assert resolve_pattern(project, "data/leak_*.csv") == []
    evidence = gather_evidence(project, "- [X] T1 writes `data/link/secret_{i}.csv` and `data/leak_{i}.csv`")
    assert "SECRET SENTINEL" not in evidence


def test_source_patterns_use_the_code_shorthand(project: Path) -> None:
    (project / "code" / "tests").mkdir(parents=True)
    (project / "code" / "tests" / "test_a.py").write_text("def test_a(): pass\n", encoding="utf-8")
    assert [p.name for p in resolve_pattern(project, "tests/test_*.py")] == ["test_a.py"]


def test_a_small_family_is_quoted_in_full(project: Path) -> None:
    """Two of twelve got: "the evidence only shows the contents of two CSVs"."""
    evidence = gather_evidence(project, TASK)
    for n in (1000, 10000, 100000, 1000000):
        for p in (5, 7, 11):
            assert f"contents of `data/counts_N{n}_p{p}.csv`" in evidence
            assert f"0,{n // p}\n1,{n - n // p}" in evidence
    assert "NOT quoted" not in evidence


def test_a_family_too_large_for_the_budget_says_what_it_left_out(project: Path) -> None:
    for i in range(40):
        (project / "data" / f"big_{i:02d}.csv").write_text("x,y\n" + "1,2\n" * 900, encoding="utf-8")
    evidence = gather_evidence(project, "- [X] T2 writes `data/big_{i}.csv` for 40 seeds")
    assert "40 matching file(s) exist" in evidence
    assert "contents of `data/big_00.csv`" in evidence and "contents of `data/big_39.csv`" in evidence
    assert "contents of `data/big_17.csv`" not in evidence
    assert "38 file(s) listed above are NOT quoted" in evidence
    assert "`data/big_17.csv` (" in evidence, "still listed with size and digest"
