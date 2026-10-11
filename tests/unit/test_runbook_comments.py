"""A shell comment after a run-book command is not part of the command.

Canary 7 (2026-10-11) is the only one of fourteen runs that had every task
accepted and reached the execution gate. Its quickstart read

    python code/totient_census.py          # computes phi, writes census_summary.*
    python -m pytest tests -v               # runs all verification tests

The executor passed ``#``, ``computes``, ``phi,`` ... to the script as
arguments (argparse exit 2) and to pytest as test paths (exit 4, "file or
directory not found"). No task owned either failure, nothing was reopened, and
the project spent its last 21 steps repeating the same two commands.
"""
import shlex

import pytest

from llmxive.execution.analysis_runner import extract_run_commands

QUICKSTART = """# Quickstart

```bash
bash code/run_all.sh
python code/totient_census.py          # computes phi, writes census_summary.* and residue_counts.csv
python code/make_report.py             # builds results_table.md, tv_vs_N.png, updates paper.md
python -m pytest tests -v               # runs all verification tests, including the reproducibility rerun
pytest code/test_x.py # quick check
```
"""


def test_trailing_comments_are_dropped_from_run_book_commands() -> None:
    assert extract_run_commands(QUICKSTART) == [
        "bash code/run_all.sh",
        "python code/totient_census.py",
        "python code/make_report.py",
        "python -m pytest tests -v",
        "python -m pytest code/test_x.py",
    ]


@pytest.mark.parametrize("line", [
    "python code/run.py --label 'run #3' --sep '#'",
    'python code/run.py --pattern "a # b"',
    "python code/plot.py --color=#ff0000",
    "python code/fetch.py --url https://example.org/page#section",
])
def test_a_hash_that_is_data_stays(line: str) -> None:
    (command,) = extract_run_commands(f"```bash\n{line}\n```\n")
    assert command == line
    assert shlex.split(command) == shlex.split(line)


def test_a_line_that_is_only_a_comment_is_not_a_command() -> None:
    assert extract_run_commands("```bash\n# python code/old.py\npython code/new.py\n```\n") == ["python code/new.py"]
