# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generate_data.py --seed 42 --overlap high`
  - script usage: `generate_data.py [-h] [--overlap {LOW,MEDIUM,HIGH}] [--seed SEED]`
  - argparse error: `generate_data.py: error: argument --overlap: invalid choice: 'high' (choose from 'LOW', 'MEDIUM', 'HIGH')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --input data/results/metrics.csv; 2 command(s) failed: python code/generate_data.py --seed 42 --overlap high (rc=2); python -m pytest tests/contract/ (rc=1); 2 declared deliverable(s) absent: data/raw/skills.json; data/raw/tasks.json

## Failing / missing run-book commands

- python code/generate_data.py --seed 42 --overlap high -> rc=2

usage: generate_data.py [-h] [--overlap {LOW,MEDIUM,HIGH}] [--seed SEED]
generate_data.py: error: argument --overlap: invalid choice: 'high' (choose from 'LOW', 'MEDIUM', 'HIGH')

- python code/analysis.py --input data/results/metrics.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/analysis.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
e_count():
        """Verify that negative usage_count fails validation."""
>       schema = load_schema()

tests/contract/test_skill_schema.py:82: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def load_schema():
        """Load the skill schema from YAML."""
        if not os.path.exists(SCHEMA_PATH):
>           pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
E           Failed: Schema file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/tests/contracts/skill.schema.yaml

tests/contract/test_skill_schema.py:23: Failed
=========================== short test summary info ============================
FAILED tests/contract/test_skill_schema.py::test_schema_loads - Failed: Schem...
FAILED tests/contract/test_skill_schema.py::test_valid_skill_object - Failed:...
FAILED tests/contract/test_skill_schema.py::test_missing_required_field - Fai...
FAILED tests/contract/test_skill_schema.py::test_wrong_type_field - Failed: S...
FAILED tests/contract/test_skill_schema.py::test_negative_usage_count - Faile...
=================== 5 failed, 29 passed, 3 skipped in 0.21s ====================



## Declared deliverables still missing

- data/raw/skills.json
- data/raw/tasks.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/skills.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/skills.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
    - `code/run_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
