# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --step download --species-list data/species_list.csv (rc=1); python code/main.py --step phylogeny (rc=1); python code/main.py --step stats (rc=1); 4 declared deliverable(s) absent: data/processed/climate_dist_matrix.csv; data/processed/mantel_results.json; data/processed/partial_mantel_results.json

## Failing / missing run-book commands

- python code/main.py --step download --species-list data/species_list.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-408-investigating-the-predictive-power-of-pl/code/main.py", line 245, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-408-investigating-the-predictive-power-of-pl/code/main.py", line 231, in main
    output_dir = Path(config.output_dir)
                      ^^^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'output_dir'

- python code/main.py --step phylogeny -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-408-investigating-the-predictive-power-of-pl/code/main.py", line 245, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-408-investigating-the-predictive-power-of-pl/code/main.py", line 226, in main
    species_file = Path(config.data_dir) / "raw" / "test_species_10.txt"
                        ^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'data_dir'. Did you mean: 'state_dir'?

- python code/main.py --step stats -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-408-investigating-the-predictive-power-of-pl/code/main.py", line 245, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-408-investigating-the-predictive-power-of-pl/code/main.py", line 226, in main
    species_file = Path(config.data_dir) / "raw" / "test_species_10.txt"
                        ^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'data_dir'. Did you mean: 'state_dir'?

- python code/main.py --step viz -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-408-investigating-the-predictive-power-of-pl/code/main.py", line 245, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-408-investigating-the-predictive-power-of-pl/code/main.py", line 226, in main
    species_file = Path(config.data_dir) / "raw" / "test_species_10.txt"
                        ^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'data_dir'. Did you mean: 'state_dir'?


## Declared deliverables still missing

- data/processed/climate_dist_matrix.csv
- data/processed/mantel_results.json
- data/processed/partial_mantel_results.json
- data/processed/phylo_dist_matrix.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/climate_dist_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_integration_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/climate_dist_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mantel_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/report.py` — NOT invoked by the run-book
    - `code/run_integration_test.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mantel_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/partial_mantel_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — NOT invoked by the run-book
    - `code/run_integration_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/partial_mantel_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/phylo_dist_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/run_integration_test.py` — NOT invoked by the run-book
    - `scripts/audit_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/phylo_dist_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
