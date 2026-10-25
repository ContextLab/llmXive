# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/analyze.py --step=exploratory`
  - script usage: `analyze.py [-h] [--step {coverage,similarity,stats,report}]`
  - argparse error: `analyze.py: error: argument --step: invalid choice: 'exploratory' (choose from 'coverage', 'similarity', 'stats', 'report')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/baseline_copy.py; python code/human_eval.py; bash scripts/verify_repro.sh   # Checks hashes, seeds, and that all outputs exist; 9 command(s) failed: python code/utils/repo_fetcher.py   # Writes data/raw/frozen_repo_list.json (rc=-1); python code/utils/git_clone.py   # Clones each repo into data/raw/repos/ (rc=1); python code/extract.py (rc=1); 5 declared deliverable(s) absent: data/processed/final_report.json; data/processed/results.json; data/processed/results_with_coverage.json

## Failing / missing run-book commands

- python code/utils/repo_fetcher.py   # Writes data/raw/frozen_repo_list.json -> rc=-1
rror: rate limit exceeded for url: https://api.github.com/repos/scikit-learn/scikit-learn. Retrying in 16.0s...
2026-10-25 14:38:34,758 - __main__ - WARNING - Skipping scikit-learn due to fetch error: Failed to fetch star count for https://github.com/scikit-learn/scikit-learn after 5 retries.
2026-10-25 14:38:34,831 - __main__ - WARNING - Attempt 1/5 failed for https://github.com/keras-team/keras: 403 Client Error: rate limit exceeded for url: https://api.github.com/repos/keras-team/keras. Retrying in 1.0s...
2026-10-25 14:38:35,859 - __main__ - WARNING - Attempt 2/5 failed for https://github.com/keras-team/keras: 403 Client Error: rate limit exceeded for url: https://api.github.com/repos/keras-team/keras. Retrying in 2.0s...
2026-10-25 14:38:37,889 - __main__ - WARNING - Attempt 3/5 failed for https://github.com/keras-team/keras: 403 Client Error: rate limit exceeded for url: https://api.github.com/repos/keras-team/keras. Retrying in 4.0s...
2026-10-25 14:38:41,920 - __main__ - WARNING - Attempt 4/5 failed for https://github.com/keras-team/keras: 403 Client Error: rate limit exceeded for url: https://api.github.com/repos/keras-team/keras. Retrying in 8.0s...


[TIMEOUT after 120s]
- python code/utils/git_clone.py   # Clones each repo into data/raw/repos/ -> rc=1

2026-10-25 14:38:46,150 - __main__ - INFO - Starting repository cloning process
2026-10-25 14:38:46,151 - __main__ - INFO - Repo list: /home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/data/raw/frozen_repo_list.json
2026-10-25 14:38:46,151 - __main__ - INFO - Target directory: /home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/data/raw/repos
2026-10-25 14:38:46,151 - __main__ - ERROR - Critical error during cloning: Repository list file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/data/raw/frozen_repo_list.json

- python code/extract.py -> rc=1
2026-10-25 14:38:47,614 - __main__ - INFO - Starting repository extraction pipeline
2026-10-25 14:38:47,614 - __main__ - ERROR - Pipeline failed: Repository list not found at data/raw/frozen_repo_list.json. Run T010 to generate it first.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/extract.py", line 272, in main
    raise FileNotFoundError(
FileNotFoundError: Repository list not found at data/raw/frozen_repo_list.json. Run T010 to generate it first.


- python code/baseline_copy.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-318-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/baseline_copy.py': [Errno 2] No such file or directory

- python code/aggregate.py -> rc=1
2026-10-25 14:38:49,724 - INFO - Starting aggregation. Processing dir: /home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/data/processed, Output: /home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/data/processed/results.json
2026-10-25 14:38:49,725 - INFO - Found 0 batch files in /home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/data/processed
2026-10-25 14:38:49,725 - ERROR - No batch files found. Aborting.


- python code/analyze.py --step=coverage -> rc=1
2026-10-25 14:38:50,123 - __main__ - INFO - Loading data from data/processed/results.json

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/analyze.py", line 373, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/analyze.py", line 299, in main
    data = load_json_file(input_path)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/analyze.py", line 57, in load_json_file
    raise FileNotFoundError(f"File not found: {file_path}")
FileNotFoundError: File not found: data/processed/results.json

- python code/analyze.py --step=similarity -> rc=1
2026-10-25 14:38:50,562 - __main__ - INFO - Loading data from data/processed/results_with_coverage.json

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/analyze.py", line 373, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/analyze.py", line 309, in main
    data = load_json_file(input_path)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/analyze.py", line 57, in load_json_file
    raise FileNotFoundError(f"File not found: {file_path}")
FileNotFoundError: File not found: data/processed/results_with_coverage.json

- python code/human_eval.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-318-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/human_eval.py': [Errno 2] No such file or directory

- python code/analyze.py --step=stats -> rc=1
2026-10-25 14:38:51,038 - __main__ - INFO - Loading data from data/processed/results_with_scores.json

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/analyze.py", line 373, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/analyze.py", line 319, in main
    data = load_json_file(input_path)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/code/analyze.py", line 57, in load_json_file
    raise FileNotFoundError(f"File not found: {file_path}")
FileNotFoundError: File not found: data/processed/results_with_scores.json

- python code/analyze.py --step=exploratory -> rc=2

usage: analyze.py [-h] [--step {coverage,similarity,stats,report}]
                  [--input INPUT] [--output OUTPUT]
analyze.py: error: argument --step: invalid choice: 'exploratory' (choose from 'coverage', 'similarity', 'stats', 'report')

- bash scripts/verify_repro.sh   # Checks hashes, seeds, and that all outputs exist -> rc=-1

shell script must be an existing project-local .sh file
- python -m pytest tests/ -v -> rc=2
/test_analysis.py:164: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

tests/integration/test_analysis.py:201
  /home/runner/work/llmXive/llmXive/projects/PROJ-318-evaluating-the-impact-of-code-generation/tests/integration/test_analysis.py:201: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_analysis_coverage.py
ERROR tests/unit/test_analyze.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_generation.py
ERROR tests/unit/test_quantization_enforcer.py
ERROR tests/unit/test_repo_fetcher.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 4 warnings, 6 errors in 2.37s =========================



## Declared deliverables still missing

- data/processed/final_report.json
- data/processed/results.json
- data/processed/results_with_coverage.json
- data/processed/results_with_scores.json
- data/raw/frozen_repo_list.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/final_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/final_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate.py` — IS a run-book command
    - `code/analyze.py` — IS a run-book command
    - `code/extract.py` — IS a run-book command
    - `code/generate.py` — IS a run-book command
    - `code/utils/coverage.py` — NOT invoked by the run-book
    - `code/utils/file_walker.py` — NOT invoked by the run-book
    - `code/utils/git_clone.py` — IS a run-book command
    - `code/utils/similarity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results_with_coverage.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/results_with_coverage.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results_with_scores.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/results_with_scores.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/frozen_repo_list.json` is declared but was NOT written. Scripts referencing it:
    - `code/extract.py` — IS a run-book command
    - `code/utils/git_clone.py` — IS a run-book command
    - `code/utils/repo_fetcher.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/frozen_repo_list.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
