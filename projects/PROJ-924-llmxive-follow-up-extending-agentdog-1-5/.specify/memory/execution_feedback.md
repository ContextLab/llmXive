# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m code.taxonomy_builder --source "agentdog_1_5_paper" --output data/processed/taxonomy_centroids.json (rc=1); python -m code.drift_scoring --input data/raw/atbench.parquet --taxonomy data/processed/taxonomy_centroids.json --output data/processed/drift_results.csv (rc=1); python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/gold_standard_proxy.csv --output data/processed/validation_report.json (rc=1); 3 declared deliverable(s) absent: data/processed/drift_scores.csv; data/processed/taxonomy_centroids.json; data/processed/us01_final_stats.json

## Failing / missing run-book commands

- python -m code.taxonomy_builder --source "agentdog_1_5_paper" --output data/processed/taxonomy_centroids.json -> rc=1
    2026-08-13 16:40:00,627 - ERROR - Error in main: "Path 'raw_taxonomy' not found in configuration."
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/taxonomy_builder.py", line 201, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/taxonomy_builder.py", line 174, in main
    taxonomy = load_taxonomy()
               ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/taxonomy_builder.py", line 44, in load_taxonomy
    taxonomy_path = str(get_path("raw_taxonomy"))
                        ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/config.py", line 113, in get_path
    raise KeyError(f"Path '{name}' not found in configuration.")
KeyError: "Path 'raw_taxonomy' not found in configuration."
- python -m code.drift_scoring --input data/raw/atbench.parquet --taxonomy data/processed/taxonomy_centroids.json --output data/processed/drift_results.csv -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/drift_scoring.py", line 9, in <module>
    from sentence_transformers import SentenceTransformer
ModuleNotFoundError: No module named 'sentence_transformers'
- python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/gold_standard_proxy.csv --output data/processed/validation_report.json -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/validation.py", line 15, in <module>
    from scipy import stats
ModuleNotFoundError: No module named 'scipy'
- python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/human_annotations.csv --output data/processed/validation_report.json -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/validation.py", line 15, in <module>
    from scipy import stats
ModuleNotFoundError: No module named 'scipy'

## Declared deliverables still missing

- data/processed/drift_scores.csv
- data/processed/taxonomy_centroids.json
- data/processed/us01_final_stats.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/drift_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/utils.py` — NOT invoked by the run-book
    - `code/annotator_interface.py` — NOT invoked by the run-book
    - `code/drift_scoring.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/drift_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/taxonomy_centroids.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils.py` — NOT invoked by the run-book
    - `code/drift_scoring.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/taxonomy_centroids.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/us01_final_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/us01_final_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/taxonomy_centroids.json`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[Path]`
- PRODUCER(s) to edit: `code/utils.py`, `code/drift_scoring.py`
- CONSUMER(s) that read it: `code/utils.py`, `code/drift_scoring.py`
  → Edit the producer so every required name [Path] is in `data/processed/taxonomy_centroids.json`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
