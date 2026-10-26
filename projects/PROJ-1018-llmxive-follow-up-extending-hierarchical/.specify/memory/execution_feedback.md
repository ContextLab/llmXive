# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python src/data_loader.py  --dataset deepmind/pg19  --split-ratio 0.05  --seed 42  --min-tokens 32000  --pad-short-docs False`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): bash ./run_pipeline.sh; python src/sensitivity.py --k-values 50,100,200 --output data/reports/sweep_report.json; 2 command(s) failed: python src/data_loader.py  --dataset deepmind/pg19  --split-ratio 0.05  --seed 42  --min-tokens 32000  --pad-short-docs False (rc=1); python code/src/clustering.py --input data/interim/relevance_profiles.json --k 100 --output data/processed/static_index_k100.json --seed 42 (rc=1); 2 declared deliverable(s) absent: data/interim/filtered_pg19.json; data/interim/relevance_profiles.json

## Failing / missing run-book commands

- bash ./run_pipeline.sh -> rc=-1

shell script must be an existing project-local .sh file
- python src/data_loader.py  --dataset deepmind/pg19  --split-ratio 0.05  --seed 42  --min-tokens 32000  --pad-short-docs False -> rc=1
e/llmXive/.llmxive-venvs/PROJ-1018-llmxive-follow-up-extending-hierarchical/lib/python3.11/site-packages/datasets/load.py", line 1134, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'lmsys/pg-19-test' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/src/data_loader.py", line 145, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/src/data_loader.py", line 134, in main
    _ = load_streaming_pg19(
        ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/src/data_loader.py", line 67, in load_streaming_pg19
    raise RuntimeError(f"Failed to load dataset {dataset_name}: {e}")
RuntimeError: Failed to load dataset lmsys/pg-19-test: Dataset 'lmsys/pg-19-test' doesn't exist on the Hub or cannot be accessed.

- python code/src/clustering.py --input data/interim/relevance_profiles.json --k 100 --output data/processed/static_index_k100.json --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/src/clustering.py", line 270, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/src/clustering.py", line 241, in main
    profiles_path = os.path.join(config.data_interim_dir, 'relevance_profiles.json')
                                 ^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'data_interim_dir'. Did you mean: 'interim_dir'?

- python src/sensitivity.py --k-values 50,100,200 --output data/reports/sweep_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1018-llmxive-follow-up-extending-hierarchical/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/src/sensitivity.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/interim/filtered_pg19.json
- data/interim/relevance_profiles.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/filtered_pg19.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data_loader.py` — NOT invoked by the run-book
    - `src/data_loader.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/filtered_pg19.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/relevance_profiles.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_static_inference.py` — NOT invoked by the run-book
    - `code/src/aggregation.py` — IS a run-book command
    - `code/src/clustering.py` — IS a run-book command
    - `code/src/extraction.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/relevance_profiles.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
