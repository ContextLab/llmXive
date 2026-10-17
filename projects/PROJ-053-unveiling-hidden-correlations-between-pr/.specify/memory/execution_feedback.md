# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --step download (rc=1); python code/main.py --step preprocess (rc=1); python code/main.py --step train (rc=1)

## Failing / missing run-book commands

- python code/main.py --step download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 23, in <module>
    from models.gpr_trainer import main as train_gpr_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/gpr_trainer.py", line 77, in <module>
    def run_stratified_analysis(df: pd.DataFrame, feature_cols: List[str], target_cols: List[str]) -> Dict[str, Any]:
                                    ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

- python code/main.py --step preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 23, in <module>
    from models.gpr_trainer import main as train_gpr_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/gpr_trainer.py", line 77, in <module>
    def run_stratified_analysis(df: pd.DataFrame, feature_cols: List[str], target_cols: List[str]) -> Dict[str, Any]:
                                    ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

- python code/main.py --step train -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 23, in <module>
    from models.gpr_trainer import main as train_gpr_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/gpr_trainer.py", line 77, in <module>
    def run_stratified_analysis(df: pd.DataFrame, feature_cols: List[str], target_cols: List[str]) -> Dict[str, Any]:
                                    ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

- python code/main.py --step analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 23, in <module>
    from models.gpr_trainer import main as train_gpr_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/gpr_trainer.py", line 77, in <module>
    def run_stratified_analysis(df: pd.DataFrame, feature_cols: List[str], target_cols: List[str]) -> Dict[str, Any]:
                                    ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

