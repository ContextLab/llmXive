# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m code.taxonomy_builder --source "agentdog_1_5_paper" --output data/processed/taxonomy_centroids.json (rc=1); python -m code.drift_scoring --input data/raw/atbench.parquet --taxonomy data/processed/taxonomy_centroids.json --output data/processed/drift_results.csv (rc=1); python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/gold_standard_proxy.csv --output data/processed/validation_report.json (rc=1); 1 declared deliverable(s) absent: data/raw/agent_logs.csv

## Failing / missing run-book commands

- python -m code.taxonomy_builder --source "agentdog_1_5_paper" --output data/processed/taxonomy_centroids.json -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/taxonomy_builder.py", line 130, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/taxonomy_builder.py", line 118, in main
    taxonomy = load_taxonomy(args.source)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/taxonomy_builder.py", line 38, in load_taxonomy
    raise TaxonomyLoadError(f"Taxonomy file not found at {taxonomy_path}.")
TaxonomyLoadError: Taxonomy file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/processed/taxonomy_agentdog.json.
- python -m code.drift_scoring --input data/raw/atbench.parquet --taxonomy data/processed/taxonomy_centroids.json --output data/processed/drift_results.csv -> rc=1
    Loading taxonomy centroids...

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/drift_scoring.py", line 194, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/drift_scoring.py", line 164, in main
    centroids = load_centroids(centroid_path)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/drift_scoring.py", line 27, in load_centroids
    with open(centroid_path, 'r', encoding='utf-8') as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/taxonomy_centroids.json'
- python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/gold_standard_proxy.csv --output data/processed/validation_report.json -> rc=1
    follow-up-extending-agentdog-1-5/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1645, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1904, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/processed/drift_scores.csv'
- python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/human_annotations.csv --output data/processed/validation_report.json -> rc=1
    follow-up-extending-agentdog-1-5/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1645, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1904, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/processed/drift_scores.csv'

## Declared deliverables still missing

- data/raw/agent_logs.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_path` — defined in `code/config.py`; called 25 way(s):

- code/main.py: atbench_path = get_path("raw_data") / "ATBench_raw.parquet"
- code/main.py: mapped_path = get_path("processed") / "ATBench_mapped.csv"
- code/main.py: output_path = get_path("processed") / "taxonomy_centroids.json"
- code/main.py: centroids_path = get_path("processed") / "taxonomy_centroids.json"
- code/main.py: logs_path = get_path("raw_data") / "ATBench_raw.parquet"
- code/main.py: output_path = get_path("processed") / "drift_scores.csv"
- code/main.py: str(get_path("raw_data")),
- code/main.py: str(get_path("processed")),
- code/main.py: str(get_path("test"))
- code/main.py: output_path = get_path("processed") / "us01_final_stats.json"
- code/ensure_test_dir.py: base_path = path or get_path("data_test")
- code/generate_static_test_fixture.py: output_path = get_path('data/test_static_logs.json')
- code/utils.py: base_dir = get_path("specs")
- code/ensure_specs_dir.py: project_root = get_path(base_path)
- code/data_loader.py: relative_path = os.path.relpath(file_path, get_path("project_root"))
- code/data_loader.py: output_path = str(get_path("raw_data") / "ATBench_raw.parquet")
- code/data_loader.py: output_path = str(get_path("processed") / "ATBench_mapped.csv")
- code/data_loader.py: output_path = str(get_path("raw_data") / "agent_logs.csv")
- code/data_loader.py: output_path = str(get_path("processed") / "taxonomy_agentdog.json")
- code/data_loader.py: output_path = str(get_path("raw_data") / "advbench.parquet")
- code/data_loader.py: output_path = str(get_path("raw_data") / "hf4.parquet")
- code/data_loader.py: input_path = args.output or str(get_path("raw_data") / "ATBench_raw.parquet")
- code/config.py: - get_path("key") where key is in PATHS
- code/config.py: - get_path("data", "processed") to build paths from components
- code/config.py: - get_path("data", "processed", "file.csv") for nested paths

Make `get_path` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/agent_logs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/agent_logs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/taxonomy_centroids.json`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[Path]`
- PRODUCER(s) to edit: `code/drift_scoring.py`, `code/taxonomy_builder.py`
- CONSUMER(s) that read it: `code/main.py`, `code/config.py`, `code/drift_scoring.py`, `code/taxonomy_builder.py`
  → Edit the producer so every required name [Path] is in `data/processed/taxonomy_centroids.json`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/processed/taxonomy_agentdog.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data_loader.py`, `code/taxonomy_builder.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/processed/taxonomy_agentdog.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data_loader.py`, `code/taxonomy_builder.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/processed/drift_scores.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/annotator_interface.py`, `code/drift_scoring.py`, `code/validation.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/processed/drift_scores.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/config.py`, `code/annotator_interface.py`, `code/drift_scoring.py`, `code/validation.py`.
