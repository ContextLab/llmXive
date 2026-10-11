# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py  --max-samples 5000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01 (rc=1)

## Failing / missing run-book commands

- python code/main.py  --max-samples 5000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/main.py", line 34, in <module>
    from models.mc_dropout import run_mc_dropout
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/models/mc_dropout.py", line 80, in <module>
    X_train: pd.DataFrame,
             ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

