# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/features.py: self-declared fabricated metric — “…# For now, we'll return a dummy value of 1.0 if we can't group.…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/features.py: self-declared fabricated metric — “…# For now, we'll return a dummy value of 1.0 if we can't group.…”; 5 command(s) failed: python code/ingestion.py --dataset adress --output data/interim/cleaned_transcripts.csv (rc=1); python code/features.py --input data/interim/cleaned_transcripts.csv --output data/processed/features.csv (rc=1); python code/stats.py --input data/processed/features.csv --output data/processed/stats_results.json (rc=1); 6 declared deliverable(s) absent: data/interim/cleaned_adress.csv; data/processed/checksums.json; data/processed/embeddings.npy

## Failing / missing run-book commands

- python code/ingestion.py --dataset adress --output data/interim/cleaned_transcripts.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/ingestion.py", line 244, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/ingestion.py", line 195, in main
    validate_scope(config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/ingestion.py", line 61, in validate_scope
    if config.source != "ADReSS":
       ^^^^^^^^^^^^^
AttributeError: 'DataSourceConfig' object has no attribute 'source'
- python code/features.py --input data/interim/cleaned_transcripts.csv --output data/processed/features.csv -> rc=1
    ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1643, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1907, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/interim/cleaned_transcripts.csv'
- python code/stats.py --input data/processed/features.csv --output data/processed/stats_results.json -> rc=1
    ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1643, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1907, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/features.csv'
- python code/modeling.py --input data/processed/features.csv --output data/processed/model_results.json -> rc=1
    ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1643, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1907, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/features.csv'
- python code/main.py -> rc=1
    mXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/verify_plan.py']. Error: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/bin/python', '/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/verify_plan.py']' returned non-zero exit status 1.
2026-09-30 16:28:04,666 - ERROR - Command failed with code 1. Stopping.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/main.py", line 110, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/main.py", line 97, in main
    metrics = measure_runtime_and_memory(commands)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/main.py", line 44, in measure_runtime_and_memory
    current, peak = tracemalloc.get_memory_usage()
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'tracemalloc' has no attribute 'get_memory_usage'

## Declared deliverables still missing

- data/interim/cleaned_adress.csv
- data/processed/checksums.json
- data/processed/embeddings.npy
- data/processed/features.csv
- data/results/metadata.json
- data/results/raw_record_count.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `DataSourceConfig` (in `code/config.py`) — accessed via method/attribute names this round: `source`

`DataSourceConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `DataSourceConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`DataSourceConfig.source` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/cleaned_adress.csv` is declared but was NOT written. Scripts referencing it:
    - `code/t016_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/t012h_success_criterion.py` — NOT invoked by the run-book
    - `code/derivation.py` — NOT invoked by the run-book
    - `code/t014_filter_records.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/cleaned_adress.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/t024c_checksum.py` — NOT invoked by the run-book
    - `code/checksums.py` — NOT invoked by the run-book
    - `code/t012f_checksum_record.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/embeddings.npy` is declared but was NOT written. Scripts referencing it:
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/t024c_checksum.py` — NOT invoked by the run-book
    - `code/features.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/embeddings.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/modeling.py` — IS a run-book command
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/features.py` — IS a run-book command
    - `code/stats.py` — IS a run-book command
    - `code/t025_save_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/t016_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/t012g_metadata_aggregation.py` — NOT invoked by the run-book
    - `code/t012e_low_power_warning.py` — NOT invoked by the run-book
    - `code/t012h_success_criterion.py` — NOT invoked by the run-book
    - `code/derivation.py` — NOT invoked by the run-book
    - `code/t025_save_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/raw_record_count.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/t012h_success_criterion.py` — NOT invoked by the run-book
    - `code/t012b_raw_record_count.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/results/raw_record_count.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/interim/cleaned_transcripts.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/main.py`, `code/t012e_low_power_warning.py`, `code/ingestion.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/interim/cleaned_transcripts.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/t012e_low_power_warning.py`, `code/ingestion.py`.

### `data/processed/features.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/save_features.py`, `code/main.py`, `code/t025_save_features.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/features.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/save_features.py`, `code/main.py`, `code/t025_save_features.py`.
