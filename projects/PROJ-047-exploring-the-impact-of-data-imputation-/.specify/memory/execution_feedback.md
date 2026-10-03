# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0 (rc=1); python code/analysis.py --validate-schema --input data/results/simulation_summary.csv (rc=1); python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png (rc=1); 4 declared deliverable(s) absent: data/results/power_analysis.json; data/results/simulation_summary.csv; data/results/statistical_test_results.json

## Failing / missing run-book commands

- python code/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/run_simulation.py", line 11, in <module>
    from analysis.pipeline import run_imputation_and_estimation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/pipeline.py", line 12, in <module>
    from .imputation import apply_mean_imputation, apply_knn_imputation, apply_mice_imputation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/imputation.py", line 4, in <module>
    from sklearn.impute import SimpleImputer, KNNImputer, IterativeImputer
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/.venv/lib/python3.11/site-packages/sklearn/impute/__init__.py", line 18, in __getattr__
    raise ImportError(
ImportError: IterativeImputer is experimental and the API might change without any deprecation cycle. To use it, you need to explicitly import enable_iterative_imputer:
from sklearn.experimental import enable_iterative_imputer
- python code/analysis.py --validate-schema --input data/results/simulation_summary.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis.py", line 6, in <module>
    from analysis.metrics import run_statistical_test, save_statistical_test_results
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/metrics.py", line 13, in <module>
    from .schemas import StatisticalTestResults, validate_statistical_test_results
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/schemas.py", line 12, in <module>
    from pydantic import BaseModel, Field, field_validator, model_validator
ModuleNotFoundError: No module named 'pydantic'
- python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/visualization.py", line 5, in <module>
    from analysis.plot_coverage import main as plot_coverage_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/plot_coverage.py", line 26, in <module>
    def run_regression_test(df: pd.DataFrame) -> Dict[str, float]:
                                                 ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/visualization.py --plot coverage_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/coverage_vs_beta.png -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/visualization.py", line 5, in <module>
    from analysis.plot_coverage import main as plot_coverage_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/plot_coverage.py", line 26, in <module>
    def run_regression_test(df: pd.DataFrame) -> Dict[str, float]:
                                                 ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/visualization.py --plot bias_distributions --input data/results/simulation_summary.csv --output docs/paper/figures/bias_distributions.png -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/visualization.py", line 5, in <module>
    from analysis.plot_coverage import main as plot_coverage_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/plot_coverage.py", line 26, in <module>
    def run_regression_test(df: pd.DataFrame) -> Dict[str, float]:
                                                 ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
- python code/analysis.py --verify-sensitivity --input data/results/sensitivity_analysis.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis.py", line 6, in <module>
    from analysis.metrics import run_statistical_test, save_statistical_test_results
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/metrics.py", line 13, in <module>
    from .schemas import StatisticalTestResults, validate_statistical_test_results
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-047-exploring-the-impact-of-data-imputation-/code/analysis/schemas.py", line 12, in <module>
    from pydantic import BaseModel, Field, field_validator, model_validator
ModuleNotFoundError: No module named 'pydantic'

## Declared deliverables still missing

- data/results/power_analysis.json
- data/results/simulation_summary.csv
- data/results/statistical_test_results.json
- data/results/us1_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/simulation_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_simulation.py` — IS a run-book command
    - `code/visualization.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
    - `code/analysis/schemas.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/plot_bias.py` — NOT invoked by the run-book
    - `code/analysis/power.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/simulation_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/statistical_test_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/analysis/schemas.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/statistical_test_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/us1_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_simulation.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
    - `code/simulation/verify_us1.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/us1_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
