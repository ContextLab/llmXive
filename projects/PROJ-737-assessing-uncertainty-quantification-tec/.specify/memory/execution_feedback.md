# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 2 declared deliverable(s) absent: data/results/per_sample_errors.csv; data/results/pipeline_run.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
eaturizers.composition.element import ElementFraction
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/matminer/featurizers/composition/element.py", line 202, in <module>
    class BandCenter(BaseFeaturizer):
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/matminer/featurizers/composition/element.py", line 210, in BandCenter
    magpie_data = MagpieData()
                  ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/matminer/utils/data.py", line 217, in __init__
    self.all_elemental_props[descriptor_name][Element.from_Z(atomic_no).symbol] = prop_value
                                              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/pymatgen/core/periodic_table.py", line 541, in from_Z
    raise ValueError(f"Unexpected atomic number {Z=}")
ValueError: Unexpected atomic number Z=119


## Declared deliverables still missing

- data/results/per_sample_errors.csv
- data/results/pipeline_run.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/per_sample_errors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/create_skeleton.py` — NOT invoked by the run-book
    - `code/generate_metrics_raw.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/utils/schema_utils.py` — NOT invoked by the run-book
    - `code/verify_t001.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/per_sample_errors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/pipeline_run.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/results/pipeline_run.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
