# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python -m pytest tests/test_contracts.py (rc=1); 2 declared deliverable(s) absent: data/raw/mp_raw.json; data/raw/nist_alloys.json

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/main.py", line 16, in <module>
    CONFIG = get_config()
             ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/config.py", line 88, in get_config
    _CONFIG = Config()
              ^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/config.py", line 53, in __init__
    self.results = self.results_dir
    ^^^^^^^^^^^^
AttributeError: property 'results' of 'Config' object has no setter

- python -m pytest tests/test_contracts.py -> rc=1
           "model_metrics.schema.yaml",
            "feature_importance.schema.yaml",
            "collinearity_diagnostic.schema.yaml",
        ],
    )
    def test_contract_file_exists_and_valid(contract_file: str):
        """Check that a contract file exists and can be parsed as YAML/JSON."""
        path = CONTRACTS_DIR / contract_file
>       assert path.is_file(), f"Contract file missing: {contract_file}"
E       AssertionError: Contract file missing: feature_importance.schema.yaml
E       assert False
E        +  where False = <bound method Path.is_file of PosixPath('contracts/feature_importance.schema.yaml')>()
E        +    where <bound method Path.is_file of PosixPath('contracts/feature_importance.schema.yaml')> = PosixPath('contracts/feature_importance.schema.yaml').is_file

tests/test_contracts.py:30: AssertionError
=========================== short test summary info ============================
FAILED tests/test_contracts.py::test_contract_file_exists_and_valid[model_metrics.schema.yaml]
FAILED tests/test_contracts.py::test_contract_file_exists_and_valid[feature_importance.schema.yaml]
========================= 2 failed, 4 passed in 0.06s ==========================



## Declared deliverables still missing

- data/raw/mp_raw.json
- data/raw/nist_alloys.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/mp_raw.json` is declared but was NOT written. Scripts referencing it:
    - `code/_download_logic.py` — NOT invoked by the run-book
    - `code/data/download_mp.py` — NOT invoked by the run-book
    - `code/data/merge_sources.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/mp_raw.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/nist_alloys.json` is declared but was NOT written. Scripts referencing it:
    - `code/_download_logic.py` — NOT invoked by the run-book
    - `code/data/_download_logic.py` — NOT invoked by the run-book
    - `code/data/merge_sources.py` — NOT invoked by the run-book
    - `code/merge.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/nist_alloys.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
