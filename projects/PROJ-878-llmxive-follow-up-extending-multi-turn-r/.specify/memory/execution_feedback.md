# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/graph_generator.py  --count 500  --depth-min 1  --depth-max 10  --branch-min 1  --branch-max 5  --output data/raw/synthetic_puzzles.jsonl  --seed 42 (rc=1); python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log.csv  --max-turns 50  --batch-size 5  --device cpu (rc=-1); python code/analyzer.py  --puzzles data/raw/synthetic_puzzles.jsonl  --results data/processed/execution_log.csv  --output results/statistical_report.json  --thresholds 40 50 60 (rc=1); 1 declared deliverable(s) absent: data/processed/extended_budget_log.csv

## Failing / missing run-book commands

- python code/graph_generator.py  --count 500  --depth-min 1  --depth-max 10  --branch-min 1  --branch-max 5  --output data/raw/synthetic_puzzles.jsonl  --seed 42 -> rc=1
026-10-16 09:21:54,672 - WARNING - Only one path exists; using longest path as ground truth.
2026-10-16 09:21:54,673 - WARNING - Only one path exists; using longest path as ground truth.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/graph_generator.py", line 414, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/graph_generator.py", line 407, in main
    _write_checksums([output_path], checksum_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/graph_generator.py", line 324, in _write_checksums
    rel = file_path.relative_to(Path.cwd())
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 730, in relative_to
    raise ValueError("{!r} is not in the subpath of {!r}"
ValueError: 'data/raw/synthetic_puzzles.jsonl' is not in the subpath of '/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r' OR one path is relative and the other is absolute.

- python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log.csv  --max-turns 50  --batch-size 5  --device cpu -> rc=-1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-878-llmxive-follow-up-extending-multi-turn-r/lib/python3.11/site-packages/huggingface_hub/file_download.py:949: FutureWarning: `resume_download` is deprecated and will be removed in version 1.0.0. Downloads always resume when possible. If you want to force a new download, use `force_download=True`.
  warnings.warn(

[TIMEOUT after 120s]
- python code/analyzer.py  --puzzles data/raw/synthetic_puzzles.jsonl  --results data/processed/execution_log.csv  --output results/statistical_report.json  --thresholds 40 50 60 -> rc=1
runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/analyzer.py", line 89, in perform_cox_ph_analysis
    'concordance_index': cph.concordance_index_,
                         ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-878-llmxive-follow-up-extending-multi-turn-r/lib/python3.11/site-packages/lifelines/fitters/coxph_fitter.py", line 594, in __getattr__
    if hasattr(self._model, attr):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-878-llmxive-follow-up-extending-multi-turn-r/lib/python3.11/site-packages/lifelines/fitters/coxph_fitter.py", line 2759, in concordance_index_
    self._concordance_index_ = _concordance_ratio(num_correct, num_tied, num_pairs)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-878-llmxive-follow-up-extending-multi-turn-r/lib/python3.11/site-packages/lifelines/utils/concordance.py", line 99, in _concordance_ratio
    raise ZeroDivisionError("No admissable pairs in the dataset.")
ZeroDivisionError: No admissable pairs in the dataset.


## Declared deliverables still missing

- data/processed/extended_budget_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/extended_budget_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/extended_budget_analysis.py` — NOT invoked by the run-book
    - `code/extended_budget_runner.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/extended_budget_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
