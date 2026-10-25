# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/contract_hashes.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap low medium high  --pruning {on,off}  --seed 42  --randomize-tasks`
  - script usage: `agent.py [-h] --library-sizes LIBRARY_SIZES [LIBRARY_SIZES ...]`
  - argparse error: `agent.py: error: argument --pruning: invalid choice: '{on,off}' (choose from 'off', 'fr04', 'on')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/contract_hashes.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --input data/results/metrics.csv; 5 command(s) failed: python code/generate_data.py --seed 42 --overlap high (rc=1); python -m pytest tests/contract/ (rc=1); python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap low medium high  --pruning {on,off}  --seed 42  --randomize-tasks (rc=2); 4 declared deliverable(s) absent: data/raw/checksums.json; data/raw/skills.json; data/raw/tasks.json

## Failing / missing run-book commands

- python code/generate_data.py --seed 42 --overlap high -> rc=1

2026-10-25 19:21:29,539 INFO __main__: Generating data with overlap level: HIGH
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/generate_data.py", line 444, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/generate_data.py", line 383, in main
    core_skills = _generate_skills_core(
                  ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/generate_data.py", line 294, in _generate_skills_core
    raise RuntimeError(
RuntimeError: Failed to generate embeddings satisfying HIGH overlap after 20 attempts.

- python -m pytest tests/contract/ -> rc=1
le sample task object against the schema."""
        sample_task = {
            "task_id": "TASK_SAMPLE_001",
            "description": "Calculate the sum of two numbers and return the result.",
            "ground_truth_path": ["skill_add", "skill_return"],
            "complexity": 2
        }
        try:
            validate(instance=sample_task, schema=schema)
        except ValidationError as e:
>           pytest.fail(f"Sample task failed schema validation: {e.message}")
E           Failed: Sample task failed schema validation: 'ground_truth_skills' is a required property

tests/contract/test_task_schema.py:48: Failed
=========================== short test summary info ============================
FAILED tests/contract/test_schema_presence.py::test_dummy_instance_validation
FAILED tests/contract/test_task_schema.py::test_schema_loads - AssertionError...
FAILED tests/contract/test_task_schema.py::test_sample_task_validates - Faile...
ERROR tests/contract/test_checksums.py::test_tasks_checksum_matches - FileNot...
ERROR tests/contract/test_checksums.py::test_skills_checksum_matches - FileNo...
============== 3 failed, 12 passed, 6 skipped, 2 errors in 3.25s ===============


- python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap low medium high  --pruning {on,off}  --seed 42  --randomize-tasks -> rc=2

usage: agent.py [-h] --library-sizes LIBRARY_SIZES [LIBRARY_SIZES ...]
                [--task-sample TASK_SAMPLE] [--overlap [{low,medium,high}]]
                [--pruning [{off,fr04,on}]]
agent.py: error: argument --pruning: invalid choice: '{on,off}' (choose from 'off', 'fr04', 'on')

- python -m pytest tests/contract/ -> rc=1
le sample task object against the schema."""
        sample_task = {
            "task_id": "TASK_SAMPLE_001",
            "description": "Calculate the sum of two numbers and return the result.",
            "ground_truth_path": ["skill_add", "skill_return"],
            "complexity": 2
        }
        try:
            validate(instance=sample_task, schema=schema)
        except ValidationError as e:
>           pytest.fail(f"Sample task failed schema validation: {e.message}")
E           Failed: Sample task failed schema validation: 'ground_truth_skills' is a required property

tests/contract/test_task_schema.py:48: Failed
=========================== short test summary info ============================
FAILED tests/contract/test_schema_presence.py::test_dummy_instance_validation
FAILED tests/contract/test_task_schema.py::test_schema_loads - AssertionError...
FAILED tests/contract/test_task_schema.py::test_sample_task_validates - Faile...
ERROR tests/contract/test_checksums.py::test_tasks_checksum_matches - FileNot...
ERROR tests/contract/test_checksums.py::test_skills_checksum_matches - FileNo...
============== 3 failed, 12 passed, 6 skipped, 2 errors in 3.05s ===============


- python code/analysis.py --input data/results/metrics.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/analysis.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
le sample task object against the schema."""
        sample_task = {
            "task_id": "TASK_SAMPLE_001",
            "description": "Calculate the sum of two numbers and return the result.",
            "ground_truth_path": ["skill_add", "skill_return"],
            "complexity": 2
        }
        try:
            validate(instance=sample_task, schema=schema)
        except ValidationError as e:
>           pytest.fail(f"Sample task failed schema validation: {e.message}")
E           Failed: Sample task failed schema validation: 'ground_truth_skills' is a required property

tests/contract/test_task_schema.py:48: Failed
=========================== short test summary info ============================
FAILED tests/contract/test_schema_presence.py::test_dummy_instance_validation
FAILED tests/contract/test_task_schema.py::test_schema_loads - AssertionError...
FAILED tests/contract/test_task_schema.py::test_sample_task_validates - Faile...
ERROR tests/contract/test_checksums.py::test_tasks_checksum_matches - FileNot...
ERROR tests/contract/test_checksums.py::test_skills_checksum_matches - FileNo...
============== 3 failed, 12 passed, 6 skipped, 2 errors in 3.06s ===============



## Declared deliverables still missing

- data/raw/checksums.json
- data/raw/skills.json
- data/raw/tasks.json
- data/results/experiment_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_data.py` — IS a run-book command
    - `code/update_state.py` — NOT invoked by the run-book
    - `code/write_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/skills.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/pruning.py` — NOT invoked by the run-book
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
    - `code/update_state.py` — NOT invoked by the run-book
    - `code/write_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/skills.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/pruning.py` — NOT invoked by the run-book
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
    - `code/run_sensitivity.py` — NOT invoked by the run-book
    - `code/update_state.py` — NOT invoked by the run-book
    - `code/write_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/experiment_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/analyze.py` — NOT invoked by the run-book
    - `code/copy_contracts.py` — IS a run-book command
    - `code/logging_config.py` — NOT invoked by the run-book
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_sensitivity.py` — NOT invoked by the run-book
    - `code/setup_contracts.py` — NOT invoked by the run-book
    - `code/smoke_logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/experiment_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
