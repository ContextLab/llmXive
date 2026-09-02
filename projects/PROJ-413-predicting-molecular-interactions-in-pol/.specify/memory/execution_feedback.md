# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py   # Downloads MolNet, records checksum`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/data/download.py   # Downloads MolNet, records checksum (rc=1); python code/data/clean.py      # Validates columns, aborts with E‑DATA‑001 if adhesion_energy missing (rc=1); python code/data/graph_build.py   # Generates PyG graphs and analysis/topology_audit.md (rc=1); 2 declared deliverable(s) absent: data/curated/curated_dataset.csv; data/processed/descriptors.csv

## Failing / missing run-book commands

- python code/data/download.py   # Downloads MolNet, records checksum -> rc=1
    INFO:__main__:Loading MolNet dataset from Hugging Face...
INFO:httpx:HTTP Request: GET https://huggingface.co/api/agent-harnesses "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET https://huggingface.co/api/datasets/molnet "HTTP/1.1 401 Unauthorized"
ERROR:__main__:Failed to download MolNet dataset: Dataset 'molnet' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/molnet to ask for access.
ERROR:__main__:Data error: E-DATA-001: Failed to download MolNet dataset. Dataset 'molnet' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/molnet to ask for access.
- python code/data/clean.py      # Validates columns, aborts with E‑DATA‑001 if adhesion_energy missing -> rc=1
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 620, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 873, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/molnet_raw.csv'
- python code/data/graph_build.py   # Generates PyG graphs and analysis/topology_audit.md -> rc=1
    Random seed set to: 42

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/data/graph_build.py", line 404, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/data/graph_build.py", line 347, in main
    raise DataError(f"Curated dataset not found at {curated_path}")
utils.exceptions.DataError: Curated dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/data/curated/curated_dataset.csv
- python code/models/train.py   # 3‑layer GAT, batch ≤32, checkpoint every 10 epochs -> rc=1
    Random seed set to: 42

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/models/train.py", line 286, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/models/train.py", line 204, in main
    raise DataError(f"Processed graphs not found at {graphs_path}. Run graph_build.py first.")
utils.exceptions.DataError: Processed graphs not found at data/processed/graphs.pt. Run graph_build.py first.
- python code/analysis/perm_test.py   # 1000 permutations, 20 epochs each, runtime ≤2 h -> rc=1
    2026-09-02 03:37:42,854 - INFO - Starting Permutation Test: 1000 iterations, 5 epochs each.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/analysis/perm_test.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/analysis/perm_test.py", line 180, in main
    raise DataError(f"Required data file {DATA_PATH} not found. Please run T024 first.")
utils.exceptions.DataError: Required data file /home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/data/processed/graphs.pt not found. Please run T024 first.
- python code/analysis/attribution.py   # Integrated Gradients on test samples -> rc=1
    2026-09-02 03:37:45,278 - __main__ - INFO - Starting Integrated Gradients attribution analysis
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/analysis/attribution.py", line 381, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/analysis/attribution.py", line 356, in main
    model = load_trained_model(MODEL_PATH)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/analysis/attribution.py", line 48, in load_trained_model
    raise DataError(f"Model file not found: {model_path}. "
utils.exceptions.DataError: Model file not found: results/model.pt. Run T028 (train_final.py) to generate the model first.
- python code/analysis/collinearity.py   # VIF on handcrafted descriptors -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-413-predicting-molecular-interactions-in-pol/code/analysis/collinearity.py", line 24, in <module>
    from statsmodels.stats.outliers_influence import variance_inflation_factor
ModuleNotFoundError: No module named 'statsmodels'

## Declared deliverables still missing

- data/curated/curated_dataset.csv
- data/processed/descriptors.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/curated/curated_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/topology_audit.py` — NOT invoked by the run-book
    - `code/data/clean.py` — IS a run-book command
    - `code/data/update_state_for_curated.py` — NOT invoked by the run-book
    - `code/data/descriptor_extractor.py` — NOT invoked by the run-book
    - `code/data/generate_curated.py` — NOT invoked by the run-book
    - `code/data/graph_build.py` — IS a run-book command
    - `code/utils/verify_artifacts.py` — NOT invoked by the run-book
    - `code/utils/hash_state.py` — IS a run-book command
  Make ONE of these WRITE `data/curated/curated_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_attribution_json.py` — NOT invoked by the run-book
    - `code/analysis/collinearity.py` — IS a run-book command
    - `code/analysis/generate_stats.py` — NOT invoked by the run-book
    - `code/data/descriptor_extractor.py` — NOT invoked by the run-book
    - `code/utils/verify_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/raw/molnet_raw.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/clean.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/molnet_raw.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/clean.py`, `code/utils/verify_artifacts.py`.
