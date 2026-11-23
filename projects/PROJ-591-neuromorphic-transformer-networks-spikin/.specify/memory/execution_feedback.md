# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/tests/neuromorphic_fidelity_test.py; 4 command(s) failed: python code/main.py --model baseline --seed 1 (rc=1); python code/main.py --model spiking --seed 1 (rc=1); python code/analysis/statistical_tests.py (rc=1); 4 declared deliverable(s) absent: data/logs/zero_spike_report.json; data/processed/baseline_metrics.csv; data/processed/spiking_metrics.csv

## Failing / missing run-book commands

- python code/tests/neuromorphic_fidelity_test.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/tests/neuromorphic_fidelity_test.py': [Errno 2] No such file or directory

- python code/main.py --model baseline --seed 1 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/main.py", line 21, in <module>
    from data.dataset_loader import get_wikitext_dataloader
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/data/__init__.py", line 2, in <module>
    from .dataset_loader import load_dataset_wikitext2
ImportError: cannot import name 'load_dataset_wikitext2' from 'data.dataset_loader' (/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/data/dataset_loader.py)

- python code/main.py --model spiking --seed 1 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/main.py", line 21, in <module>
    from data.dataset_loader import get_wikitext_dataloader
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/data/__init__.py", line 2, in <module>
    from .dataset_loader import load_dataset_wikitext2
ImportError: cannot import name 'load_dataset_wikitext2' from 'data.dataset_loader' (/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/data/dataset_loader.py)

- python code/analysis/statistical_tests.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/analysis/statistical_tests.py", line 184, in <module>
    ) -> Dict[str, Any]:
                   ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?

- python code/analysis/plots.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-591-neuromorphic-transformer-networks-spikin/code/analysis/plots.py", line 9, in <module>
    import matplotlib.pyplot as plt
ModuleNotFoundError: No module named 'matplotlib'


## Declared deliverables still missing

- data/logs/zero_spike_report.json
- data/processed/baseline_metrics.csv
- data/processed/spiking_metrics.csv
- data/results/sensitivity_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/zero_spike_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/zero_spike_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/baseline_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/plots.py` — IS a run-book command
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/statistical_tests.py` — IS a run-book command
    - `code/analysis/tests/test_report_generator.py` — NOT invoked by the run-book
    - `code/analysis/tests/test_statistical_tests.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/run_baseline_seeds.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/spiking_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/plots.py` — IS a run-book command
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/statistical_tests.py` — IS a run-book command
    - `code/analysis/tests/test_report_generator.py` — NOT invoked by the run-book
    - `code/analysis/tests/test_statistical_tests.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/run_spiking_seeds.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/spiking_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/plots.py` — IS a run-book command
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/tests/test_report_generator.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
