# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py  --mode generate_and_analyze  --Llist 100 200 400 800 1600  --Wlist 0.5 1.0 2.0  --realizations 100  --seed 42 (rc=1); python code/main.py  --mode scaling_analysis  --output data/processed/scaling_results.csv (rc=1); python code/main.py  --mode visualize  --L 200  --W 2.0  --realization 5  --output figures/eigenstate_decay.png (rc=1); 3 declared deliverable(s) absent: data/metadata/residuals.json; data/processed/bonferroni_results.json; data/processed/scaling_fits.json

## Failing / missing run-book commands

- python code/main.py  --mode generate_and_analyze  --Llist 100 200 400 800 1600  --Wlist 0.5 1.0 2.0  --realizations 100  --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/main.py", line 19, in <module>
    from code.analyze_pr import analyze_single_realization
ImportError: cannot import name 'analyze_single_realization' from 'code.analyze_pr' (/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/analyze_pr.py)
- python code/main.py  --mode scaling_analysis  --output data/processed/scaling_results.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/main.py", line 19, in <module>
    from code.analyze_pr import analyze_single_realization
ImportError: cannot import name 'analyze_single_realization' from 'code.analyze_pr' (/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/analyze_pr.py)
- python code/main.py  --mode visualize  --L 200  --W 2.0  --realization 5  --output figures/eigenstate_decay.png -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/main.py", line 19, in <module>
    from code.analyze_pr import analyze_single_realization
ImportError: cannot import name 'analyze_single_realization' from 'code.analyze_pr' (/home/runner/work/llmXive/llmXive/projects/PROJ-676-quantifying-the-effect-of-disorder-on-el/code/analyze_pr.py)

## Declared deliverables still missing

- data/metadata/residuals.json
- data/processed/bonferroni_results.json
- data/processed/scaling_fits.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/residuals.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/finite_size_scaling.py` — NOT invoked by the run-book
    - `code/logger_utils.py` — NOT invoked by the run-book
    - `code/stats.py` — NOT invoked by the run-book
    - `code/analyze_pr.py` — NOT invoked by the run-book
    - `code/logger.py` — NOT invoked by the run-book
    - `code/run_residual_logger.py` — NOT invoked by the run-book
    - `code/residual_logger.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/residuals.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bonferroni_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/apply_bonferroni.py` — NOT invoked by the run-book
    - `code/aggregate_and_correct_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bonferroni_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scaling_fits.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/finite_size_scaling.py` — NOT invoked by the run-book
    - `code/apply_bonferroni.py` — NOT invoked by the run-book
    - `code/stats.py` — NOT invoked by the run-book
    - `code/compare_methods.py` — NOT invoked by the run-book
    - `code/aggregate_and_correct_stats.py` — NOT invoked by the run-book
    - `code/analyze_pr.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/scaling_fits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
