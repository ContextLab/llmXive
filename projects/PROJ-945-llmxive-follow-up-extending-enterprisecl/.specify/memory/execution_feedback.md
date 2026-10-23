# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/src/extractors/extract_features.py --input data/raw/ --output data/processed/features.json; python code/src/oracle/apply_oracle.py --input data/processed/features.json --output data/processed/triplets.json; python code/src/models/train_classifier.py --input data/processed/triplets.json --output code/models/classifier.pkl; 1 command(s) failed: python code/run_pipeline.sh (rc=2); 6 declared deliverable(s) absent: data/processed/error_schema.json; data/results/distinctiveness_stats.csv; data/results/extraction_memory_log.json

## Failing / missing run-book commands

- python code/run_pipeline.sh -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-945-llmxive-follow-up-extending-enterprisecl/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-945-llmxive-follow-up-extending-enterprisecl/code/run_pipeline.sh': [Errno 2] No such file or directory

- python code/src/extractors/extract_features.py --input data/raw/ --output data/processed/features.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-945-llmxive-follow-up-extending-enterprisecl/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-945-llmxive-follow-up-extending-enterprisecl/code/src/extractors/extract_features.py': [Errno 2] No such file or directory

- python code/src/oracle/apply_oracle.py --input data/processed/features.json --output data/processed/triplets.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-945-llmxive-follow-up-extending-enterprisecl/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-945-llmxive-follow-up-extending-enterprisecl/code/src/oracle/apply_oracle.py': [Errno 2] No such file or directory

- python code/src/models/train_classifier.py --input data/processed/triplets.json --output code/models/classifier.pkl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-945-llmxive-follow-up-extending-enterprisecl/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-945-llmxive-follow-up-extending-enterprisecl/code/src/models/train_classifier.py': [Errno 2] No such file or directory

- python code/src/evaluation/run_eval.py --model code/models/classifier.pkl --lite-set data/lite_set/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-945-llmxive-follow-up-extending-enterprisecl/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-945-llmxive-follow-up-extending-enterprisecl/code/src/evaluation/run_eval.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/error_schema.json
- data/results/distinctiveness_stats.csv
- data/results/extraction_memory_log.json
- data/results/ground_truth_validation.json
- data/results/oracle_independence.json
- data/results/rule_based_enforcement.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/error_schema.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/modeling/dataset.py` — NOT invoked by the run-book
    - `code/src/modeling/oracle.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/error_schema.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/distinctiveness_stats.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/features/distinctiveness_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/distinctiveness_stats.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/extraction_memory_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/features/run_extraction_with_monitor.py` — NOT invoked by the run-book
    - `code/src/utils/resource_monitor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/extraction_memory_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/ground_truth_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/utils/validate_ground_truth.py` — NOT invoked by the run-book
    - `code/tests/unit/test_validate_ground_truth.py` — NOT invoked by the run-book
    - `src/utils/validate_ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ground_truth_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/oracle_independence.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/modeling/verify_oracle_independence.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/oracle_independence.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/rule_based_enforcement.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/modeling/verify_rule_based_enforcement.py` — NOT invoked by the run-book
    - `code/tests/unit/test_rule_based_enforcement.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/rule_based_enforcement.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
