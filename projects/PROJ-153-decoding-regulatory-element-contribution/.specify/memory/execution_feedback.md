# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/03_annotate.py; python code/04_filter.py; python code/05_weights.py; 4 declared deliverable(s) absent: data/processed/delta_peak_signal.tsv; data/processed/peak_signal_matrix.tsv; data/processed/vif_flags.tsv

## Failing / missing run-book commands

- python code/03_annotate.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/03_annotate.py': [Errno 2] No such file or directory
- python code/04_filter.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/04_filter.py': [Errno 2] No such file or directory
- python code/05_weights.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/05_weights.py': [Errno 2] No such file or directory
- python code/08_visualize.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/08_visualize.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/delta_peak_signal.tsv
- data/processed/peak_signal_matrix.tsv
- data/processed/vif_flags.tsv
- data/processed/weights.tsv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/delta_peak_signal.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/05b_compute_delta_signal.py` — NOT invoked by the run-book
    - `code/05c_compute_weights.py` — NOT invoked by the run-book
    - `code/05_validate_cre_gating.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/delta_peak_signal.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/peak_signal_matrix.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/05b_check_collinearity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/peak_signal_matrix.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vif_flags.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/05b_check_collinearity.py` — NOT invoked by the run-book
    - `code/05c_compute_weights.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vif_flags.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/weights.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/05c_compute_weights.py` — NOT invoked by the run-book
    - `code/05_validate_cre_gating.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/weights.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
