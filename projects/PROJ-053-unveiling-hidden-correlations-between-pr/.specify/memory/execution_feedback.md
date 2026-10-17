# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --step download (rc=1); python code/main.py --step preprocess (rc=1); python code/main.py --step train (rc=1); 1 declared deliverable(s) absent: data/literature_baseline_importance.json

## Failing / missing run-book commands

- python code/main.py --step download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 25, in <module>
    from models.metrics import main as save_metrics_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/metrics.py", line 20, in <module>
    def _calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
                                                                      ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?

- python code/main.py --step preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 25, in <module>
    from models.metrics import main as save_metrics_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/metrics.py", line 20, in <module>
    def _calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
                                                                      ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?

- python code/main.py --step train -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 25, in <module>
    from models.metrics import main as save_metrics_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/metrics.py", line 20, in <module>
    def _calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
                                                                      ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?

- python code/main.py --step analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 25, in <module>
    from models.metrics import main as save_metrics_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/metrics.py", line 20, in <module>
    def _calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
                                                                      ^^^^^
NameError: name 'Tuple' is not defined. Did you mean: 'tuple'?


## Declared deliverables still missing

- data/literature_baseline_importance.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/literature_baseline_importance.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/importance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/literature_baseline_importance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
